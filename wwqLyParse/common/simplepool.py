#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import re, threading, queue, sys, json, os, time
import functools
from queue import Queue


def joinall(_threads, timeout=None):
    for _thread in _threads:
        _thread.join(timeout)


class Pool(object):
    def __init__(self, size=None):
        self.pool_size = size
        self.queue = Queue(0)
        self.pool_threads = []
        self.running = True
        if (self.pool_size is not None):
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
            f();

    def spawn(self, call_method, *k, **kk):
        f = functools.partial(call_method, *k, **kk)
        if (self.pool_size is not None):
            self.queue.put(f)
        else:
            pool_thread = threading.Thread(target=f,
                                           name="[" + str(self) + "-thread-" + str(len(self.pool_threads)) + "]")
            self.pool_threads.append(pool_thread)
            pool_thread.setDaemon(True)
            pool_thread.start()
            return pool_thread
