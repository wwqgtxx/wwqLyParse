#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>

import collections


def _return_item(item):
    if isinstance(item, collections.MutableMapping):
        return IgnoreCaseDict(item)
    elif isinstance(item, collections.MutableSequence):
        return MutableSequenceProxy(item)
    return item


class IgnoreCaseDict(collections.MutableMapping):
    def __init__(self, raw_dict: collections.MutableMapping):
        self.raw_dict = raw_dict

    def _find_key(self, k):
        if k in self.raw_dict:
            return k
        if isinstance(k, str):
            k_l = k.lower()
            if k_l in self.raw_dict:
                return k_l
            for _k in self.raw_dict.keys():
                if isinstance(_k, str):
                    _k_l = _k.lower()
                    if _k_l == k_l:
                        return _k
        return k

    def __setitem__(self, k, v):
        self.raw_dict[self._find_key(k)] = v

    def __delitem__(self, k):
        del self.raw_dict[self._find_key(k)]

    def __getitem__(self, k):
        return _return_item(self.raw_dict[self._find_key(k)])

    def __len__(self):
        return len(self.raw_dict)

    def __iter__(self):
        return iter(self.raw_dict)

    def __repr__(self):
        return repr(self.raw_dict)

    def __str__(self):
        return str(self.raw_dict)


class MutableSequenceProxy(collections.MutableSequence):
    def __init__(self, raw_seq: collections.MutableSequence):
        self.raw_seq = raw_seq

    def insert(self, index, o):
        self.raw_seq.insert(index, o)

    def __setitem__(self, i, o):
        self.raw_seq[i] = o

    def __delitem__(self, i):
        del self.raw_seq[i]

    def __getitem__(self, i):
        return _return_item(self.raw_seq[i])

    def __len__(self):
        return len(self.raw_seq)

    def __repr__(self):
        return repr(self.raw_seq)

    def __str__(self):
        return str(self.raw_seq)


__all__ = ["IgnoreCaseDict"]
