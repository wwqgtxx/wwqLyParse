#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib.request, io, os, sys, json, re, logging

from pyquery.pyquery import PyQuery

try:
    from ..common import *
except Exception as e:
    from common import *

__all__ = ["BaiduVLinkUrlHandle", "BaiduWWWLinkUrlHandle", "LetvUrlHandle", "HunantvUrlHandle", "MgtvUrlHandle", "IqiyiMUrlHandle"]


class BaiduVLinkUrlHandle(UrlHandle):
    filters = ['^(http|https)://v.baidu.com/link']
    order = 1

    def url_handle(self, input_text):
        html = get_url(input_text)
        html = PyQuery(html)
        a = html.children('a')
        a = PyQuery(a)
        url = a.attr("href")
        return url


class BaiduWWWLinkUrlHandle(UrlHandle):
    filters = ['^(http|https)://www.baidu.com/link']
    order = 1

    def url_handle(self, input_text):
        html = get_url(input_text)
        url = match1(html, r'setTimeout\(function\(\){window.location.replace\("(.*)"\)},timeout\)')
        if url:
            return url
        return input_text


class LetvUrlHandle(UrlHandle):
    filters = ['^(http|https)://www.letv.com']
    order = 2

    def url_handle(self, input_text):
        url = input_text.replace("letv.com", "le.com")
        return url


class HunantvUrlHandle(UrlHandle):
    filters = ['^(http|https)://www.hunantv.com']
    order = 2

    def url_handle(self, input_text):
        url = input_text.replace("hunantv.com", "mgtv.com")
        return url


class MgtvUrlHandle(UrlHandle):
    filters = ['^http://www.mgtv.com']
    order = 2

    def url_handle(self, input_text):
        url = input_text.replace("http://", "https://")
        return url


class IqiyiMUrlHandle(UrlHandle):
    filters = ['^(http|https)://m.iqiyi.com']
    order = 2

    def url_handle(self, input_text):
        url = input_text.replace("m.iqiyi.com", "www.iqiyi.com")
        return url
