#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib.request,io,os,sys,json,re,logging

from pyquery.pyquery import PyQuery

try:
    from ..common import *
except Exception as e:
    from common import *


class BaiduLinkUrlHandle(UrlHandle):

    filters = ['^(http|https)://v.baidu.com/link']

    def urlHandle(self,input_text):
        html = PyQuery(getUrl(input_text))
        a = html.children('a')
        a = PyQuery(a)
        url = a.attr("href")
        logging.debug('urlHandle:"'+input_text+'"-->"'+url+'"')
        return url