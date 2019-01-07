#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
import multiprocessing.connection as multiprocessing_connection
from .lru_cache import *
from .threadpool import *
import itertools
import logging
from typing import Dict, Tuple, List

CONN_LRU_TIMEOUT = 60 * 60  # 1 hour


class ConnectionServer(object):
    _counter = itertools.count().__next__

    def __init__(self, address, handle, authkey=None, logger=logging.root):
        self.address = address
        self.handle = handle
        self.authkey = authkey
        self.logger = logger

    def _handle(self, conn_lru_dict: LRUCacheType[multiprocessing_connection.Connection, bool],
                conn: multiprocessing_connection.Connection, c_send: multiprocessing_connection.Connection):
        try:
            data = conn.recv_bytes()
            if not data:
                raise EOFError
            self.logger.debug("parse conn %s" % conn)
            # self.logger.debug(data)
            try:
                result = self.handle(data)
                if result is not None:
                    conn.send_bytes(result)
            except Exception:
                self.logger.exception("handle error")
            conn_lru_dict[conn] = True
            c_send.send_bytes(b'ok')
        except OSError:
            self.logger.debug("conn %s was closed" % conn)
            conn.close()
        except EOFError:
            self.logger.debug("conn %s was eof" % conn)
            conn.close()
        except BrokenPipeError:
            self.logger.debug("conn %s was broken" % conn)
            conn.close()

    def _process(self, conn_lru_dict: LRUCacheType[multiprocessing_connection.Connection, bool],
                 handle_pool: ThreadPool,
                 c_recv: multiprocessing_connection.Connection,
                 c_send: multiprocessing_connection.Connection,
                 wait=multiprocessing_connection.wait):
        while True:
            try:
                for conn in wait(list(conn_lru_dict.keys()) + [c_recv]):
                    if conn == c_recv:
                        c_recv.recv_bytes()
                        continue
                    del conn_lru_dict[conn]
                    if not conn.closed:
                        handle_pool.spawn(self._handle, conn_lru_dict, conn, c_send)
                    else:
                        self.logger.debug("conn %s was closed" % conn)
            except OSError as e:
                if getattr(e, "winerror", 0) == 6:
                    continue
                logging.exception("OSError")
            except:
                logging.exception("error")

    def run(self):
        with ThreadPool(thread_name_prefix="HandlePool-%d" % self._counter()) as handle_pool:
            with multiprocessing_connection.Listener(self.address, authkey=self.authkey) as listener:
                c_recv, c_send = multiprocessing_connection.Pipe(False)

                def after_delete_handle(t: Tuple[multiprocessing_connection.Connection, bool]):
                    k, v = t
                    self.logger.debug("close timeout conn %s" % k)
                    c_send.send_bytes(b'ok')
                    k.close()

                conn_lru_dict = LRUCache(size=1024, timeout=CONN_LRU_TIMEOUT, after_delete_handle=after_delete_handle)
                handle_pool.spawn(self._process, conn_lru_dict, handle_pool, c_recv, c_send)
                while True:
                    try:
                        conn = listener.accept()
                        self.logger.debug("get a new conn %s" % conn)
                        conn_lru_dict[conn] = True
                        c_send.send_bytes(b'ok')
                    except:
                        logging.exception("error")
