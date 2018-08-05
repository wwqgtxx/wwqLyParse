#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
from . import _base

DefaultSelector = _base.DefaultSelector
EVENT_READ = _base.EVENT_READ
EVENT_WRITE = _base.EVENT_WRITE

try:
    import gevent.select
except:
    pass
else:
    import math
    from .select import select


    class GeventSelectSelector(_base.SelectSelector):
        def _select(self, r, w, _, timeout=None):
            r, w, x = select(r, w, w, timeout)
            return r, w + x, []


    DefaultSelector = GeventSelectSelector
    try:
        from .poll import *
    except:
        pass
    else:
        class GeventPollSelector(_base._PollLikeSelector):
            _selector_cls = poll
            _EVENT_READ = POLLIN
            _EVENT_WRITE = POLLOUT


        DefaultSelector = GeventPollSelector

__all__ = ["DefaultSelector", "EVENT_READ", "EVENT_WRITE"]
