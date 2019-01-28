#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
from multiprocessing.connection import Client, Connection
# from .async_connection import *
# from . import asyncio
# import concurrent.futures
import logging
import traceback
import sys

ADDRESS_LOGGING = r'\\.\pipe\%s-%s' % ("wwqLyParse", 'logging')


class RemoteStream(object):
    def __init__(self, address):  # , loop):
        self.address = address
        # self.loop = loop
        self.conn = None  # type: Connection
        self.conn = None  # type: # AsyncPipeConnection

    def write(self, data):
        for _ in range(3):
            try:
                if self.conn is None:
                    self.conn = Client(address=self.address)
                    # self.conn = AsyncPipeConnection.create_pipe_connection(self.address, loop=self.loop)
                    # logging.debug("get remote_logging connection %s" % self.conn)
                if self.conn:
                    self.conn.send_bytes(str(data).encode("utf-8"))
                return
            # except AuthenticationError:
            #     self.conn = None
            #     return
            # except asyncio.InSameLoopError:
            #     self.conn = None
            #     return
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

    def close(self):
        if self.conn is not None:
            self.conn.close()


class RemoteStreamHandler(logging.Handler):
    def __init__(self, address, fmt=None, date_fmt=None, style='%'):  # , loop=None):
        super(RemoteStreamHandler, self).__init__()
        self.stream = RemoteStream(address)  # , loop)
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
    # pc_loop = asyncio.new_running_async_loop("RemoteLogging")
    logging.root.addHandler(RemoteStreamHandler(ADDRESS_LOGGING, fmt, date_fmt, style))
    # logging.root.addHandler(RemoteStreamHandler(ADDRESS_LOGGING, fmt, date_fmt, style, loop=pc_loop))
