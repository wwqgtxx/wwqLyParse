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

__MODULE_CLASS_NAMES__ = ["MgTVParser", "MgTVListParser"]


class MgTVParser(Parser):
    filters = ['www.mgtv.com/']
    types = ["formats"]

    def get_api_data(self, url):
        # id = re.match('^http://[^\s]+/[^\s]+/([^\s]+)\.html', url).group(1)
        vid = match1(url, 'http://www.mgtv.com/(?:b|l)/\d+/(\d+).html')
        if not vid:
            vid = match1(url, 'http://www.mgtv.com/hz/bdpz/\d+/(\d+).html')
        api_url = 'http://pcweb.api.mgtv.com/player/video?video_id={}'.format(vid)
        api_data = getUrl(api_url)
        api_data = json.loads(api_data)
        # print(api_data)
        return api_data

    def Parse(self, input_text, types=None, *k, **kk):
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
        api_data = self.get_api_data(input_text)
        if api_data['code'] != 200 and api_data['data']:
            return []
        info = api_data['data']['info']
        data["name"] = info['title'] + ' ' + info['desc']
        data["icon"] = info['thumb']
        for lstream in api_data['data']['stream']:
            if lstream['url']:
                data["data"].append({
                    "label": lstream['name'],
                    "code": lstream['def'],
                    # "ext" : "",
                    # "size" : "",
                    # "type" : "",
                })
        return data

    def ParseURL(self, input_text, label, min=None, max=None, *k, **kk):
        data = {
            "protocol": "m3u8",
            "urls": [],
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
        api_data = self.get_api_data(input_text)
        if api_data['code'] != 200 and api_data['data']:
            return []
        # domain = api_data['data']['stream_domain'][0]
        for lstream in api_data['data']['stream']:
            if lstream['url'] and lstream['def'] == label:
                for domain in api_data['data']['stream_domain']:
                    api_data2 = json.loads(getUrl(domain + lstream['url'], allowCache=False))
                    # print(api_data2)
                    url = api_data2['info']
                    data["urls"].append(url)
                    break
        return [data]


class MgTVListParser(MgTVParser):
    filters = ["www.mgtv.com/"]
    types = ["collection"]

    def Parse(self, input_text, *k, **kk):
        data = {
            "data": [],
            "more": False,
            "title": '',
            "total": 0,
            "type": "collection",
            "caption": "芒果TV全集"
        }
        api_data = self.get_api_data(input_text)
        if api_data['code'] != 200 and api_data['data']:
            return []
        info = api_data['data']['info']
        collection_id = info['collection_id']
        url1 = 'http://pcweb.api.mgtv.com/variety/showlist?collection_id=' + collection_id
        api_data1 = json.loads(getUrl(url1))
        # print(api_data1)
        if api_data1['code'] != 200 and not api_data1['data']:
            return []
        data['title'] = api_data1['data']['info']['title']
        for tab in api_data1['data']['tab_m']:
            url2 = url1 + '&month=' + tab['m']
            api_data2 = json.loads(getUrl(url2))
            # print(api_data2)
            if api_data2['code'] == 200 and api_data2['data']:
                for item in api_data2['data']['list']:
                    if item['isnew'] == '2':
                        continue
                    info = {
                        "no": item['t2']+' '+item['t1'],
                        "subtitle": item['t3'],
                        "url": 'http://www.mgtv.com' + item['url']
                    }
                    # print(info)
                    data["data"].append(info)
        return data

    def ParseURL(self, url, label, min=None, max=None, *k, **kk):
        pass
