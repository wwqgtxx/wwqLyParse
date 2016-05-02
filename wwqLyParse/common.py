#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
import urllib.request,io,os,sys,json,re,gzip

class Parser(object):
    filters = []
    def Parse(self,url):
        pass
    def ParseURL(self,url,label,min=None,max=None):
        pass
    def getfilters(self):
        return self.filters
    # def getUrl(self,url):
        # req = urllib.request.Request(url)
        # f = urllib.request.urlopen(req)
        # s = f.read()
        # s = s.decode('utf-8','ignore')
        # return s
    def getUrl(self,oUrl, encoding = 'utf-8' , headers = {}, data = None, method = None) :
        # url 包含中文时 parse.quote_from_bytes(oUrl.encode('utf-8'), ':/&%?=+')
        req = urllib.request.Request( oUrl, headers= headers, data = data, method = method )
        with urllib.request.urlopen(req ) as  response:
            headers = response.info()
            cType = headers.get('Content-Type','')
            match = re.search('charset\s*=\s*(\w+)', cType)
            if match:
                encoding = match.group(1)
            blob = response.read()
            if headers.get('Content-Encoding','') == 'gzip':
                data=gzip.decompress(blob)
                html_text = data.decode(encoding,'ignore')
                return html_text
            else:
                html_text = blob.decode(encoding,'ignore')
                return html_text