#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib.request,io,os,sys,json,re,threading

from pyquery.pyquery import PyQuery

try:
    from ..common import *
except Exception as e:
    from common import *
    


class AnyPageParser(Parser):

    filters = ['^(http|https)://.+']
    
    
    TWICE_PARSE = True    
    TWICE_PARSE_TIMEOUT = 30
        
    def Parse(self,input_text,types=None):
        global TWICE_PARSE_TIMEOUT
        if (types is not None) and ("collection" not in types):
            return
        if (re.search('www.iqiyi.com/(lib/m|a_|v_)',input_text)):
            return
        html = PyQuery(getUrl(input_text))
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
            if re.search('[^\?](list|mall|about|help|shop|map|vip|faq|support|download|copyright|contract|product|tencent|upload|common|index.html|v.qq.com/u/|open.baidu.com|www.iqiyi.com/lib/s_|www.iqiyi.com/dv/|top.iqiyi.com)',url):
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

                    
            if re.search('(www.iqiyi.com/a_)|(www.le.com/comic)',url):
                unsure = True
                
            info = {
                "name": name,
                "no": no,
                "subtitle": subtitle,
                "url": url,
                "unsure": unsure           
            }
            data["data"].append(info)
        if self.TWICE_PARSE:
            try:
                from . import listparser
            except Exception as e:
                import listparser
            try:
                from .. import main
            except Exception as e:
                import main
            #run.Parse(input_text,types=None,parsers = parsers,urlhandles = urlhandles)
            def runlist_parser(queue,parser,url):
                url2 = urlHandle(url)
                try:
                    result = parser.Parse(url2)
                    if (result is not None) and (result != []) and (result["data"] is not None) and (result["data"] != []):
                        queue.put({"result":result,"url":url})
                except Exception as e:
                    #continue
                    logging.error(e)
                    #import traceback  
                    #traceback.print_exc() 
            list_parser = listparser.ListParser(pool = Pool(20))
            urlHandle = main.urlHandle
            parser_threads = []
            parse_urls = []
            t_results = []
            q_results = Queue()
            for url in urls:
                for filter in list_parser.getfilters():
                    if re.search(filter,url):
                        parser_threads.append(main.pool.spawn(runlist_parser,q_results,list_parser,url))
            joinall(parser_threads,timeout=self.TWICE_PARSE_TIMEOUT)
            while not q_results.empty():
                t_results.append(q_results.get())
                
            oldddata = data["data"]
            data["data"] = []
            for t_result in t_results:
                parse_urls.append(t_result["url"])
                for tdata in t_result["result"]["data"]:
                    tdata["no"] = t_result["result"]["title"] +" "+ tdata["no"]
                data["data"].extend(t_result["result"]["data"])
            for ddata in oldddata:
                if ddata["url"] not in parse_urls:
                    #print(ddata["url"])
                    data["data"].append(ddata)
        oldddata = data["data"]
        data["data"] = []
        parsed_urls = []
        for ddata in oldddata:
            if ddata["url"] not in parsed_urls:
                data["data"].append(ddata)
                parsed_urls.append(ddata["url"])
        data["total"] = len(data["data"])
        data["caption"] = "全页地址列表"
        return data


