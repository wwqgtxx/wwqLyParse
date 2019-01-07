#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
GEVENT_POOL = "geventpool"
SIMPLE_POOL = "simplepool"
try:
    from . import geventpool as _pool

    POOL_TYPE = GEVENT_POOL
except:
    from . import simplepool as _pool

    POOL_TYPE = SIMPLE_POOL

GreenletExit = _pool.GreenletExit

Queue = _pool.queue.Queue
Empty = _pool.queue.Empty
Full = _pool.queue.Full

try:
    SimpleQueue = _pool.queue.SimpleQueue
except:
    # copy from python3.7's queue.py
    class _PySimpleQueue:
        '''Simple, unbounded FIFO queue.

        This pure Python implementation is not reentrant.
        '''

        # Note: while this pure Python version provides fairness
        # (by using a threading.Semaphore which is itself fair, being based
        #  on threading.Condition), fairness is not part of the API contract.
        # This allows the C version to use a different implementation.

        def __init__(self):
            import collections
            import threading
            self._queue = collections.deque()
            self._count = threading.Semaphore(0)

        def put(self, item, block=True, timeout=None):
            '''Put the item on the queue.

            The optional 'block' and 'timeout' arguments are ignored, as this method
            never blocks.  They are provided for compatibility with the Queue class.
            '''
            self._queue.append(item)
            self._count.release()

        def get(self, block=True, timeout=None):
            '''Remove and return an item from the queue.

            If optional args 'block' is true and 'timeout' is None (the default),
            block if necessary until an item is available. If 'timeout' is
            a non-negative number, it blocks at most 'timeout' seconds and raises
            the Empty exception if no item was available within that time.
            Otherwise ('block' is false), return an item if one is immediately
            available, else raise the Empty exception ('timeout' is ignored
            in that case).
            '''
            if timeout is not None and timeout < 0:
                raise ValueError("'timeout' must be a non-negative number")
            if not self._count.acquire(block, timeout):
                raise Empty
            return self._queue.popleft()

        def put_nowait(self, item):
            '''Put an item into the queue without blocking.

            This is exactly equivalent to `put(item)` and is only provided
            for compatibility with the Queue class.
            '''
            return self.put(item, block=False)

        def get_nowait(self):
            '''Remove and return an item from the queue without blocking.

            Only get an item if one is immediately available. Otherwise
            raise the Empty exception.
            '''
            return self.get(block=False)

        def empty(self):
            '''Return True if the queue is empty, False otherwise (not reliable!).'''
            return len(self._queue) == 0

        def qsize(self):
            '''Return the approximate size of the queue (not reliable!).'''
            return len(self._queue)


    SimpleQueue = _PySimpleQueue


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


class WorkerPool(_pool.Pool):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.kill(block=False)

    @staticmethod
    def wait(wait_list, timeout=None):
        return _pool.wait(wait_list, timeout=timeout)


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


class RealThreadPool(_pool.ThreadPool):
    def apply(self, func, args=None, kwds=None):
        result = super(RealThreadPool, self).apply(_apply, args=(func, args, kwds))
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


_common_real_thread_pool = None


def get_common_real_thread_pool():
    global _common_real_thread_pool
    if _common_real_thread_pool is None:
        _common_real_thread_pool = RealThreadPool()
    return _common_real_thread_pool

def new_raw_async_loop():
    import asyncio
    from .concurrent_futures import ThreadPoolExecutor
    from .selectors import DefaultSelector
    import logging

    if POOL_TYPE == GEVENT_POOL:
        loop = asyncio.SelectorEventLoop(DefaultSelector())
    else:
        loop = asyncio.ProactorEventLoop()
    executor = ThreadPoolExecutor()
    import concurrent.futures
    assert isinstance(executor, concurrent.futures.ThreadPoolExecutor)
    loop.set_default_executor(executor)
    logging.debug("set %s for %s" % (executor, loop))
    return loop
