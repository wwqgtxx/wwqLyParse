#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib.request,io,os,sys,json,re

from pyquery.pyquery import PyQuery

try:
    from .. import common
except Exception as e:
    import common


class JumpUrlHandle(common.UrlHandle):

    filters = ['^(http|https)://v.baidu.com/link']
        
    def urlHandle(self,url):
        if re.match('^(http|https)://v.baidu.com/link',url):
            result = self.urlHandle_v_baidu_com_link(url)
            print('urlHandle:"'+url+'"-->"'+result+'"')
            return result

    def urlHandle_v_baidu_com_link(self,input_text):
        html = PyQuery(common.getUrl(input_text))
        a = html.children('a')
        a = PyQuery(a)
        url = a.attr("href")
        return url
    