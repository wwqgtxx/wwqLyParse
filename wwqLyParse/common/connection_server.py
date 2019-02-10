#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
import multiprocessing.connection
from . import asyncio
from .async_pool import *
from .async_pipe_connection import *
import itertools
import logging
from typing import Dict, Tuple, List, Callable

CONN_LRU_TIMEOUT = 60 * 60  # 1 hour


class ConnectionServer(object):
    _counter = itertools.count().__next__

    def __init__(self,
                 address: str,
                 handle,
                 authkey: bytes = None,
                 wrap_ssl=False,
                 logger=logging.root):
        self.address = address
        self.handle = handle
        self.authkey = authkey
        self.wrap_ssl = wrap_ssl
        self.logger = logger

    async def _handle(self, conn: AsyncPipeConnection):
        try:
            if self.authkey:
                await conn.do_auth(self.authkey)
            while True:
                data = await asyncio.wait_for(conn.recv_bytes(), CONN_LRU_TIMEOUT)
                if not data:
                    raise EOFError
                self.logger.debug("parse conn %s" % conn)
                # self.logger.debug(data)
                try:
                    result = await asyncio.async_run_func_or_co(self.handle, data)
                except Exception:
                    self.logger.exception("handle error")
                else:
                    if result is not None:
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

    async def run(self):
        handle_pool = AsyncPool(thread_name_prefix="HandlePool-%d" % self._counter())
        async with AsyncPipeListener(self.address, wrap_ssl=self.wrap_ssl) as listener:
            while True:
                try:
                    conn = await listener.accept()
                    self.logger.debug("get a new conn %s" % conn)
                    handle_pool.spawn(self._handle(conn))
                except:
                    self.logger.exception("error")


__all__ = ["ConnectionServer", "CONN_LRU_TIMEOUT"]
