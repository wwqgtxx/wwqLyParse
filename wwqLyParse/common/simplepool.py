#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import re, threading, queue, sys, json, os, time
import functools
from queue import Queue, Full


class GreenletExit(Exception):
    pass


class Pool(object):
    def __init__(self, size=None):
        self.pool_size = size
        self.queue = Queue(0)
        if self.pool_size:
            self.working_queue = Queue(size)
        self.pool_threads = []
        self.running = True
        if self.pool_size is not None:
            for i in range(size):
                self.pool_threads.append(
                    threading.Thread(target=self._pool_runner, name="[" + str(self) + "-thread-" + str(i) + "]",
                                     args=[self.queue]))
            for pool_thread in self.pool_threads:
                pool_thread.setDaemon(True)
                pool_thread.start()

    def _pool_runner(self, queue):
        while self.running:
            f = queue.get()
            try:
                self.working_queue.put(None)
                f()
            finally:
                self.working_queue.get()

    def spawn(self, call_method, *k, **kk):
        f = functools.partial(call_method, *k, **kk)
        if self.pool_size is not None:
            self.running = True
            self.queue.put(f)
        else:
            pool_thread = threading.Thread(target=f,
                                           name="[" + str(self) + "-thread-" + str(len(self.pool_threads)) + "]")
            self.pool_threads.append(pool_thread)
            pool_thread.setDaemon(True)
            pool_thread.start()
            return pool_thread

    def join(self, *k, timeout=None, **kk):
        if self.pool_size is not None:
            num = 0
            try:
                for i in range(self.pool_size):
                    try:
                        self.working_queue.put(None, block=True, timeout=timeout)
                    except Full:
                        return False
                    else:
                        num = num + 1
                return True
            finally:
                for i in range(num):
                    self.working_queue.get()
        else:
            for _thread in self.pool_threads:
                _thread.join(timeout)

    def kill(self, *k, block=False, **kk):
        def _do_nothing():
            pass

        if self.pool_size is not None:
            self.running = False
            for i in range(self.pool_size):
                self.queue.put(_do_nothing)
