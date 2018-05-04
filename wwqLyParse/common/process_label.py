#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
from .get_size import byte2size


def make_label(_format, _id, quality, size=0):
    quality = quality.replace(' ', '')
    size_str = byte2size(size, False)
    size = byte2size(size, True)
    _format = str(_format).replace("_", "!")
    l = '_'.join([str(_id), _format, quality, size_str])
    return l, _format, size


def parse_label(raw):
    if '_' in raw:
        parts = raw.split('_')
        _format = parts[1]
        _format = str(_format).replace("!", "_")
        return _format
    raw = str(raw).replace("!", "_")
    return raw
