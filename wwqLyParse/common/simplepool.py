#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import re, threading, queue, sys, json, os, time
import functools
import concurrent.futures
from queue import Queue


class GreenletExit(Exception):
    pass


class Pool(object):
    def __init__(self, size=None):
        self.pool_size = size
        self.queue = Queue(0)
        if self.pool_size is not None:
            self.ex = concurrent.futures.ThreadPoolExecutor(size)
        self.pool_threads = []

    def spawn(self, call_method, *k, **kk):
        f = functools.partial(call_method, *k, **kk)
        if self.pool_size is not None:
            self.pool_threads.append(self.ex.submit(f))
        else:
            pool_thread = threading.Thread(target=f,
                                           name="[" + str(self) + "-thread-" + str(len(self.pool_threads)) + "]")
            self.pool_threads.append(pool_thread)
            pool_thread.setDaemon(True)
            pool_thread.start()
            return pool_thread

    def join(self, *k, timeout=None, **kk):
        if self.pool_size is not None:
            concurrent.futures.wait(self.ex, timeout)
        else:
            for _thread in self.pool_threads:
                _thread.join(timeout)

    def kill(self, *k, block=False, **kk):
        if self.pool_size is not None:
            self.ex.shutdown(wait=block)
