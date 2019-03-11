#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
import asyncio
import sys
import logging
import threading
import functools
import itertools
from . import concurrent_futures

# import all from standard asyncio lib
from asyncio import *


def new_raw_async_loop(force_use_selector=False):
    if not force_use_selector:
        loop = asyncio.ProactorEventLoop()
    else:
        loop = asyncio.SelectorEventLoop()
    executor = concurrent_futures.ThreadPoolExecutor()
    import concurrent.futures
    assert isinstance(executor, concurrent.futures.ThreadPoolExecutor)
    assert concurrent_futures.TimeoutError is concurrent.futures.TimeoutError
    loop.set_default_executor(executor)
    logging.debug("set %s for %s" % (executor, loop))
    return loop


def _run_forever(loop):
    logging.debug("starting loop %s", loop)
    asyncio.set_event_loop(loop)
    loop.run_forever()


def new_running_async_loop(name="AsyncLoopThread", force_use_selector=False):
    fu = concurrent_futures.Future()
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


def start_main_async_loop_in_other_thread(callback=None, *args, **kwargs):
    global _main_async_loop
    assert _main_async_loop is None
    if _main_async_loop is None:
        _main_async_loop = new_running_async_loop("MainLoop")
    if callback is not None:
        callback(*args, **kwargs)


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


_MODULE_TASK_NAME = "__asyncio__.name"


def set_task_name(name: str, task: asyncio.Task = None):
    if task is None:
        task = current_task()
    setattr(task, _MODULE_TASK_NAME, name)


def get_task_name(task: asyncio.Task = None):
    try:
        if task is None:
            task = current_task()
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


async def async_run_in_loop(co, loop, cancel_connect=True):
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
    except concurrent_futures.TimeoutError:
        if cancel_connect:
            fu.cancel()
        raise


_MODULE_TIMEOUT = "__asyncio__.timeout"
_MODULE_TIMEOUT_HANDLE = "__asyncio__.timeout_handle"


def set_timeout(task: asyncio.Task, timeout: [float, int], loop: asyncio.AbstractEventLoop = None, timeout_cancel=True):
    assert isinstance(timeout, (float, int))
    if loop is None:
        loop = get_running_loop()
    now_time = loop.time()
    out_time = now_time + timeout
    if timeout_cancel:
        if timeout <= 0:
            task.cancel()
            return
        unset_timeout(task)
        handle = loop.call_at(out_time, task.cancel)
        setattr(task, _MODULE_TIMEOUT_HANDLE, handle)
    setattr(task, _MODULE_TIMEOUT, out_time)


def unset_timeout(task: asyncio.Task):
    handle = getattr(task, _MODULE_TIMEOUT_HANDLE, None)
    if handle is not None:
        assert isinstance(handle, asyncio.Handle)
        handle.cancel()
    setattr(task, _MODULE_TIMEOUT, None)


def get_left_time(task: asyncio.Task = None, loop: asyncio.AbstractEventLoop = None):
    if loop is None:
        loop = get_running_loop()
    if task is None:
        task = current_task()
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


class AsyncStreamProtocol(asyncio.streams.FlowControlMixin, asyncio.protocols.Protocol):
    def __init__(self, handle_class, pool=None, loop=None):
        super().__init__(loop=loop)
        self.handle_class = handle_class
        self.pool = pool  # type: AsyncPool
        self.loop = self._loop  # type: asyncio.AbstractEventLoop
        self.stream_reader = None  # type: asyncio.StreamReader
        self.stream_writer = None  # type: asyncio.StreamWriter
        self.transport = None  # type: asyncio.Transport
        self._closed = self.loop.create_future()

    def rebuild(self):
        self.stream_reader = asyncio.StreamReader(loop=self.loop)
        self.stream_reader.set_transport(self.transport)
        self.stream_writer = asyncio.StreamWriter(self.transport, self,
                                                  self.stream_reader,
                                                  self.loop)

    def connection_made(self, transport):
        self.transport = transport
        self.rebuild()
        res = self.handle_class(self)
        if self.pool is None:
            self.loop.create_task(res())
        else:
            self.pool.spawn(res())

    def connection_lost(self, exc):
        if self.stream_reader is not None:
            if exc is None:
                self.stream_reader.feed_eof()
            else:
                self.stream_reader.set_exception(exc)
        if not self._closed.done():
            if exc is None:
                self._closed.set_result(None)
            else:
                self._closed.set_exception(exc)
        super().connection_lost(exc)
        # self.stream_reader = None
        # self.stream_writer = None

    def data_received(self, data):
        self.stream_reader.feed_data(data)

    def eof_received(self):
        self.stream_reader.feed_eof()
        return True

    def __del__(self):
        closed = self._closed
        if closed.done() and not closed.cancelled():
            closed.exception()


class AsyncPipeStreamProtocol(AsyncStreamProtocol):
    def __init__(self, handle_class, pool, loop=None):
        super().__init__(handle_class, pool, loop=loop)
        self.pipe = None

    def rebuild(self):
        super().rebuild()
        self.pipe = self.transport.get_extra_info('pipe')


class AsyncTcpStreamProtocol(AsyncStreamProtocol):
    def __init__(self, handle_class, pool, loop=None):
        super().__init__(handle_class, pool, loop=loop)
        self._over_ssl = False
        self.socket = None
        self.sockname = None
        self.peername = None

    def rebuild(self):
        super().rebuild()
        self._over_ssl = self.transport.get_extra_info('sslcontext') is not None
        self.socket = self.transport.get_extra_info('socket')
        self.sockname = self.transport.get_extra_info('sockname')
        self.peername = self.transport.get_extra_info('peername')

    def eof_received(self):
        self.stream_reader.feed_eof()
        if self._over_ssl:
            return False
        return True


class AsyncStreamRequestHandler(object):
    def __init__(self, protocol: AsyncStreamProtocol):
        self.protocol = protocol

    @property
    def wfile(self):
        return self.protocol.stream_writer

    @property
    def rfile(self):
        return self.protocol.stream_reader

    async def __call__(self, *args, **kwargs):
        await self.setup()
        try:
            await self.handle()
        except ConnectionResetError:
            pass
        finally:
            await self.finish()

    async def setup(self):
        pass

    async def handle(self):
        pass

    async def finish(self):
        try:
            await self.wfile.drain()
        except asyncio.CancelledError:
            raise
        except:
            pass
        self.wfile.close()


class AsyncPipeStreamRequestHandler(AsyncStreamRequestHandler):
    def __init__(self, protocol: AsyncPipeStreamProtocol):
        super().__init__(protocol)
        self.protocol = protocol

    @property
    def pipe(self):
        return self.protocol.pipe


class AsyncTcpStreamRequestHandler(AsyncStreamRequestHandler):
    def __init__(self, protocol: AsyncTcpStreamProtocol):
        super().__init__(protocol)
        self.protocol = protocol

    @property
    def socket(self):
        return self.protocol.socket

    @property
    def sockname(self):
        return self.protocol.sockname

    @property
    def peername(self):
        return self.protocol.peername

    client_address = peername
