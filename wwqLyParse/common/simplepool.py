#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>

import functools
import itertools
import weakref
import threading
import logging
from queue import Queue, Empty
import time
from .concurrent_futures import ThreadPoolExecutor
from .concurrent_futures import wait as _wait


class GreenletExit(Exception):
    pass


class Pool(object):
    def __init__(self, size=None, thread_name_prefix=''):
        self.pool_size = size
        self.ex = ThreadPoolExecutor(size, thread_name_prefix=thread_name_prefix, class_name="ThreadPool")
        self.pool_threads = []

    def _remove_from_pool_threads(self, future):
        try:
            self.pool_threads.remove(future)
        except ValueError:
            pass

    def apply(self, func, args=None, kwds=None):
        if args is None:
            args = ()
        if kwds is None:
            kwds = {}
        return self.spawn(func, *args, **kwds).result()

    def spawn(self, call_method, *k, **kk):
        f = functools.partial(call_method, *k, **kk)
        future = self.ex.submit(f)
        future.add_done_callback(self._remove_from_pool_threads)
        self.pool_threads.append(future)
        return future

    def join(self, *k, timeout=None, **kk):
        while True:
            try:
                return _wait(self.pool_threads, timeout)
            except ValueError:
                pass

    def kill(self, *k, block=False, **kk):
        self.ex.shutdown(wait=block)


class ThreadPool(Pool):
    def __init__(self, size=None, hub=None):
        super(ThreadPool, self).__init__(size)
        logging.debug("new pool %s" % self)

    def apply(self, func, args=None, kwds=None):
        return self.spawn(func, *args, **kwds).result()
