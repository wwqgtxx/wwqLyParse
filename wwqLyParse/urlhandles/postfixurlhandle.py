#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib.request,io,os,sys,json,re

from pyquery.pyquery import PyQuery

try:
    from .. import common
except Exception as e:
    import common


class PostfixUrlHandle(common.UrlHandle):

    filters = ['^(http|https)://[^\s]+/[^\s]+\.[s]{0,1}html(\?|#)[^\s]+']
        
    def urlHandle(self,url):
        result =  re.match('^(http|https)://[^\s]+/[^\s]+\.[s]{0,1}html',url).group()
        print('urlHandle:"'+url+'"-->"'+result+'"')
        return result

    