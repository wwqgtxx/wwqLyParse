#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>

try:
    import gevent.select
except:
    from select import select
else:
    def select(rlist, wlist, xlist, timeout=None):
        rlist = tuple(rlist)
        wlist = tuple(wlist)
        xlist = tuple(xlist)
        rresult = list()
        wresult = list()
        xresult = list()
        for i in range(0, len(rlist), 500):
            sel_results = gevent.select.select(rlist[i:i + 500], [], [], 0)
            rresult.extend(sel_results[0])
        for i in range(0, len(wlist), 500):
            sel_results = gevent.select.select([], wlist[i:i + 500], [], 0)
            wresult.extend(sel_results[1])
        for i in range(0, len(xlist), 500):
            sel_results = gevent.select.select([], [], xlist[i:i + 500], 0)
            xresult.extend(sel_results[2])

        if rresult or wresult or xresult or (timeout is not None and timeout == 0):
            return rresult, wresult, xresult

        result = gevent.select.SelectResult()
        return result.select(rlist, wlist, timeout)
