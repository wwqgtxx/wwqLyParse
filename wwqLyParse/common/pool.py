#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
try:
    from gevent import GreenletExit
    from gevent.pool import Pool as _Pool
    from gevent.queue import Queue
    POOL_TYPE = "geventpool"
except:
    from .simplepool import GreenletExit
    from .simplepool import Pool as _Pool
    from queue import Queue
    POOL_TYPE = "simplepool"


def call_method_and_save_to_queue(queue, method, args, kwargs):
    try:
        queue.put(method(*args, **kwargs))
    except GreenletExit:
        pass


class Pool(_Pool):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.kill(block=False)
