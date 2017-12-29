#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import re, threading, queue, sys, json, os, time
import functools
import concurrent.futures
from queue import Queue
import time


class GreenletExit(Exception):
    pass


class ThreadPoolExecutor(concurrent.futures.ThreadPoolExecutor):
    def _adjust_thread_count(self):
        time.sleep(0.01)
        if self._work_queue.qsize():
            super(ThreadPoolExecutor, self)._adjust_thread_count()

    def shutdown(self, wait=True):
        with self._shutdown_lock:
            self._shutdown = True
            for t in self._threads:
                self._work_queue.put(None)
        if wait:
            for t in self._threads:
                t.join()


class Pool(object):
    def __init__(self, size=None):
        if not size:
            size = 1000
        self.pool_size = size
        self.ex = ThreadPoolExecutor(size)
        self.pool_threads = []

    def _remove_from_pool_threads(self, future):
        try:
            self.pool_threads.remove(future)
        except ValueError:
            pass

    def spawn(self, call_method, *k, **kk):
        f = functools.partial(call_method, *k, **kk)
        future = self.ex.submit(f)
        future.add_done_callback(self._remove_from_pool_threads)
        self.pool_threads.append(future)

    def join(self, *k, timeout=None, **kk):
        while True:
            try:
                return concurrent.futures.wait(self.pool_threads, timeout)
            except ValueError:
                pass

    def kill(self, *k, block=False, **kk):
        self.ex.shutdown(wait=block)


class ThreadPool(Pool):
    def __init__(self, size=None, hub=None):
        super(ThreadPool, self).__init__(size)

    def apply(self, func, args=None, kwds=None):
        from .pool import call_method_and_save_to_queue
        queue = Queue(1)
        self.spawn(call_method_and_save_to_queue, queue, func, args, kwds)
        return queue.get()
