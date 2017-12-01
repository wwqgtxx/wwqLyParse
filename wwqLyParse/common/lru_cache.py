#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
from __future__ import absolute_import, division, print_function, \
    with_statement

import collections
import threading
import time


class LRUCache(collections.MutableMapping):
    def __init__(self, size=5, timeout=60, *args, **kwargs):
        self.size = size
        self.timeout = timeout
        self._store = {}
        self._keys_to_last_time = collections.OrderedDict()
        self._lock = threading.RLock()
        self.update(dict(*args, **kwargs))

    def __getitem__(self, key):
        with self._lock:
            self.sweep()
            t = time.time()
            item = self._store[key]
            self._keys_to_last_time[key] = t
            self._keys_to_last_time.move_to_end(key, False)  # move to start
            return item

    def __setitem__(self, key, value):
        with self._lock:
            self.sweep()
            t = time.time()
            self._store[key] = value
            self._keys_to_last_time[key] = t
            self._keys_to_last_time.move_to_end(key, False)  # move to start

    def __delitem__(self, key):
        with self._lock:
            del self._store[key]
            del self._keys_to_last_time[key]

    def __iter__(self):
        with self._lock:
            return iter(self._store.copy())

    def __len__(self):
        with self._lock:
            return len(self._store)

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
                    del self._store[k]
                    del self._keys_to_last_time[k]

            while len(sorted_dict_items) > 0 and now - sorted_dict_items[-1][1] > self.timeout:
                k, v = sorted_dict_items.pop()
                del self._store[k]
                del self._keys_to_last_time[k]


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
