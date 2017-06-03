#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib.request, io, os, sys, json, re

from pyquery.pyquery import PyQuery

try:
    from ..common import *
except Exception as e:
    from common import *

JUDGE_VIP = True

__MODULE_CLASS_NAMES__ = []


class MgTVParser(Parser):
    filters = ['http://www.mgtv.com/v/']
    types = ["formats"]

    def Parse(self, input_text, types=None):
        data = {
            "type": "formats",
            "name": "",
            "icon": "http://xxx.cn/xxx.jpg",
            "provider": "芒果TV",
            "caption": "芒果TV解析",
            # "warning" : "提示信息",
            "sorted": 1,
            "data": []
        }
        id = re.match('^http://[^\s]+/[^\s]+/([^\s]+)\.html', input_text).group(1)
        ejson_url = 'http://v.api.mgtv.com/player/video?retry=1&video_id=' + id
        ejson = getUrl(ejson_url)
        # print(ejson)
        ejson = json.loads(ejson)
        if ejson["status"] != 200:
            return
        edata = ejson["data"]
        # don't parse vip
        if JUDGE_VIP and (edata["user"]["isvip"] != "0"):
            return
        einfo = edata["info"]
        estream = edata["stream"]
        estream_domain = edata["stream_domain"]
        data["name"] = einfo["title"]
        data["icon"] = einfo["thumb"]
        length = len(estream)
        # 1=标清，2=高清,3=超清
        if length >= 3:
            data["data"].append({
                "label": "超清",
                "code": 3,
                # "ext" : "",
                # "size" : "",
                # "type" : "",
            })
        if length >= 2:
            data["data"].append({
                "label": "高清",
                "code": 2,
                # "ext" : "",
                # "size" : "",
                # "type" : "",
            })
        if length >= 1:
            data["data"].append({
                "label": "标清",
                "code": 1,
                # "ext" : "",
                # "size" : "",
                # "type" : "",
            })
        return data

    def ParseURL(self, input_text, label, min=None, max=None):
        data = {
            "protocol": "http",
            "urls": [""],
            # "args" : {},
            # "duration" : 1111,
            # "length" : 222222,
            # "decrypt" : "KanKan",
            # "decryptData" : {},
            # "adjust" : "KanKan",
            # "adjustData" : { },
            # "segmentSize": 1024,
            # "maxDown" : 5,
            # "convert" : "",
            # "convertData" : "",
        }
        id = re.match('^http://[^\s]+/[^\s]+/([^\s]+)\.html', input_text).group(1)
        ejson_url = 'http://v.api.mgtv.com/player/video?retry=1&video_id=' + id
        ejson = getUrl(ejson_url)
        ejson = json.loads(ejson)
        if ejson["status"] != 200:
            return
        edata = ejson["data"]
        estream = edata["stream"]
        estream_domain = edata["stream_domain"]
        i = int(label) - 1
        stream = estream[i]
        stream_domain = estream_domain[i]
        host = str(stream_domain)
        url = str(stream["url"])
        aurl = url.split('?')
        a = aurl[0].strip('/playlist.m3u8')
        b = aurl[1].split('&')
        u = host + '/' + a + '?pno=1031&' + b[3] + '&' + b[4]
        op1 = getUrl(u)
        data1 = json.loads(op1)
        eurl = data1['info']
        data["urls"] = eurl
        info = {
            "label": i,
            "code": i,
            # "ext" : "",
            # "size" : "",
            # "type" : "",
        }
        return [data]
