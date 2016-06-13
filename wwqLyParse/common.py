#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
import urllib.request,io,os,sys,json,re,gzip,time

urlcache = {}
def getUrl(oUrl, encoding = 'utf-8' , headers = {}, data = None, method = None) :
    url_json = {"oUrl":oUrl,"encoding":encoding,"headers":headers,"data":data,"method":method}
    url_json = json.dumps(url_json,sort_keys=True, ensure_ascii=False)
    if url_json in urlcache:
        item = urlcache[url_json]
        html_text = item["html_text"]
        item["lasttimestap"] = int(time.time())
        print("cache get:"+url_json)
        if (len(urlcache)>100):
            cleanUrlcache()
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
        urlcache[url_json] = {"html_text":html_text,"lasttimestap":int(time.time())}
        return html_text

def cleanUrlcache():
    sortedDict = sorted(urlcache.items(), key=lambda d: d[1]["lasttimestap"], reverse=True)
    newDict = sortedDict[:100] # 从数组中取索引start开始到end-1的记录
    urlcache = newDict
    print("urlcache has been cleaned")
        
def debug(input):
    print (((str(input))).encode('gbk', 'ignore').decode('gbk') )
        
class Parser(object):
    filters = []
    def Parse(self,url,types=None):
        pass
    def ParseURL(self,url,label,min=None,max=None):
        pass
    def getfilters(self):
        return self.filters
        
class UrlHandle():
    filters = []
    def urlHandle(url):
        pass
    def getfilters(self):
        return self.filters