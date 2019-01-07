#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>

from gevent import GreenletExit
from gevent import wait
from gevent.pool import Pool as _Pool
from gevent.threadpool import ThreadPool as _ThreadPool
import gevent.queue as queue

import threading
import itertools
import logging


class Pool(_Pool):
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
            return _fn(*args, **kwargs)

        return super(Pool, self).spawn(_spawn)


class ThreadPool(_ThreadPool):
    def __init__(self, maxsize=None, hub=None):
        if not maxsize:
            maxsize = 1000
        self.__size = 0
        super(ThreadPool, self).__init__(maxsize, hub)
        logging.debug("new GeventThreadPool %s" % self)
