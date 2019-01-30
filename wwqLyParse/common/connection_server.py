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
        self.handle_pool = AsyncPool(thread_name_prefix="HandlePool-%d" % self._counter(), loop=self.loop)

    async def _handle(self, conn: AsyncPipeConnection):
        try:
            if self.authkey:
                await conn.do_auth(self.authkey)
            while True:
                data = await asyncio.wait_for(conn.recv_bytes(), CONN_LRU_TIMEOUT)
                if not data:
                    raise EOFError
                if self.recv_parse_func is not None:
                    data = self.recv_parse_func(data)
                self.logger.debug("parse conn %s" % conn)
                # self.logger.debug(data)
                try:
                    result = await asyncio.async_run_func_or_co(self.handle, data)
                except Exception:
                    self.logger.exception("handle error")
                else:
                    if result is not None:
                        if self.send_parse_func is not None:
                            result = self.send_parse_func(result)
                        await asyncio.wait_for(conn.send_bytes(result), CONN_LRU_TIMEOUT)
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

    async def _run(self):
        async with AsyncPipeListener(self.address) as listener:
            while True:
                try:
                    conn = await listener.accept()
                    self.logger.debug("get a new conn %s" % conn)
                    self.handle_pool.spawn(self._handle(conn))
                except:
                    self.logger.exception("error")

    def run(self):
        asyncio.run_in_other_loop(self._run(), self.loop)


__all__ = ["ConnectionServer", "CONN_LRU_TIMEOUT"]
