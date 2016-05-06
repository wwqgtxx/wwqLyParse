#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib.request,io,os,sys,json,re

from pyquery.pyquery import PyQuery

try:
    from .. import common
except Exception as e:
    import common


class MgTVParser(common.Parser):

    filters = ['http://www.mgtv.com/v/']
        
   
    def Parse(self,input_text,types=None):
        if (types is None) or ("formats" in types):
            data = {
                "type" : "formats",
                "name" : "",   
                #"icon" : "http://xxx.cn/xxx.jpg",
                #"provider" : "芒果TV",
                "caption" : "标题",
                #"warning" : "提示信息",
                "sorted" : 1,
                "data" : []
            }
            id = re.match('^http://[^\s]+/[^\s]+/([^\s]+)\.html',input_text).group(1)
            ejson_url = 'http://v.api.mgtv.com/player/video?retry=1&video_id=' + id
            ejson = common.getUrl(ejson_url)
            #print(ejson)
            ejson = json.loads(ejson)
            if ejson["status"] != 200:
                return
            edata = ejson["data"]
            estream = edata["stream"]
            estream_domain = edata["stream_domain"]
            for i in range(0, len(estream)):
                info = { 
                    "label" : i,   
                    "code" : i,
                    #"ext" : "",   
                    #"size" : "",
                    #"type" : "",
                }
                data["data"].append(info)
            return data

    def ParseURL(self,input_text,label,min=None,max=None):
        data = {
            "protocol" : "http", 
            "urls" : [""],
            #"args" : {},
            #"duration" : 1111,
            #"length" : 222222,
            #"decrypt" : "KanKan",
            #"decryptData" : {},
            #"adjust" : "KanKan", 
            #"adjustData" : { },
            #"segmentSize": 1024,
            #"maxDown" : 5,
            #"convert" : "",
            #"convertData" : "",
        }
        id = re.match('^http://[^\s]+/[^\s]+/([^\s]+)\.html',input_text).group(1)
        ejson_url = 'http://v.api.mgtv.com/player/video?retry=1&video_id=' + id
        ejson = common.getUrl(ejson_url)
        ejson = json.loads(ejson)
        if ejson["status"] != 200:
            return
        edata = ejson["data"]
        estream = edata["stream"]
        estream_domain = edata["stream_domain"]
        i = int(label)
        stream = estream[i]
        stream_domain = estream_domain[i]
        host = str(stream_domain)
        url = str(stream["url"])
        aurl = url.split('?')
        a = aurl[0].strip('/playlist.m3u8')
        b = aurl[1].split('&')
        u = host+'/'+a+'?pno=1031&'+b[3]+'&'+b[4]
        op1 = common.getUrl(u)
        data1 = json.loads(op1)
        eurl = data1['info']
        data["urls"] = eurl
        info = { 
            "label" : i,   
            "code" : i,
            #"ext" : "",   
            #"size" : "",
            #"type" : "",
        }
        return [data]
    