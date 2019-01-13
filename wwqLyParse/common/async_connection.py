#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
import asyncio
from . import asyncio_helper
from .async_pool import AsyncPool
import struct
import logging
import itertools


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


class AsyncPipeConnection(object):
    def __init__(self, handle: AsyncPipeStreamRequestHandler):
        self.handle = handle

    @classmethod
    async def _create_pipe_connection_async(cls, address):
        loop = asyncio_helper.get_running_loop()
        assert isinstance(loop, asyncio.ProactorEventLoop)
        handle_future = loop.create_future()

        class _PipeHandle(AsyncPipeStreamRequestHandler):
            def __init__(self, *k, **kk):
                super().__init__(*k, **kk)

            async def __call__(self, *args, **kwargs):
                handle_future.set_result(cls(self))

        def factory():
            return AsyncPipeStreamProtocol(_PipeHandle, None, loop)

        trans, protocol = await loop.create_pipe_connection(factory, address)
        conn = await handle_future  # type:AsyncPipeConnection
        return conn

    @classmethod
    async def create_pipe_connection_async(cls, address, loop=None):
        if loop is None:
            loop = asyncio_helper.get_running_loop()
        return await asyncio_helper.async_run_in_other_loop(cls._create_pipe_connection_async(address), loop)

    @classmethod
    def create_pipe_connection(cls, address, loop=None, timeout=None):
        conn = asyncio_helper.run_in_other_loop(cls._create_pipe_connection_async(address),
                                                loop, timeout=timeout)  # type:AsyncPipeConnection
        return conn

    async def _send_bytes_async(self, b_data: bytes):
        assert self.handle is not None
        b_data_head = struct.pack("!Q", len(b_data))
        self.handle.wfile.write(b_data_head + b_data)
        await self.handle.wfile.drain()

    async def _recv_bytes_async(self):
        assert self.handle is not None
        b_data_head = await self.handle.rfile.readexactly(8)
        b_data_len = struct.unpack("!Q", b_data_head)[0]
        return await self.handle.rfile.readexactly(b_data_len)

    async def _close_async(self):
        assert self.handle is not None
        await self.handle.finish()

    async def recv_bytes_async(self):
        return await asyncio_helper.async_run_in_other_loop(self._recv_bytes_async(), self.handle.protocol.loop)

    async def send_bytes_async(self, b_data: bytes):
        return await asyncio_helper.async_run_in_other_loop(self._send_bytes_async(b_data), self.handle.protocol.loop)

    async def close_async(self):
        return await asyncio_helper.async_run_in_other_loop(self._close_async(), self.handle.protocol.loop)

    def recv_bytes(self):
        return asyncio_helper.async_run_in_other_loop(self._recv_bytes_async(), self.handle.protocol.loop)

    def send_bytes(self, b_data: bytes):
        return asyncio_helper.run_in_other_loop(self._send_bytes_async(b_data), self.handle.protocol.loop)

    def close(self):
        return asyncio_helper.run_in_other_loop(self._close_async(), self.handle.protocol.loop)


class AsyncPipeServer(object):
    counter = itertools.count().__next__

    def __init__(self, address, handle, authkey=None, logger=logging.root, loop=None):
        self.address = address
        self.handle = handle
        self.authkey = authkey
        self.logger = logger
        self.loop = loop
        if self.loop is None:
            self.loop = asyncio_helper.get_running_loop()
        self.server = None

    async def _run_async(self):
        loop = asyncio_helper.get_running_loop()
        assert isinstance(loop, asyncio.ProactorEventLoop)
        pool = AsyncPool(thread_name_prefix="HandlePool-%d" % self.counter(), loop=loop)
        handle = self.handle

        class _PipeHandle(AsyncPipeStreamRequestHandler):
            def __init__(self, *k, **kk):
                super().__init__(*k, **kk)

            async def handle(self):
                await handle(AsyncPipeConnection(self))

        def factory():
            return AsyncPipeStreamProtocol(_PipeHandle, pool, loop)

        self.server = await loop.start_serving_pipe(factory, self.address)

    async def run_async(self):
        return await asyncio_helper.async_run_in_other_loop(self._run_async(), self.loop)

    def run(self):
        return asyncio_helper.run_in_other_loop(self._run_async(),self.loop)

    async def _shutdown_async(self):
        if self.server is not None:
            self.server.close()

    async def shutdown_async(self):
        return await asyncio_helper.async_run_in_other_loop(self._shutdown_async(), self.loop)

    def shutdown(self):
        return asyncio_helper.run_in_other_loop(self._shutdown_async(), self.loop)
