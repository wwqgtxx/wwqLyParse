#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
from __future__ import absolute_import, division, print_function, \
    with_statement

import collections
import threading
import time

___all___ = ["LRUCache", "LRUCacheType"]


class NullLock(object):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return


class LRUCache(collections.MutableMapping):
    def __init__(self, size=5, timeout=60, delete_handle=None, after_delete_handle=None, use_lock=True,
                 use_default_dict=False, default_factory=None, *args,
                 **kwargs):
        self.size = size
        self.timeout = timeout
        self._store = collections.defaultdict(
            default_factory) if use_default_dict or default_factory is not None else dict()
        self._keys_to_last_time = collections.OrderedDict()
        self._lock = threading.RLock() if use_lock else NullLock()
        self.delete_handle = delete_handle
        self.after_delete_handle = after_delete_handle
        self.update(dict(*args, **kwargs))

    def flush(self, key, not_sweep=False):
        with self._lock:
            t = time.time()
            self._keys_to_last_time[key] = t
            self._keys_to_last_time.move_to_end(key, False)  # move to start
            if not not_sweep:
                self.sweep()

    def __getitem__(self, key):
        with self._lock:
            self.flush(key)
            return self._store[key]

    def __setitem__(self, key, value):
        with self._lock:
            self.flush(key)
            self._store[key] = value

    def __delitem__(self, key):
        with self._lock:
            self._delete(key, call_handle=False)

    def __iter__(self):
        with self._lock:
            return iter(self._store.copy())

    def __len__(self):
        with self._lock:
            return len(self._store)

    def __contains__(self, item):
        with self._lock:
            return item in self._store

    def __str__(self):
        with self._lock:
            return str(self._store)

    def __repr__(self):
        with self._lock:
            return repr(self._store)

    def items(self):
        with self._lock:
            return self._store.items()

    def values(self):
        with self._lock:
            return self._store.values()

    def keys(self):
        with self._lock:
            return self._store.keys()

    def sweep(self):
        with self._lock:
            len_store = len(self._store)
            if len_store == 0:
                return
            now = time.time()
            sorted_dict_items = collections.deque(self._keys_to_last_time.items())
            # sorted_dict_items = sorted(self._keys_to_last_time.items(), key=lambda i: i[1], reverse=True)
            if len_store > self.size:
                for _ in range(len_store - self.size):
                    i = sorted_dict_items.pop()
                    if i is None:
                        break
                    k, v = i
                    if self._delete(k) is False:
                        return

            while len(sorted_dict_items) > 0 and now - sorted_dict_items[-1][1] > self.timeout:
                i = sorted_dict_items.pop()
                k, v = i
                if self._delete(k) is False:
                    return

    def _delete(self, key, call_handle=True):
        if call_handle and self.delete_handle:
            value = self._store[key]
            if self.delete_handle((key, value)) is False:
                self.flush(key)
                return False
            self._delete(key, call_handle=False)
            self.after_delete_handle((key, value))
        else:
            del self._store[key]
            del self._keys_to_last_time[key]


import typing

LRUCacheType = typing.MutableMapping

if __name__ == '__main__':
    l = LRUCache(5, 10)
    l["a"] = 5
    time.sleep(0.1)
    l["b"] = 6
    time.sleep(0.1)
    l["c"] = 7
    time.sleep(0.1)
    l["d"] = 8
    time.sleep(0.1)
    l["e"] = 9
    time.sleep(0.1)
    l["f"] = 10
    time.sleep(0.1)
    l["g"] = 11
    if "a" not in l:
        print("successful")
    else:
        print("error")
    time.sleep(7)
    if "f" in l:
        print("successful")
    else:
        print("error")
    time.sleep(7)
    if "f" in l:
        print("successful")
    else:
        print("error")
    if "g" not in l:
        print("successful")
    else:
        print("error")
    print(list(l.items()))
