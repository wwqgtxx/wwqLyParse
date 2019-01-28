#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
from __future__ import absolute_import, division, print_function, \
    with_statement

__all__ = ["KeyLockDict", "AsyncKeyLockDict",
           "KeyLockWrapper", "AsyncKeyLockWrapper",
           "FUCK_KEY_LOCK", "ASYNC_FUCK_KEY_LOCK"]


class KeyLockDict(dict):
    @staticmethod
    def _get_new_lock():
        import threading
        return threading.RLock()

    def __missing__(self, key):
        self[key] = value = KeyLockWrapper(key, self, self._get_new_lock)
        return value


class AsyncKeyLockDict(dict):
    @staticmethod
    def _get_new_lock():
        from . import asyncio
        return asyncio.Lock()

    def __missing__(self, key):
        self[key] = value = AsyncKeyLockWrapper(key, self, self._get_new_lock)
        return value


class KeyLockWrapper(object):
    def __init__(self, _key, _dict, _get_new_lock):
        self._key = _key
        self._dict = _dict
        self._lock = _get_new_lock()
        self._inner_lock = _get_new_lock()
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


class AsyncKeyLockWrapper(object):
    def __init__(self, _key, _dict, _get_new_lock):
        self._key = _key
        self._dict = _dict
        self._lock = _get_new_lock()
        self._inner_lock = _get_new_lock()
        self._count = 0

    async def __aenter__(self):
        async with self._inner_lock:
            self._count += 1
        await self._lock.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        async with self._inner_lock:
            self._count -= 1
            if self._count == 0:
                del self._dict[self._key]
        await self._lock.__aexit__(exc_type, exc_val, exc_tb)


class KeyLockFuck(KeyLockWrapper):
    def __init__(self, *k, **kk):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class AsyncKeyLockFuck(AsyncKeyLockWrapper):
    def __init__(self, *k, **kk):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


FUCK_KEY_LOCK = KeyLockFuck()
ASYNC_FUCK_KEY_LOCK = AsyncKeyLockFuck()
