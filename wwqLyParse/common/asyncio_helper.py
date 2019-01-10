#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
import asyncio
import sys
import logging
import threading
import functools
import itertools
from .concurrent_futures import ThreadPoolExecutor

PY37 = sys.version_info >= (3, 7)
if PY37:
    get_current_task = asyncio.current_task
    get_running_loop = asyncio.get_running_loop
else:
    get_current_task = asyncio.Task.current_task
    get_running_loop = asyncio.get_event_loop

AbstractEventLoop = asyncio.AbstractEventLoop
CancelledError = asyncio.CancelledError


def new_raw_async_loop(force_use_selector=False):
    if not force_use_selector:
        loop = asyncio.ProactorEventLoop()
    else:
        loop = asyncio.SelectorEventLoop()
    executor = ThreadPoolExecutor()
    import concurrent.futures
    assert isinstance(executor, concurrent.futures.ThreadPoolExecutor)
    loop.set_default_executor(executor)
    logging.debug("set %s for %s" % (executor, loop))
    return loop


def _run_forever(loop):
    logging.debug("start loop %s", loop)
    asyncio.set_event_loop(loop)
    loop.run_forever()


def new_running_async_loop(name="AsyncLoopThread", force_use_selector=False):
    loop = new_raw_async_loop(force_use_selector=force_use_selector)
    threading.Thread(target=_run_forever, args=(loop,), name=name, daemon=True).start()
    return loop


_main_async_loop = None  # type: asyncio.AbstractEventLoop


def get_main_async_loop():
    assert _main_async_loop is not None
    return _main_async_loop


def start_main_async_loop_in_main_thread(callback, *args, **kwargs):
    global _main_async_loop
    assert _main_async_loop is None
    _main_async_loop = new_raw_async_loop()

    def _cb():
        try:
            callback(*args, **kwargs)
        finally:
            _main_async_loop.stop()

            async def _null():
                pass

            asyncio.run_coroutine_threadsafe(_null(), _main_async_loop)

    thread = threading.Thread(target=_cb)
    _main_async_loop.call_soon(thread.start)
    threading.current_thread().name = "MainLoop"
    _run_forever(_main_async_loop)
    threading.current_thread().name = "MainThread"


_MODULE_TASK_NAME = "__asyncio_helper__.name"


def set_task_name(name: str, task: asyncio.Task = None):
    if task is None:
        task = get_current_task()
    setattr(task, _MODULE_TASK_NAME, name)


def get_task_name(task: asyncio.Task = None):
    try:
        if task is None:
            task = get_current_task()
        if task is not None:
            return getattr(task, _MODULE_TASK_NAME)
    except AttributeError:
        pass
    except RuntimeError:
        pass
    return ""


def get_task_name_with_thread(task: asyncio.Task = None):
    task_name = get_task_name(task)
    thread_name = threading.current_thread().getName()
    if task_name:
        return thread_name + '~' + task_name
    else:
        return thread_name


def run_in_main_async_loop(coro):
    thread_name = threading.current_thread().getName()

    async def _co():
        set_task_name("For-" + thread_name)
        return await coro

    loop = get_main_async_loop()
    return asyncio.run_coroutine_threadsafe(_co(), loop)


async def async_run_func_or_co(func_or_co, *args, **kwargs):
    fn = functools.partial(func_or_co, *args, **kwargs)
    if asyncio.iscoroutinefunction(func_or_co):
        return await fn()
    else:
        return await get_running_loop().run_in_executor(None, fn)


async def async_run_in_other_loop(co, loop, cancel_connect=True):
    our_loop = get_running_loop()
    if loop == our_loop:
        # shortcuts in same loop
        fu = asyncio.ensure_future(co)
    else:
        fu = asyncio.wrap_future(asyncio.run_coroutine_threadsafe(co, loop=loop))
    if not cancel_connect:
        fu = asyncio.shield(fu)
    return await fu


def run_in_other_loop(co, loop, timeout=None):
    return asyncio.run_coroutine_threadsafe(co, loop=loop).result(timeout=timeout)


_MODULE_TIMEOUT = "__asyncio_helper__.timeout"
_MODULE_TIMEOUT_HANDLE = "__asyncio_helper__.timeout_handle"


def set_timeout(task: asyncio.Task, timeout: [float, int], loop: asyncio.AbstractEventLoop = None, timeout_cancel=True):
    assert isinstance(timeout, (float, int))
    if loop is None:
        loop = get_running_loop()
    now_time = loop.time()
    out_time = now_time + timeout
    setattr(task, _MODULE_TIMEOUT, out_time)
    if timeout_cancel:
        if timeout <= 0:
            task.cancel()
            return
        handle = getattr(task, _MODULE_TIMEOUT_HANDLE, None)
        if handle is not None:
            assert isinstance(handle, asyncio.Handle)
            handle.cancel()
        handle = loop.call_at(out_time, task.cancel)
        setattr(task, _MODULE_TIMEOUT_HANDLE, handle)


def get_left_time(task: asyncio.Task = None, loop: asyncio.AbstractEventLoop = None):
    if loop is None:
        loop = get_running_loop()
    if task is None:
        task = get_current_task()
    out_time = getattr(task, _MODULE_TIMEOUT, None)
    if not out_time:
        if PY37:
            return sys.maxsize
        else:
            return 60 * 60 * 24  # one day (resolve the ValueError("timeout too big") in py35)
    now_time = loop.time()
    left_time = out_time - now_time
    if left_time < 0:
        return 0
    return left_time


def patch_logging():
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.threadName = get_task_name_with_thread()
        return record

    logging.setLogRecordFactory(record_factory)


async def start_tls(self, transport, protocol, sslcontext, *,
                    server_side=False,
                    server_hostname=None,
                    ssl_handshake_timeout=None):
    """Upgrade transport to TLS.

        Return a new transport that *protocol* should start using
        immediately.
        """

    # for py37
    _start_tls = getattr(self, "start_tls", None)
    if _start_tls is not None:
        return await _start_tls(transport, protocol, sslcontext, server_side=server_side,
                                server_hostname=server_hostname,
                                ssl_handshake_timeout=ssl_handshake_timeout)

    # try to back port start_tls support from py37's asyncio/base_event.py
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # Notice its not work fine with ProactorEventLoop because of bpo-26819 and bpo-33694
    # so we must use a SelectEventLoop for this function when below python3.7
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    assert not isinstance(self, asyncio.ProactorEventLoop)

    import asyncio.sslproto as sslproto

    waiter = self.create_future()
    ssl_protocol = sslproto.SSLProtocol(
        self, protocol, sslcontext, waiter,
        server_side, server_hostname)

    # Pause early so that "ssl_protocol.data_received()" doesn't
    # have a chance to get called before "ssl_protocol.connection_made()".
    transport.pause_reading()

    transport._protocol = ssl_protocol
    # transport.set_protocol(ssl_protocol)
    conmade_cb = self.call_soon(ssl_protocol.connection_made, transport)
    resume_cb = self.call_soon(transport.resume_reading)

    try:
        await waiter
    except Exception:
        transport.close()
        conmade_cb.cancel()
        resume_cb.cancel()
        raise

    return ssl_protocol._app_transport
