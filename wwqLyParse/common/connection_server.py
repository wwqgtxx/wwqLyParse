#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
import multiprocessing.connection
from . import asyncio
from .async_pool import *
from .async_connection import *
import itertools
import logging
from typing import Dict, Tuple, List, Callable

CONN_LRU_TIMEOUT = 60 * 60  # 1 hour


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
        self.connection_selector = get_common_mp_connection_selector()
        self.handle_pool = AsyncPool(thread_name_prefix="HandlePool-%d" % self._counter(), loop=self.loop)

    async def _handle(self, conn: AsyncMPConnection):
        try:
            while True:
                data = await asyncio.wait_for(conn.recv_bytes_async(parse_func=self.recv_parse_func), CONN_LRU_TIMEOUT)
                self.logger.debug("parse conn %s" % conn)
                # self.logger.debug(data)
                try:
                    result = await asyncio.async_run_func_or_co(self.handle, data)
                except Exception:
                    self.logger.exception("handle error")
                else:
                    if result is not None:
                        await asyncio.wait_for(conn.send_bytes_async(result, parse_func=self.send_parse_func),
                                               CONN_LRU_TIMEOUT)
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
        with multiprocessing.connection.Listener(self.address, authkey=self.authkey) as listener:
            while True:
                try:
                    conn = listener.accept()
                    self.logger.debug("get a new conn %s" % conn)
                    self.loop.call_soon_threadsafe(self.handle_pool.spawn,
                                                   self._handle(AsyncMPConnection(conn, self.connection_selector)))
                except:
                    self.logger.exception("error")


__all__ = ["ConnectionServer", "CONN_LRU_TIMEOUT"]
