#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


def green_base():
    import concurrent.futures
    from . import _base
    from ..green_target import green_target
    green_target([
        "FIRST_COMPLETED",
        "FIRST_COMPLETED",
        "ALL_COMPLETED",
        "CancelledError",
        "TimeoutError",
        "InvalidStateError",
        "BrokenExecutor",
        "Future",
        "Executor",
    ], _base, concurrent.futures)


def green_thread():
    import concurrent.futures
    from . import thread
    from ..green_target import green_target
    green_target("ThreadPoolExecutor", thread, concurrent.futures)


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
