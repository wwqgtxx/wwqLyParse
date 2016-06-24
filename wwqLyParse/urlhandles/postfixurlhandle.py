#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib.request,io,os,sys,json,re,threading,queue

from pyquery.pyquery import PyQuery

try:
    from ..common import *
except Exception as e:
    from common import *


class PostfixUrlHandle(UrlHandle):

    filters = ['^(http|https)://[^\s]+/[^\s]+\.[s]{0,1}html(\?|#)[^\s]+']
        
    def urlHandle(self,url):
        def getUrl(queue,url):
            queue.put(getUrl(url))
        result =  re.match('^(http|https)://[^\s]+/[^\s]+\.[s]{0,1}html',url).group()
        q_results = queue.Queue()
        htmls = []
        t1 = threading.Thread(target=getUrl, args=(q_results, url))
        t2 = threading.Thread(target=getUrl, args=(q_results, result))
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        while not q_results.empty():
            htmls.append(q_results.get())
        if htmls[0] == htmls[1]:
            print('urlHandle:"'+url+'"-->"'+result+'"')
            return result
        return url
    