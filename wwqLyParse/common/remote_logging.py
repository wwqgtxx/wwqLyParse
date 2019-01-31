#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
# from multiprocessing.connection import Client, Connection
from .async_pipe_connection import *
from . import asyncio
# import concurrent.futures
import logging
import traceback
import sys

ADDRESS_LOGGING = r'\\.\pipe\%s-%s' % ("wwqLyParse", 'logging')


class RemoteStream(object):
    def __init__(self, address, loop):
        self.address = address
        self.loop = loop
        self.conn = None  # type: AsyncPipeConnection

    async def _write(self, data):
        data = str(data).encode("utf-8")
        for _ in range(3):
            try:
                if self.conn is None:
                    self.conn = await AsyncPipeClient(self.address)
                if self.conn:
                    await self.conn.send_bytes(data)
                return
            except FileNotFoundError:
                self.conn = None
                return
            except BrokenPipeError:
                self.conn = None
            except OSError:
                self.conn = None
            except EOFError:
                self.conn = None
            except Exception:
                print(traceback.format_exc())
                self.conn = None

    def write(self, data):
        asyncio.run_coroutine_threadsafe(self._write(data), self.loop)

    def close(self):
        if self.conn is not None:
            self.conn.close()


class RemoteStreamHandler(logging.Handler):
    def __init__(self, address, fmt=None, date_fmt=None, style='%', loop=None):
        super(RemoteStreamHandler, self).__init__()
        self.stream = RemoteStream(address, loop)
        fmt = logging.Formatter(fmt, date_fmt, style)
        self.setFormatter(fmt)
        # logging.root.addHandler(self)

    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            stream.write(msg)
        except Exception:
            self.handleError(record)


def add_remote_logging(fmt=None, date_fmt=None, style='%'):
    pc_loop = asyncio.new_running_async_loop("RemoteLogging")
    logging.root.addHandler(RemoteStreamHandler(ADDRESS_LOGGING, fmt, date_fmt, style, loop=pc_loop))
