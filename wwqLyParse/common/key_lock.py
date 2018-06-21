#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
from __future__ import absolute_import, division, print_function, \
    with_statement

import threading

__all__ = ["KeyLockDict", "KeyLockWrapper", "KeyLockFuck", "FUCK_KEY_LOCK"]


class KeyLockDict(dict):
    def __missing__(self, key):
        self[key] = value = KeyLockWrapper(key, self)
        return value


class KeyLockWrapper(object):
    def __init__(self, _key, _dict):
        self._key = _key
        self._dict = _dict
        self._lock = threading.Lock()
        self._inner_lock = threading.Lock()
        self._count = 0

    def __enter__(self):
        with self._inner_lock:
            self._count += 1
        self._lock.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        with self._inner_lock:
            self._count -= 1
            if self._count == 0:
                del self._dict[self._key]
        self._lock.__exit__(exc_type, exc_val, exc_tb)


class KeyLockFuck(object):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


FUCK_KEY_LOCK = KeyLockFuck()
