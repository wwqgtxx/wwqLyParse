#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
import multiprocessing.connection as multiprocessing_connection
from . import asyncio_helper
import asyncio
from .async_pool import *
from .lru_cache import *
from .threadpool import *
import collections
import itertools
import logging
from typing import Dict, Tuple, List, Callable

CONN_LRU_TIMEOUT = 60 * 60  # 1 hour


class ConnectionLoop(object):
    _counter = itertools.count().__next__

    def __init__(self, logger=logging.root):
        self.logger = logger
        self.c_recv, self.c_send = multiprocessing_connection.Pipe(False)
        self.conn_lru_dict = collections.defaultdict(list)
        self.pool = ThreadPool(thread_name_prefix="ConnectionLoopPool-%d" % self._counter())
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
                for conn in multiprocessing_connection.wait(conn_list):
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

    async def recv_bytes_async(self, conn: multiprocessing_connection.Connection, maxlength=None, parse_func=None):
        loop = asyncio_helper.get_running_loop()
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

    async def send_bytes_async(self, conn: multiprocessing_connection.Connection, buf: bytes, parse_func=None):
        def _send():
            if parse_func is not None:
                data = parse_func(buf)
            else:
                data = buf
            conn.send_bytes(data)

        return await asyncio_helper.async_run_func_or_co(_send)


_common_connection_loop = None


def get_common_connection_loop():
    global _common_connection_loop
    if _common_connection_loop is None:
        _common_connection_loop = ConnectionLoop()
    return _common_connection_loop


class AsyncConnection(object):
    def __init__(self, conn: multiprocessing_connection.Connection, connection_loop: ConnectionLoop):
        self._conn = conn
        self._connection_loop = connection_loop

    async def recv_bytes_async(self, maxlength=None, parse_func=None):
        return await self._connection_loop.recv_bytes_async(self._conn, maxlength=maxlength, parse_func=parse_func)

    async def send_bytes_async(self, buf: bytes, parse_func=None):
        return await self._connection_loop.send_bytes_async(self._conn, buf, parse_func=parse_func)

    @property
    def closed(self):
        return self._conn.closed

    def close(self):
        return self._conn.close()


class ConnectionServer(object):
    _counter = itertools.count().__next__

    def __init__(self,
                 address: str,
                 handle,
                 loop: asyncio.AbstractEventLoop,
                 authkey: bytes = None,
                 logger=logging.root,
                 recv_parse_func: Callable = None,
                 send_parse_func: Callable = None):
        self.address = address
        self.loop = loop
        self.handle = handle
        self.authkey = authkey
        self.logger = logger
        self.recv_parse_func = recv_parse_func
        self.send_parse_func = send_parse_func
        self.connection_loop = get_common_connection_loop()
        self.handle_pool = AsyncPool(thread_name_prefix="HandlePool-%d" % self._counter(), loop=self.loop)

    async def _handle(self, conn: AsyncConnection):
        try:
            while True:
                data = await asyncio.wait_for(conn.recv_bytes_async(parse_func=self.recv_parse_func), CONN_LRU_TIMEOUT)
                self.logger.debug("parse conn %s" % conn)
                # self.logger.debug(data)
                try:
                    result = await asyncio_helper.async_run_func_or_co(self.handle, data)
                except Exception:
                    self.logger.exception("handle error")
                else:
                    if result is not None:
                        await asyncio.wait_for(conn.send_bytes_async(result,parse_func=self.send_parse_func), CONN_LRU_TIMEOUT)
        except asyncio.TimeoutError:
            self.logger.debug("conn %s was timeout" % conn)
            conn.close()
        except OSError:
            self.logger.debug("conn %s was closed" % conn)
            conn.close()
        except EOFError:
            self.logger.debug("conn %s was eof" % conn)
            conn.close()
        except BrokenPipeError:
            self.logger.debug("conn %s was broken" % conn)
            conn.close()

    def run(self):
        with multiprocessing_connection.Listener(self.address, authkey=self.authkey) as listener:
            while True:
                try:
                    conn = listener.accept()
                    self.logger.debug("get a new conn %s" % conn)
                    self.loop.call_soon_threadsafe(self.handle_pool.spawn,
                                                   self._handle(AsyncConnection(conn, self.connection_loop)))
                except:
                    self.logger.exception("error")
