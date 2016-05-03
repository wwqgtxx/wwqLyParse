#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
import urllib.request,io,os,sys,json,re,gzip

urlcache = {}
def getUrl(oUrl, encoding = 'utf-8' , headers = {}, data = None, method = None) :
    url_json = {"oUrl":oUrl,"encoding":encoding,"headers":headers,"data":data,"method":method}
    url_json = json.dumps(url_json,sort_keys=True, ensure_ascii=False)
    if url_json in urlcache:
        html_text = urlcache[url_json]
        print("cache get:"+url_json)
        return html_text
    print("normal get:"+url_json)
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
        else:
            html_text = blob.decode(encoding,'ignore')
        urlcache[url_json] = html_text
        return html_text

class Parser(object):
    filters = []
    def Parse(self,url,types=None):
        pass
    def ParseURL(self,url,label,min=None,max=None):
        pass
    def getfilters(self):
        return self.filters
    def getUrl(self,oUrl, encoding = 'utf-8' , headers = {}, data = None, method = None) :
        return getUrl(oUrl, encoding , headers, data, method)