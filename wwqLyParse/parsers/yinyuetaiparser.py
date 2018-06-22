#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib.request, io, os, sys, json, re

from pyquery.pyquery import PyQuery
import urllib.parse

try:
    from ..common import *
except Exception as e:
    from common import *

JUDGE_VIP = True

__all__ = ["YinYueTaiParser", "YinYueTaiListParser"]


class YinYueTaiParser(Parser):
    filters = ['http://\w+.yinyuetai.com/video/(\d+)', 'http://\w+.yinyuetai.com/video/h5/(\d+)']
    types = ["formats"]
    ids = ['BD', 'TD', 'HD', 'SD']
    types_2_id = {'sh': 'BD', 'he': 'TD', 'hd': 'HD', 'hc': 'SD'}
    types_2_profile = {'sh': u'原画', 'he': u'超清', 'hd': u'高清', 'hc': u'标清', '': u'标清'}

    def parse(self, input_text, types=None, *k, **kk):
        data = {
            "type": "formats",
            "name": "",
            "icon": "http://xxx.cn/xxx.jpg",
            "provider": "音悦台",
            "caption": "音悦台解析",
            # "warning" : "提示信息",
            "sorted": 1,
            "data": []
        }
        vid = match1(input_text, 'http://\w+.yinyuetai.com/video/(\d+)')
        if not vid:
            vid = match1(input_text, 'http://\w+.yinyuetai.com/video/h5/(\d+)')
        api_data = json.loads(
            get_url('http://www.yinyuetai.com/insite/get-video-info?json=true&videoId={}'.format(vid), allow_cache=False))
        # api_data = json.loads(
        #     get_url('http://ext.yinyuetai.com/main/get-h-mv-info?json=true&videoId={}'.format(vid), allow_cache=False))
        # if api_data['error']:
        #     return []
        video_data = api_data['videoInfo']['coreVideoInfo']

        title = video_data['videoName']
        title = str(title).replace("&lt;", "《").replace("&gt;", "》")
        # artist = video_data['artistNames']
        data["name"] = title
        for s in video_data['videoUrlModels']:
            data["data"].append({
                "label": self.types_2_profile[s['qualityLevel']],
                "code": self.types_2_id[s['qualityLevel']],
                # "ext" : "",
                "size": byte2size(s['fileSize']),
                # "type" : "",
                "download": [{
                    "protocol": "http",
                    "urls": [s['videoUrl']],
                    # "args" : {},
                    # "duration" : 1111,
                    # "length" : 222222,
                    # "decrypt" : "KanKan",
                    # "decryptData" : {},
                    #  "adjust" : "KanKan",
                    # "adjustData" : { },
                    # "segmentSize": 1024,
                    # "maxDown" : 5,
                    # "convert" : "",
                    # "convertData" : "",
                }]
            })

        # data["data"] = sorted(data["data"], key=self.ids.index)

        return data


class YinYueTaiListParser(YinYueTaiParser):
    filters = ["so.yinyuetai.com"]
    types = ["collection"]
    types_2_profile = {'sh': u'原画', 'shd': u'超清', 'hd': u'高清', '': u'标清'}

    def parse(self, input_text, *k, **kk):
        data = {
            "data": [],
            "more": False,
            "title": '',
            "total": 0,
            "type": "collection",
            "caption": "音悦台全集"
        }
        keyword = input_text.split("http://so.yinyuetai.com/?keyword=")[1]
        data["title"] = urllib.parse.unquote(keyword)
        last_num = 1
        while True:
            api_data = get_url(
                "http://soapi.yinyuetai.com/search/video-search?keyword={}&pageIndex={}&pageSize=24".format(keyword,
                                                                                                            last_num))
            api_data = json.loads(api_data)
            if api_data['error'] or not api_data['videos']['data']:
                break
            for item in api_data['videos']['data']:
                title = "【%s】%s" % (self.types_2_profile[item["videoType"]], item["title"])
                url = "http://v.yinyuetai.com/video/%d" % item['id']
                info = {
                    "name": title,
                    "no": title,
                    "subtitle": title,
                    "url": url,
                    "unsure": True
                }
                data["data"].append(info)
            last_num += 1
        is_ok = False
        for item in data["data"]:
            if "【原画】" in item["name"]:
                item["unsure"] = False
                is_ok = True
                break
        if not is_ok:
            for item in data["data"]:
                if "【超清】" in item["name"]:
                    item["unsure"] = False
                    is_ok = True
                    break
        if not is_ok:
            for item in data["data"]:
                if "【高清】" in item["name"]:
                    item["unsure"] = False
                    is_ok = True
                    break
        if not is_ok:
            for item in data["data"]:
                if "【标清】" in item["name"]:
                    item["unsure"] = False
                    is_ok = True
                    break
        data["total"] = len(data["data"])
        return data
