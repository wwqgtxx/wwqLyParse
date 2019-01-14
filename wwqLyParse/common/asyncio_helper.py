#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
import asyncio
# import asyncio.windows_utils
import sys
import logging
import threading
import functools
import itertools
import concurrent.futures
from .concurrent_futures import ThreadPoolExecutor

PY37 = sys.version_info >= (3, 7)
get_current_task = asyncio.current_task
get_running_loop = asyncio.get_running_loop
AbstractEventLoop = asyncio.AbstractEventLoop
CancelledError = asyncio.CancelledError

PIPE_MAX_BYTES = 32 * 1024 * 1024  # 32m


# class IocpProactor(asyncio.IocpProactor):
#     def recv(self, conn, nbytes, flags=0):
#         if isinstance(conn, asyncio.windows_utils.PipeHandle):
#             # patch default nNumberOfBytesToRead from 32k to 32m
#             if nbytes == 32768:  # proactor_event.py line 274
#                 nbytes = PIPE_MAX_BYTES
#         return super().recv(conn, nbytes, flags)


def new_raw_async_loop(force_use_selector=False):
    if not force_use_selector:
        # loop = asyncio.ProactorEventLoop(IocpProactor())
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
    logging.debug("starting loop %s", loop)
    asyncio.set_event_loop(loop)
    loop.run_forever()


def new_running_async_loop(name="AsyncLoopThread", force_use_selector=False):
    fu = concurrent.futures.Future()
    loop = new_raw_async_loop(force_use_selector=force_use_selector)

    def _cb():
        logging.debug("finish start loop %s", loop)
        fu.set_result(None)

    loop.call_soon_threadsafe(_cb)
    threading.Thread(target=_run_forever, args=(loop,), name=name, daemon=True).start()
    fu.result()
    return loop


_main_async_loop = None  # type: asyncio.AbstractEventLoop


def get_main_async_loop():
    assert _main_async_loop is not None
    return _main_async_loop


def start_main_async_loop_in_main_thread(callback, *args, **kwargs):
    global _main_async_loop
    assert _main_async_loop is None
    _main_async_loop = new_raw_async_loop()

    async def _co():
        logging.debug("finish start main loop %s", _main_async_loop)

        threading.Thread(target=_cb).start()

    def _cb():
        try:
            callback(*args, **kwargs)
        finally:
            _main_async_loop.stop()

            async def _null():
                pass

            asyncio.run_coroutine_threadsafe(_null(), _main_async_loop)

    logging.debug(asyncio)
    _main_async_loop.create_task(_co())
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


class InSameLoopError(Exception):
    pass


def run_in_other_loop(co, loop, timeout=None, cancel_connect=False):
    try:
        r_loop = get_running_loop()
    except RuntimeError:
        pass
    else:
        if r_loop is loop:
            raise InSameLoopError()
    fu = asyncio.run_coroutine_threadsafe(co, loop=loop)
    try:
        return fu.result(timeout=timeout)
    except concurrent.futures.TimeoutError:
        if cancel_connect:
            fu.cancel()
        raise


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
        return sys.maxsize
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

    _start_tls = getattr(self, "start_tls", None)
    if _start_tls is not None:
        return await _start_tls(transport, protocol, sslcontext, server_side=server_side,
                                server_hostname=server_hostname,
                                ssl_handshake_timeout=ssl_handshake_timeout)
    else:
        raise NotImplementedError
