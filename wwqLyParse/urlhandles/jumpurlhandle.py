#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib.request, io, os, sys, json, re, logging

from pyquery.pyquery import PyQuery

try:
    from ..common import *
except Exception as e:
    from common import *

__MODULE_CLASS_NAMES__ = ["BaiduLinkUrlHandle", "LetvUrlHandle", "MgtvUrlHandle", "IqiyiMUrlHandle"]


class BaiduLinkUrlHandle(UrlHandle):
    filters = ['^(http|https)://v.baidu.com/link']

    def urlHandle(self, input_text):
        html = PyQuery(getUrl(input_text))
        a = html.children('a')
        a = PyQuery(a)
        url = a.attr("href")
        logging.debug('urlHandle:"' + input_text + '"-->"' + url + '"')
        return url


class LetvUrlHandle(UrlHandle):
    filters = ['^(http|https)://www.letv.com']

    def urlHandle(self, input_text):
        url = input_text.replace("letv.com", "le.com")
        logging.debug('urlHandle:"' + input_text + '"-->"' + url + '"')
        return url


class MgtvUrlHandle(UrlHandle):
    filters = ['^(http|https)://www.hunantv.com']

    def urlHandle(self, input_text):
        url = input_text.replace("hunantv.com", "mgtv.com")
        logging.debug('urlHandle:"' + input_text + '"-->"' + url + '"')
        return url


class IqiyiMUrlHandle(UrlHandle):
    filters = ['^(http|https)://m.iqiyi.com']

    def urlHandle(self, input_text):
        url = input_text.replace("m.iqiyi.com", "www.iqiyi.com")
        logging.debug('urlHandle:"' + input_text + '"-->"' + url + '"')
        return url
