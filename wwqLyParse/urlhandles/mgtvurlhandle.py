#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib.request,io,os,sys,json,re,logging

from pyquery.pyquery import PyQuery

try:
    from ..common import *
except Exception as e:
    from common import *

__MODULE_CLASS_NAMES__ = ["MgtvUrlHandle"]
    
class MgtvUrlHandle(UrlHandle):
    filters = ['^(http|https)://www.hunantv.com']

    def urlHandle(self,input_text):
        url = input_text.replace("hunantv.com","mgtv.com")
        logging.debug('urlHandle:"'+input_text+'"-->"'+url+'"')
        return url
