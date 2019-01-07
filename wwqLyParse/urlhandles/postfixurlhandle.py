#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib.request, io, os, sys, json, re, threading, queue, logging

try:
    from ..common import *
except Exception as e:
    from common import *

__all__ = ["PostfixUrlHandle"]


class PostfixUrlHandle(UrlHandle):
    filters = ['^(http|https)://[^\s]+/[^\s]+\.[s]{0,1}html(\?|#)[^\s]+']

    async def url_handle(self, url):
        if re.match('http://v.qq.com/cover/y/[^\s]+\.html\?vid=[^\s]+', url):
            return url
        result = re.match('^(http|https)://[^\s]+/[^\s]+\.[s]{0,1}html', url).group()
        async with AsyncPool() as pool:
            task1 = pool.spawn(get_url_service.get_url_async(url, callmethod=get_caller_info(0)))
            task2 = pool.spawn(get_url_service.get_url_async(result, callmethod=get_caller_info(0)))
            html1 = await task1
            html2 = await task2
            if str(html1).strip() == str(html2).strip():
                return result
            return url
