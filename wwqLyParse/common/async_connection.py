#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
import multiprocessing.connection
from . import asyncio
from .threadpool import *
import collections
import itertools
import logging


class MPConnectionSelector(object):
    _counter = itertools.count().__next__

    def __init__(self, logger=logging.root):
        self.logger = logger
        self.c_recv, self.c_send = multiprocessing.connection.Pipe(False)
        self.conn_lru_dict = collections.defaultdict(list)
        self.pool = ThreadPool(thread_name_prefix="MPCSelectorPool-%d" % self._counter())
        self.pool.spawn(self._select)

    def _select(self):
        self.logger.debug("start %s's select loop", self)
        while True:
            try:
                conn_list_raw = list(self.conn_lru_dict.keys())
                conn_list = list()
                conn_list.append(self.c_recv)
                for conn in conn_list_raw:
                    if not conn.closed:
                        conn_list.append(conn)
                    else:
                        self._call_cb(conn)
                # logging.debug("select:%s", conn_list)
                for conn in multiprocessing.connection.wait(conn_list):
                    if conn == self.c_recv:
                        self.c_recv.recv_bytes()
                        continue
                    self._call_cb(conn)
            except OSError as e:
                if getattr(e, "winerror", 0) == 6:
                    continue
                logging.exception("OSError")
            except:
                logging.exception("error")

    def _call_cb(self, conn):
        cb_list = self.conn_lru_dict.pop(conn)
        for cb in cb_list:
            self.pool.spawn(cb)

    def _write_to_self(self):
        self.c_send.send_bytes(b'ok')

    async def recv_bytes_async(self, conn: multiprocessing.connection.Connection, maxlength=None, parse_func=None):
        loop = asyncio.get_running_loop()
        future = loop.create_future()

        def _recv_cb():
            try:
                data = conn.recv_bytes(maxlength=maxlength)
                if not data:
                    raise EOFError
                if parse_func is not None:
                    data = parse_func(data)
            except BaseException as e:
                loop.call_soon_threadsafe(future.set_exception, e)
            else:
                loop.call_soon_threadsafe(future.set_result, data)

        self.conn_lru_dict[conn].append(_recv_cb)
        self._write_to_self()
        try:
            return await future
        finally:
            try:
                self.conn_lru_dict[conn].remove(_recv_cb)
            except ValueError:
                pass

    async def send_bytes_async(self, conn: multiprocessing.connection.Connection, buf: bytes, parse_func=None):
        def _send():
            if parse_func is not None:
                data = parse_func(buf)
            else:
                data = buf
            conn.send_bytes(data)

        return await asyncio.async_run_func_or_co(_send)


_common_mp_connection_selector = None


def get_common_mp_connection_selector():
    global _common_mp_connection_selector
    if _common_mp_connection_selector is None:
        _common_mp_connection_selector = MPConnectionSelector()
    return _common_mp_connection_selector


class AsyncMPConnection(object):
    def __init__(self, conn: multiprocessing.connection.Connection, connection_selector: MPConnectionSelector):
        self._conn = conn
        self._connection_selector = connection_selector

    async def recv_bytes_async(self, maxlength=None, parse_func=None):
        return await self._connection_selector.recv_bytes_async(self._conn, maxlength=maxlength, parse_func=parse_func)

    async def send_bytes_async(self, buf: bytes, parse_func=None):
        return await self._connection_selector.send_bytes_async(self._conn, buf, parse_func=parse_func)

    @property
    def closed(self):
        return self._conn.closed

    def close(self):
        return self._conn.close()


__all__ = ["MPConnectionSelector", "get_common_mp_connection_selector", "AsyncMPConnection"]

