# Copyright 2009 Brian Quinlan. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Execute computations asynchronously using threads or processes."""

__author__ = 'Brian Quinlan (brian@sweetapp.com)'

from ._base import (FIRST_COMPLETED,
                    FIRST_EXCEPTION,
                    ALL_COMPLETED,
                    CancelledError,
                    TimeoutError,
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
        from .thread import ThreadPoolExecutor as te
        ThreadPoolExecutor = te
        return te

    raise AttributeError("module {} has no attribute {}".format(__name__, name))


import sys

if sys.version_info[0:2] < (3, 7):
    from .process import ProcessPoolExecutor
    from .thread import ThreadPoolExecutor
