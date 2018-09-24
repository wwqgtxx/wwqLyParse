#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


def green_class(class_name, target, raw):
    setattr(target, class_name,
            type(class_name,
                 (getattr(target, class_name), getattr(raw, class_name, object)),
                 {})
            )


def green_base():
    import concurrent.futures
    from . import _base
    _base.FIRST_COMPLETED = concurrent.futures.FIRST_COMPLETED
    _base.FIRST_EXCEPTION = concurrent.futures.FIRST_EXCEPTION
    _base.ALL_COMPLETED = concurrent.futures.ALL_COMPLETED
    green_class("CancelledError", _base, concurrent.futures)
    green_class("TimeoutError", _base, concurrent.futures)
    green_class("InvalidStateError", _base, concurrent.futures)
    green_class("BrokenExecutor", _base, concurrent.futures)
    green_class("Future", _base, concurrent.futures)
    green_class("Executor", _base, concurrent.futures)


def green_thread():
    import concurrent.futures
    from . import thread
    green_class("ThreadPoolExecutor", thread, concurrent.futures)


green_base()

from ._base import (FIRST_COMPLETED,
                    FIRST_EXCEPTION,
                    ALL_COMPLETED,
                    CancelledError,
                    TimeoutError,
                    InvalidStateError,
                    BrokenExecutor,
                    Future,
                    Executor,
                    wait,
                    as_completed)

__all__ = (
    'FIRST_COMPLETED',
    'FIRST_EXCEPTION',
    'ALL_COMPLETED',
    'CancelledError',
    'TimeoutError',
    'BrokenExecutor',
    'Future',
    'Executor',
    'wait',
    'as_completed',
    'ProcessPoolExecutor',
    'ThreadPoolExecutor',
)


def __dir__():
    return __all__ + ('__author__', '__doc__')


def __getattr__(name):
    global ProcessPoolExecutor, ThreadPoolExecutor

    if name == 'ProcessPoolExecutor':
        from .process import ProcessPoolExecutor as pe
        ProcessPoolExecutor = pe
        return pe

    if name == 'ThreadPoolExecutor':
        green_thread()
        from .thread import ThreadPoolExecutor as te
        ThreadPoolExecutor = te
        return te

    raise AttributeError("module {} has no attribute {}".format(__name__, name))


import sys

if sys.version_info[0:2] < (3, 7):
    green_thread()
    from .process import ProcessPoolExecutor
    from .thread import ThreadPoolExecutor
