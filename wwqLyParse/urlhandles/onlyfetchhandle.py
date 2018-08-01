#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib.request, io, os, sys, json, re, threading, queue, logging

try:
    from ..common import *
except Exception as e:
    from common import *

__all__ = ["OnlyFetchUrlHandle"]


class OnlyFetchUrlHandle(UrlHandle):
    filters = ['^(http|https)://']
    order = sys.maxsize

    def url_handle(self, url):
        get_url(url)
        return url
