#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
import multiprocessing.connection
import functools
from typing import Dict, Tuple, List
from .workerpool import RealThreadPool, POOL_TYPE, get_common_real_thread_pool

if POOL_TYPE == "geventpool":
    class Connection(object):
        def __init__(self, _connection: multiprocessing.connection.Connection,
                     _connection_threadpool: RealThreadPool = None):
            self._connection = _connection
            if _connection_threadpool is None:
                self._connection_threadpool = get_common_real_thread_pool()
                self._need_close_connection_threadpool = True
            else:
                self._connection_threadpool = _connection_threadpool
                self._need_close_connection_threadpool = False

        closed = property(lambda self: self._connection.closed)
        readable = property(lambda self: self._connection.readable)
        writable = property(lambda self: self._connection.writable)

        def fileno(self):
            return self._connection_threadpool.apply(self._connection.fileno)

        def close(self):
            try:
                return self._connection_threadpool.apply(self._connection.close)
            finally:
                if self._need_close_connection_threadpool:
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
            return self._connection_threadpool.apply(self._connection.poll, args=(timeout,))

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, exc_tb):
            self.close()


    class Listener(object):
        def __init__(self, address=None, family=None, backlog=1, authkey=None, _listener_threadpool: RealThreadPool = None):
            self._listener = multiprocessing.connection.Listener(address=address, family=family, backlog=backlog,
                                                                 authkey=authkey)
            if _listener_threadpool is None:
                self._listener_threadpool = get_common_real_thread_pool()
                self._listener_threadpool_need_closed = True
            else:
                self._listener_threadpool = _listener_threadpool
                self._listener_threadpool_need_closed = False

        def accept(self):
            return Connection(self._listener_threadpool.apply(self._listener.accept), self._listener_threadpool)

        def close(self):
            try:
                return self._listener_threadpool.apply(self._listener.close)
            finally:
                if self._listener_threadpool_need_closed:
                    self._listener_threadpool.kill()

        address = property(lambda self: self._listener.address)
        last_accepted = property(lambda self: self._listener.last_accepted)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, exc_tb):
            self.close()


    def Client(address, family=None, authkey=None, _threadpool: RealThreadPool = None) -> Connection:
        if _threadpool is None:
            _threadpool = get_common_real_thread_pool()
        c = _threadpool.apply(multiprocessing.connection.Client, args=(address, family, authkey))
        return Connection(c, _threadpool)


    def wait(object_list, timeout=None, _threadpool: RealThreadPool = None) -> List[Connection]:
        if _threadpool is None:
            _threadpool = get_common_real_thread_pool()
        return _threadpool.apply(multiprocessing.connection.wait, args=(object_list, timeout))


    def Pipe(duplex=True, _threadpool: RealThreadPool = None) -> Tuple[Connection, Connection]:
        if _threadpool is None:
            _threadpool = get_common_real_thread_pool()
        c1, c2 = multiprocessing.connection.Pipe(duplex)
        return Connection(c1, _threadpool), Connection(c2, _threadpool)

else:
    class _Listener(multiprocessing.connection.Listener):
        def __init__(self, address=None, family=None, backlog=1, authkey=None, _listener_threadpool=None):
            super(_Listener, self).__init__(address, family, backlog, authkey)


    Connection = multiprocessing.connection.Connection
    Listener = _Listener


    def Client(address, family=None, authkey=None, _threadpool: RealThreadPool = None) -> Connection:
        return multiprocessing.connection.Client(address, family, authkey)


    def wait(object_list, timeout=None, _threadpool=None) -> List[Connection]:
        return multiprocessing.connection.wait(object_list, timeout)


    def Pipe(duplex=True, _threadpool=None) -> Tuple[Connection, Connection]:
        return multiprocessing.connection.Pipe(duplex)
