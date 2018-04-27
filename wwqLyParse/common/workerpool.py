#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
try:
    from .geventpool import GreenletExit
    from .geventpool import Pool as _Pool
    from .geventpool import ThreadPool as _ThreadPool
    from .geventpool import Queue

    POOL_TYPE = "geventpool"
except:
    from .simplepool import GreenletExit
    from .simplepool import Pool as _Pool
    from .simplepool import ThreadPool as _ThreadPool
    from queue import Queue

    POOL_TYPE = "simplepool"


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


class WorkerPool(_Pool):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.kill(block=False)


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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.kill()

    def __bool__(self):
        return True


common_threadpool = ThreadPool()
