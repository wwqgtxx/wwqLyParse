#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>

from concurrent.futures import (FIRST_COMPLETED,
                                FIRST_EXCEPTION,
                                ALL_COMPLETED,
                                CancelledError,
                                TimeoutError,
                                Future,
                                Executor,
                                wait,
                                as_completed)

try:
    from concurrent.futures import BrokenExecutor
except:
    class BrokenExecutor(RuntimeError):
        """
        Raised when a executor has become non-functional after a severe failure.
        """