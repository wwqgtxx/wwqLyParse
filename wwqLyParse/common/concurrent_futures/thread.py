#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>

import sys
import atexit
import queue
import collections
import functools
import itertools
import weakref
import threading
import logging
from queue import Queue, Empty
import time
from .base import *

LOGGER = logging.getLogger("concurrent.futures")

_threads_queues = weakref.WeakKeyDictionary()
_shutdown = False


def _python_exit():
    global _shutdown
    _shutdown = True
    items = list(_threads_queues.items())
    for t, q in items:
        q.put(None)
    for t, q in items:
        t.join()


atexit.register(_python_exit)


class _WorkItem(object):
    def __init__(self, future, fn, args, kwargs):
        self.future = future
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        if not self.future.set_running_or_notify_cancel():
            return

        try:
            result = self.fn(*self.args, **self.kwargs)
        except BaseException as exc:
            self.future.set_exception(exc)
            # Break a reference cycle with the exception 'exc'
            self = None
        else:
            self.future.set_result(result)


def _worker(executor_reference, work_queue: Queue, initializer, initargs, timeout):
    if initializer is not None:
        try:
            initializer(*initargs)
        except BaseException:
            LOGGER.critical('Exception in initializer:', exc_info=True)
            executor = executor_reference()
            if executor is not None:
                executor._initializer_failed()
            return
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


class BrokenThreadPool(BrokenExecutor):
    """
    Raised when a worker thread in a ThreadPoolExecutor failed initializing.
    """


class ThreadPoolExecutor(Executor):
    _counter_dict = collections.defaultdict(lambda: itertools.count().__next__)

    def __init__(self, max_workers=None, thread_name_prefix='',
                 initializer=None, initargs=(), thread_dead_timeout=5 * 60, class_name=None):
        if initializer is not None and not callable(initializer):
            raise TypeError("initializer must be a callable")
        self._class_name = class_name or self.__class__.__name__
        self._max_workers = max_workers
        if sys.version_info[0:2] < (3, 7):
            self._work_queue = queue.Queue()
        else:
            self._work_queue = queue.SimpleQueue()
        self._threads = set()
        self._broken = False
        self._shutdown = False
        self._shutdown_lock = threading.Lock()
        self._thread_name_prefix = (thread_name_prefix or
                                    ("%s-%d" % (self._class_name, self._counter_dict[self._class_name]())))
        self._initializer = initializer
        self._initargs = initargs
        self._thread_dead_timeout = thread_dead_timeout
        self._thread_name_counter = itertools.count().__next__

    def submit(self, fn, *args, **kwargs):
        with self._shutdown_lock:
            if self._broken:
                raise BrokenThreadPool(self._broken)

            if self._shutdown:
                raise RuntimeError('cannot schedule new futures after shutdown')
            if _shutdown:
                raise RuntimeError('cannot schedule new futures after'
                                   'interpreter shutdown')

            f = Future()
            w = _WorkItem(f, fn, args, kwargs)

            self._work_queue.put(w)
            self._adjust_thread_count()
            return f

    submit.__doc__ = Executor.submit.__doc__

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
                                           self._work_queue,
                                           self._initializer,
                                           self._initargs,
                                           self._thread_dead_timeout))
                t.daemon = True
                t.start()
                self._threads.add(t)
                _threads_queues[t] = self._work_queue

    def _initializer_failed(self):
        with self._shutdown_lock:
            self._broken = ('A thread initializer failed, the thread pool '
                            'is not usable anymore')
            # Drain work queue and mark pending futures failed
            while True:
                try:
                    work_item = self._work_queue.get_nowait()
                except queue.Empty:
                    break
                if work_item is not None:
                    work_item.future.set_exception(BrokenThreadPool(self._broken))

    def shutdown(self, wait=True):
        with self._shutdown_lock:
            self._shutdown = True
            self._work_queue.put(None)
        if wait:
            for t in self._threads:
                t.join()

    shutdown.__doc__ = Executor.shutdown.__doc__


__all__ = ["ThreadPoolExecutor"]
