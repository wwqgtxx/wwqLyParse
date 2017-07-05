#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
from __future__ import absolute_import, division, print_function, \
    with_statement

import collections
import time


class LRUCache(collections.MutableMapping):
    def __init__(self, size=5, timeout=60, *args, **kwargs):
        self.size = size
        self.timeout = timeout
        self._store = {}
        self._keys_to_last_time = {}
        self.update(dict(*args, **kwargs))

    def __getitem__(self, key):
        self.sweep()
        t = time.time()
        item = self._store[key]
        self._keys_to_last_time[key] = t
        return item

    def __setitem__(self, key, value):
        self.sweep()
        t = time.time()
        self._keys_to_last_time[key] = t
        self._store[key] = value

    def __delitem__(self, key):
        del self._store[key]
        del self._keys_to_last_time[key]

    def __iter__(self):
        return iter(self._store)

    def __len__(self):
        return len(self._store)

    def sweep(self):
        len_store = len(self._store)
        if len_store == 0:
            return
        now = time.time()
        sorted_dict_items = sorted(self._keys_to_last_time.items(), key=lambda i: i[1], reverse=True)
        delete_num = 0
        if len_store > self.size or now - sorted_dict_items[-1][1] > self.timeout:
            for k, v in sorted_dict_items[self.size:]:
                del self._store[k]
                del self._keys_to_last_time[k]
                delete_num += 1

            while delete_num < len_store and now - sorted_dict_items[delete_num][1] > self.timeout:
                k, v = sorted_dict_items[delete_num]
                del self._store[k]
                del self._keys_to_last_time[k]
                delete_num += 1


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
    time.sleep(15)
    if "g" not in l:
        print("successful")
    else:
        print("error")
