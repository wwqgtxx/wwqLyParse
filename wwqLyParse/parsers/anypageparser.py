#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib.request,io,os,sys,json,re

from pyquery.pyquery import PyQuery

try:
    from .. import common
except Exception as e:
    import common
    


class AnyPageParser(common.Parser):

    filters = ['^(http|https)\://([a-zA-Z0-9\.\-]+(\:[a-zA-Z0-9\.&amp;%\$\-]+)*@)*((25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9])\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[0-9])|localhost|([a-zA-Z0-9\-]+\.)*[a-zA-Z0-9\-]+\.(com|edu|gov|int|mil|net|org|biz|arpa|info|name|pro|aero|coop|museum|[a-zA-Z]{2,5}))(\:[0-9]+)*(/($|[a-zA-Z0-9\.\,\?\'\\\+&amp;%\$#\=~_\-]+))*$']
    
    
    TWICE_PARSE = False    
        
    def Parse(self,input_text):
        html = PyQuery(self.getUrl(input_text))
        items = html('a')
        title = html('title').text()
        data = {
            "data": [],
            "more": False,
            "title": title,
            "total": 0,
            "type": "collection"
        }
        urls = []
        for item in items:
            a = PyQuery(item)
            name = a.attr('title')
            if name is None:
                name = a.text()
            no = name
            subtitle = name
            url = a.attr('href')
            if url is None:
                continue
            if name is None or name == "":
                continue    
            if re.match('^(http|https|ftp)://.+\.(mp4|mkv|ts|avi)',url):
                url = 'direct:'+url
            if not re.match('(^(http|https)://.+\.(shtml|html|mp4|mkv|ts|avi))|(^(http|https)://.+/video/)',url):
                continue
            if re.search('(list|mall|about|help|shop|map|vip|faq|support|download|copyright|contract|product|tencent|upload|common|index.html|v.qq.com/u/|open.baidu.com|www.iqiyi.com/lib/s_|www.iqiyi.com/dv/)',url):
                continue
            if re.search('(下载|播 放|播放|投诉|评论|(\d{1,2}:\d{1,2}))',no):
                continue
            unsure = False
                        
            for temp in urls:
                if temp == str(url):
                    #print("remove:"+url)
                    url = None
                    break
            if url is None:
                continue
            
            urls.append(url)
            
            if self.TWICE_PARSE:
                try:
                    from . import listparser
                except Exception as e:
                    import listparser
                list_parser = listparser.ListParser()
                for filter in list_parser.getfilters():
                    if re.search(filter,url):
                        try:
                            print(url)
                            result = list_parser.Parse(url)
                            if (result is not None) and (result != []) and (result["data"] is not None) and (result["data"] != []):
                                data["data"].extend(result["data"])
                                url = None
                                result = None
                                break
                        except Exception as e:
                            #continue
                            print(e)
                            #import traceback  
                            #traceback.print_exc() 
                if url is None:
                    continue    


                
            info = {
                "name": name,
                "no": no,
                "subtitle": subtitle,
                "url": url,
                "unsure": unsure            
            }
            data["data"].append(info)
        data["total"] = len(data["data"])
        return data


