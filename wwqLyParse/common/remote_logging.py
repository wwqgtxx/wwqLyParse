#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
from .multiprocessing_connection import Client, Connection
import logging
import traceback
import sys

ADDRESS_LOGGING = r'\\.\pipe\%s-%s' % ("wwqLyParse", 'logging')


class RemoteStream(object):
    def __init__(self, address):
        self.address = address
        self.conn = None  # type: Connection

    def write(self, data):
        for _ in range(3):
            try:
                if self.conn is None:
                    self.conn = Client(address=self.address)
                self.conn.send_bytes(str(data).encode("utf-8"))
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

    def close(self):
        if self.conn is not None:
            self.conn.close()


class RemoteStreamHandler(logging.Handler):
    def __init__(self, address, fmt=None, date_fmt=None, style='%'):
        super(RemoteStreamHandler, self).__init__()
        self.stream = RemoteStream(address)
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