"""
from . import asyncio
from .async_pool import AsyncPool
import os
import struct
import logging
import itertools


class AsyncPipeConnection(object):
    def __init__(self, handle: asyncio.AsyncPipeStreamRequestHandler):
        self.handle = handle

    @classmethod
    async def _create_pipe_connection_async(cls, address, family=None, authkey=None):
        loop = asyncio.get_running_loop()
        assert isinstance(loop, asyncio.ProactorEventLoop)
        handle_future = loop.create_future()

        class _PipeHandle(asyncio.AsyncPipeStreamRequestHandler):
            def __init__(self, *k, **kk):
                super().__init__(*k, **kk)

            async def __call__(self, *args, **kwargs):
                handle_future.set_result(cls(self))

        def factory():
            return asyncio.AsyncPipeStreamProtocol(_PipeHandle, None, loop)

        trans, protocol = await loop.create_pipe_connection(factory, address)
        conn = await handle_future  # type:AsyncPipeConnection
        try:
            if authkey is not None:
                await conn._answer_challenge_async(authkey)
                await conn._deliver_challenge_async(authkey)
        except AuthenticationError:
            await conn._close_async()
        return conn

    @classmethod
    async def create_pipe_connection_async(cls, address, family=None, authkey=None, loop=None):
        if loop is None:
            loop = asyncio.get_running_loop()
        conn = await asyncio.async_run_in_loop(cls._create_pipe_connection_async(address, family, authkey),
                                                      loop)  # type:AsyncPipeConnection
        return conn

    @classmethod
    def create_pipe_connection(cls, address, family=None, authkey=None, loop=None, timeout=None):
        conn = asyncio.run_in_other_loop(cls._create_pipe_connection_async(address, family, authkey),
                                                loop, timeout=timeout)  # type:AsyncPipeConnection
        return conn

    async def _send_bytes_async(self, b_data: bytes):
        assert self.handle is not None
        b_data_head = struct.pack("!Q", len(b_data))
        self.handle.wfile.write(b_data_head + b_data)
        await self.handle.wfile.drain()

    async def _recv_bytes_async(self, max_size=None):
        assert self.handle is not None
        if max_size is None:
            max_size = asyncio.PIPE_MAX_BYTES
        b_data_head = await self.handle.rfile.readexactly(8)
        b_data_len = struct.unpack("!Q", b_data_head)[0]
        if b_data_len > max_size:
            raise asyncio.LimitOverrunError("data too big", b_data_len)
        return await self.handle.rfile.readexactly(b_data_len)

    async def _close_async(self):
        assert self.handle is not None
        await self.handle.finish()

    async def recv_bytes_async(self):
        return await asyncio.async_run_in_loop(self._recv_bytes_async(), self.handle.protocol.loop)

    async def send_bytes_async(self, b_data: bytes):
        return await asyncio.async_run_in_loop(self._send_bytes_async(b_data), self.handle.protocol.loop)

    async def close_async(self):
        return await asyncio.async_run_in_loop(self._close_async(), self.handle.protocol.loop)

    def recv_bytes(self):
        return asyncio.async_run_in_loop(self._recv_bytes_async(), self.handle.protocol.loop)

    def send_bytes(self, b_data: bytes):
        return asyncio.run_in_other_loop(self._send_bytes_async(b_data), self.handle.protocol.loop)

    def close(self):
        return asyncio.run_in_other_loop(self._close_async(), self.handle.protocol.loop)

    def __enter__(self):
        return self

    async def __aenter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_async()

    async def _deliver_challenge_async(self, authkey: bytes):
        import hmac
        if not isinstance(authkey, bytes):
            raise ValueError(
                "Authkey must be bytes, not {0!s}".format(type(authkey)))
        try:
            message = os.urandom(MESSAGE_LENGTH)
            await self._send_bytes_async(CHALLENGE + message)
            digest = hmac.new(authkey, message, 'md5').digest()
            response = await self._recv_bytes_async(256)  # reject large message
            if response == digest:
                await self._send_bytes_async(WELCOME)
            else:
                await self._send_bytes_async(FAILURE)
                raise AuthenticationError('digest received was wrong')
        except asyncio.LimitOverrunError as e:
            await self._send_bytes_async(FAILURE)
            raise AuthenticationError(e)

    async def _answer_challenge_async(self, authkey: bytes):
        import hmac
        if not isinstance(authkey, bytes):
            raise ValueError(
                "Authkey must be bytes, not {0!s}".format(type(authkey)))
        try:
            message = await self._recv_bytes_async(256)  # reject large message
            assert message[:len(CHALLENGE)] == CHALLENGE, 'message = %r' % message
            message = message[len(CHALLENGE):]
            digest = hmac.new(authkey, message, 'md5').digest()
            await self._send_bytes_async(digest)
            response = await self._recv_bytes_async(256)  # reject large message
            if response != WELCOME:
                raise AuthenticationError('digest sent was rejected')
        except asyncio.LimitOverrunError as e:
            raise AuthenticationError(e)


class AsyncPipeServer(object):
    counter = itertools.count().__next__

    def __init__(self, address, handle, authkey=None, logger=logging.root, loop=None):
        self.address = address
        self.handle = handle
        self.authkey = authkey
        self.logger = logger
        self.loop = loop
        if self.loop is None:
            self.loop = asyncio.get_running_loop()
        self.server = None

    async def _run_async(self):
        loop = asyncio.get_running_loop()
        assert isinstance(loop, asyncio.ProactorEventLoop)
        pool = AsyncPool(thread_name_prefix="HandlePool-%d" % self.counter(), loop=loop)
        handle = self.handle
        authkey = self.authkey

        class _PipeHandle(asyncio.AsyncPipeStreamRequestHandler):
            def __init__(self, *k, **kk):
                super().__init__(*k, **kk)

            async def handle(self):
                conn = AsyncPipeConnection(self)
                if authkey is not None:
                    await conn._deliver_challenge_async(authkey)
                    await conn._answer_challenge_async(authkey)
                await handle(conn)

        def factory():
            return asyncio.AsyncPipeStreamProtocol(_PipeHandle, pool, loop)

        self.server = await loop.start_serving_pipe(factory, self.address)

    async def run_async(self):
        return await asyncio.async_run_in_loop(self._run_async(), self.loop)

    def run(self):
        return asyncio.run_in_other_loop(self._run_async(), self.loop)

    async def _shutdown_async(self):
        if self.server is not None:
            self.server.close()

    async def shutdown_async(self):
        return await asyncio.async_run_in_loop(self._shutdown_async(), self.loop)

    def shutdown(self):
        return asyncio.run_in_other_loop(self._shutdown_async(), self.loop)


class AuthenticationError(Exception):
    pass


#
# Authentication stuff
#

MESSAGE_LENGTH = 20

CHALLENGE = b'#CHALLENGE#'
WELCOME = b'#WELCOME#'
FAILURE = b'#FAILURE#'


class AsyncConnectionServer(AsyncPipeServer):
    def __init__(self, address, handle, authkey=None, logger=logging.root, loop=None, run_directly=False):
        super().__init__(address, handle, authkey, logger, loop)
        self.raw_handle = handle
        self.handle = self._handle
        self.run_directly = run_directly

    async def _handle(self, conn: AsyncPipeConnection):
        try:
            while True:
                data = await conn.recv_bytes()
                if not data:
                    raise EOFError
                self.logger.debug("parse conn %s" % conn)
                # self.logger.debug(data)
                try:
                    if self.run_directly:
                        result = self.raw_handle(data)
                    else:
                        result = await asyncio.async_run_func_or_co(self.raw_handle, data)
                except Exception:
                    self.logger.exception("handle error")
                else:
                    if result is not None:
                        await conn.send_bytes_async(result)
        except asyncio.IncompleteReadError:
            self.logger.debug("conn %s was IncompleteRead" % conn)
        except OSError:
            self.logger.debug("conn %s was closed" % conn)
        except EOFError:
            self.logger.debug("conn %s was eof" % conn)
        except BrokenPipeError:
            self.logger.debug("conn %s was broken" % conn)
"""
