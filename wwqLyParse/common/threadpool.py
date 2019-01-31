#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>

import functools
import logging
from .concurrent_futures import ThreadPoolExecutor
from .concurrent_futures import wait


def call_method_and_save_to_queue(queue, method, args=None, kwargs=None, allow_none=True):
    if args is None:
        args = ()
    if kwargs is None:
        kwargs = {}
    try:
        result = method(*args, **kwargs)
        if allow_none or result:
            queue.put(result)
    except SystemExit:
        raise


class ThreadPool(ThreadPoolExecutor):
    def __init__(self, size=None, thread_name_prefix=''):
        super().__init__(max_workers=size, thread_name_prefix=thread_name_prefix)
        self.pool_size = size
        self.pool_threads = []
        # logging.debug("new pool %s" % self)

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
        future = self.submit(f)
        future.add_done_callback(self._remove_from_pool_threads)
        self.pool_threads.append(future)
        return future

    def join(self, *k, timeout=None, **kk):
        while True:
            if len(self.pool_threads) == 0:
                return
            try:
                return wait(self.pool_threads, timeout)
            except ValueError:
                pass

    def kill(self, *k, block=False, **kk):
        self.shutdown(wait=block)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.kill(block=False)

    @staticmethod
    def wait(wait_list, timeout=None):
        return wait(wait_list, timeout=timeout)


__all__ = ["ThreadPool"]
