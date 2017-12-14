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

    def url_handle(self, url):
        def _getUrl(queue, url):
            queue.put(get_url(url))

        if (re.match('http://v.qq.com/cover/y/[^\s]+\.html\?vid=[^\s]+', url)):
            return url
        result = re.match('^(http|https)://[^\s]+/[^\s]+\.[s]{0,1}html', url).group()
        q_results = queue.Queue()
        htmls = []
        with Pool() as pool:
            pool.spawn(call_method_and_save_to_queue, queue=q_results, method=get_url, args=(url,))
            pool.spawn(call_method_and_save_to_queue, queue=q_results, method=get_url, args=(result,))
            pool.join()
        while not q_results.empty():
            htmls.append(q_results.get())
        if str(htmls[0]).strip() == str(htmls[1]).strip():
            logging.debug('urlHandle:"' + url + '"-->"' + result + '"')
            return result
        return url
