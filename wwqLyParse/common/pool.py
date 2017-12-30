#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
try:
    from gevent import GreenletExit
    from gevent.pool import Pool as _Pool
    from gevent.threadpool import ThreadPool as _ThreadPool
    from gevent.queue import Queue

    POOL_TYPE = "geventpool"
except:
    from .simplepool import GreenletExit
    from .simplepool import Pool as _Pool
    from .simplepool import ThreadPool as _ThreadPool
    from queue import Queue

    POOL_TYPE = "simplepool"

import threading
import itertools


def call_method_and_save_to_queue(queue, method, args=None, kwargs=None, allow_none=True):
    if args is None:
        args = ()
    if kwargs is None:
        kwargs = {}
    try:
        result = method(*args, **kwargs)
        if allow_none or result:
            queue.put(result)
    except GreenletExit:
        pass


class Pool(_Pool):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.kill(block=False)

    if POOL_TYPE == "geventpool":
        _counter = itertools.count().__next__

        def __init__(self, size=None, thread_name_prefix=''):
            super().__init__(size)
            self._thread_name_prefix = (thread_name_prefix or
                                        ("GeventPool-%d" % self._counter()))
            self._thread_name_counter = itertools.count().__next__

        def spawn(self, _fn, *args, **kwargs):
            def _spawn():
                thread_name = '%s_%d' % (self._thread_name_prefix or self,
                                         self._thread_name_counter())
                t = threading.current_thread()
                t.name = thread_name
                _fn(*args, **kwargs)

            return super(Pool, self).spawn(_spawn)


def _apply(_func, _args, _kwds):
    if _args is None:
        _args = ()
    if _kwds is None:
        _kwds = {}
    result = {"type": "ok", "result": None}
    try:
        result["result"] = _func(*_args, **_kwds)
    except BaseException as e:
        result["type"] = "error"
        result["result"] = e
    return result


class ThreadPool(_ThreadPool):
    def apply(self, func, args=None, kwds=None):
        result = super(ThreadPool, self).apply(_apply, args=(func, args, kwds))
        if result["type"] == "ok":
            return result["result"]
        else:
            raise result["result"]

    if POOL_TYPE == "geventpool":
        def __init__(self, maxsize=None, hub=None):
            if not maxsize:
                maxsize = 1000
            super(ThreadPool, self).__init__(maxsize, hub)
