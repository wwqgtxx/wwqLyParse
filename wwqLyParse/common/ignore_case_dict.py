#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>

import collections


class IgnoreCaseDict(collections.MutableMapping):
    def __init__(self, raw_dict: collections.MutableMapping):
        self.raw_dict = raw_dict

    def _return_item(self, item):
        if isinstance(item, collections.MutableMapping):
            return self.__class__(item)
        elif isinstance(item, collections.MutableSequence):
            return [self._return_item(i) for i in item]
        return item

    def __setitem__(self, k, v):
        k_l = str(k).lower()
        for _k in self.raw_dict.keys():
            _k_l = str(_k).lower()
            if _k_l == k_l:
                self.raw_dict[_k] = v
                return
        self.raw_dict[k] = v

    def __delitem__(self, k):
        k_l = str(k).lower()
        for _k in self.raw_dict.keys():
            _k_l = str(_k).lower()
            if _k_l == k_l:
                del self.raw_dict[_k]
                return
        raise KeyError(k)

    def __getitem__(self, k):
        k_l = str(k).lower()
        for _k in self.raw_dict.keys():
            _k_l = str(_k).lower()
            if _k_l == k_l:
                return self._return_item(self.raw_dict[_k])
        raise KeyError(k)

    def __len__(self):
        return len(self.raw_dict)

    def __iter__(self):
        return iter(self.raw_dict)

    def __repr__(self):
        return repr(self.raw_dict)

    def __str__(self):
        return str(self.raw_dict)
