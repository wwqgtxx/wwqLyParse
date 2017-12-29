#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
import multiprocessing.connection
from .pool import ThreadPool


class Connection(object):
    def __init__(self, _connection):
        self._connection = _connection
        self._connection_threadpool = ThreadPool(5)

    closed = property(lambda self: self._connection.closed)
    readable = property(lambda self: self._connection.readable)
    writable = property(lambda self: self._connection.writable)

    def fileno(self):
        return self._connection_threadpool.apply(self._connection.fileno)

    def close(self):
        try:
            return self._connection_threadpool.apply(self._connection.close)
        finally:
            self._connection_threadpool.kill()

    def send_bytes(self, buf, offset=0, size=None):
        return self._connection_threadpool.apply(self._connection.send_bytes, args=(buf, offset, size))

    def send(self, obj):
        return self._connection_threadpool.apply(self._connection.send, args=(obj,))

    def recv_bytes(self, maxlength=None):
        return self._connection_threadpool.apply(self._connection.recv_bytes, args=(maxlength,))

    def recv_bytes_into(self, buf, offset=0):
        return self._connection_threadpool.apply(self._connection.recv_bytes_into, args=(buf, offset))

    def recv(self):
        return self._connection_threadpool.apply(self._connection.recv)

    def poll(self, timeout=0.0):
        return self._connection_threadpool.apply(self._connection.pool, args=(timeout,))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()


class Listener(object):
    def __init__(self, address=None, family=None, backlog=1, authkey=None):
        self._listener = multiprocessing.connection.Listener(address=address, family=family, backlog=backlog,
                                                             authkey=authkey)
        self._listener_threadpool = ThreadPool(2)

    def accept(self):
        return Connection(self._listener_threadpool.apply(self._listener.accept))

    def close(self):
        try:
            return self._listener_threadpool.apply(self._listener.close)
        finally:
            self._listener_threadpool.kill()

    address = property(lambda self: self._listener.address)
    last_accepted = property(lambda self: self._listener.last_accepted)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()
