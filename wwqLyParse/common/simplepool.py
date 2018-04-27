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
from .concurrent_futures import ThreadPoolExecutor as _ThreadPoolExecutor
from .concurrent_futures import wait as _wait
from .concurrent_futures.thread import _shutdown, _threads_queues


class GreenletExit(Exception):
    pass


def _worker(executor_reference, work_queue: Queue, timeout):
    try:
        while True:
            try:
                work_item = work_queue.get(block=True, timeout=timeout)
            except Empty:
                return
            if work_item is not None:
                work_item.run()
                # Delete references to object. See issue16284
                del work_item
                continue
            executor = executor_reference()
            # Exit if:
            #   - The interpreter is shutting down OR
            #   - The executor that owns the worker has been collected OR
            #   - The executor that owns the worker has been shutdown.
            if _shutdown or executor is None or executor._shutdown:
                # Notice other workers
                work_queue.put(None)
                return
            del executor
    except BaseException:
        pass


class ThreadPoolExecutor(_ThreadPoolExecutor):
    _counter = itertools.count().__next__

    def __init__(self, max_workers=None, thread_name_prefix='', thread_dead_timeout=5 * 60):
        super(ThreadPoolExecutor, self).__init__(max_workers, thread_name_prefix=thread_name_prefix)
        self._max_workers = max_workers
        self._thread_name_prefix = (thread_name_prefix or
                                    ("ThreadPool-%d" % self._counter()))
        self._thread_dead_timeout = thread_dead_timeout
        self._thread_name_counter = itertools.count().__next__

    def _adjust_thread_count(self):
        time.sleep(0.01)
        if self._work_queue.qsize():
            # When the executor gets lost, the weakref callback will wake up
            # the worker threads.
            def weakref_cb(_, q=self._work_queue):
                q.put(None)

            dead_list = list()
            for t in self._threads:
                if not t.is_alive():
                    dead_list.append(t)
            for t in dead_list:
                self._threads.remove(t)
            del dead_list

            num_threads = len(self._threads)
            if not self._max_workers or num_threads < self._max_workers:
                thread_name = '%s_%d' % (self._thread_name_prefix or self,
                                         self._thread_name_counter())
                t = threading.Thread(name=thread_name, target=_worker,
                                     args=(weakref.ref(self, weakref_cb),
                                           self._work_queue, self._thread_dead_timeout))
                t.daemon = True
                t.start()
                self._threads.add(t)
                _threads_queues[t] = self._work_queue


class Pool(object):
    def __init__(self, size=None, thread_name_prefix=''):
        self.pool_size = size
        self.ex = ThreadPoolExecutor(size, thread_name_prefix=thread_name_prefix)
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
