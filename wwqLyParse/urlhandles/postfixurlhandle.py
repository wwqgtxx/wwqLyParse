#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib.request, io, os, sys, json, re, threading, queue, logging

try:
    from ..common import *
except Exception as e:
    from common import *

__MODULE_CLASS_NAMES__ = ["PostfixUrlHandle"]


class PostfixUrlHandle(UrlHandle):
    filters = ['^(http|https)://[^\s]+/[^\s]+\.[s]{0,1}html(\?|#)[^\s]+']

    def urlHandle(self, url):
        def _getUrl(queue, url):
            queue.put(getUrl(url))

        if (re.match('http://v.qq.com/cover/y/[^\s]+\.html\?vid=[^\s]+', url)):
            return url
        result = re.match('^(http|https)://[^\s]+/[^\s]+\.[s]{0,1}html', url).group()
        q_results = queue.Queue()
        htmls = []
        t1 = threading.Thread(target=_getUrl, args=(q_results, url))
        t2 = threading.Thread(target=_getUrl, args=(q_results, result))
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        while not q_results.empty():
            htmls.append(q_results.get())
        if htmls[0] == htmls[1]:
            logging.debug('urlHandle:"' + url + '"-->"' + result + '"')
            return result
        return url
