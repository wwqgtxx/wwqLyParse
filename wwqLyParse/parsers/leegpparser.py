#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib, io, os, sys, json, re, math, subprocess, time, binascii, math, logging, random, queue

from uuid import uuid4
from math import floor
import hashlib
import tempfile

try:
    from ..common import *
except Exception as e:
    from common import *

__all__ = ["LeEGPParser"]


class LeEGPParser(Parser):
    filters = ['http://www.le.com/ptv/vplay/']
    un_supports = []
    types = ["formats"]

    # stream_types = [
    #     {'id': '54', 'container': 'm3u8', 'video_profile': '(9)4K'},
    #     {'id': '53', 'container': 'm3u8', 'video_profile': '(8)1080P高码'},
    #     {'id': '52', 'container': 'm3u8', 'video_profile': '(7)1080P'},
    #     {'id': '51', 'container': 'm3u8', 'video_profile': '(6)720P高码'},
    #     {'id': '22', 'container': 'm3u8', 'video_profile': '(5)720P'},
    #     {'id': '13', 'container': 'm3u8', 'video_profile': '(4)540P'},
    #     {'id': '21', 'container': 'm3u8', 'video_profile': '(3)360P'},
    #     {'id': '58', 'container': 'm3u8', 'video_profile': '(2)320P'},
    #     {'id': '9', 'container': 'm3u8', 'video_profile': '(1)280P'},
    # ]

    stream_ids = [str(i) for i in range(250)]

    def get_vid(self, url):
        return match1(url, 'vplay/(\d+).html', '#record/(\d+)')

    def get_first_json(self, vid, q):
        # normal process
        if type(q) == list:
            q = ','.join(q)
        url = 'http://tvepg.letv.com/apk/data/common/security/playurl/geturl/byvid.shtml?vid=%s&key=&vtype=%s' % (
            vid, q)
        r = get_url(url, allow_cache=False)
        data = json.loads(r)
        return data

    def parse(self, input_text, *k, **kk):
        info = {
            "type": "formats",
            "name": "",
            "icon": "",
            "provider": "乐视",
            "caption": "WWQ乐视EPG视频解析",
            # "warning" : "提示信息",
            # "sorted" : 1,
            "data": []
        }

        html = get_url(input_text)
        info['name'] = match1(html, r'title:"(.+?)",')
        vid = self.get_vid(input_text)
        data = self.get_first_json(vid, self.stream_ids)
        debug(json.dumps(data))
        if data["statusCode"] != 1001:
            return
        if not data["data"]:
            return
        data_infos = data["data"][0]["infos"]
        for data_info in data_infos:
            # if "encodeId" not in data_info:
            #     continue
            q = data_info["vtype"]
            info['data'].append({
                "label": "%s-%s-%s-%sx%s-%skbps-%skbps" % (
                    # q,
                    # self.get_stream_type(q)["video_profile"],
                    data_info["gfmt"].lower(),
                    data_info["vfmt"].upper(),
                    data_info["afmt"].replace(' ', '').replace('-', ''),
                    data_info["vwidth"],
                    data_info["vheight"],
                    data_info["vbr"],
                    data_info["abr"]),
                "code": q,
                "ext": 'ts',  # data_info["gfmt"],
                "size": byte2size(data_info["gsize"]),
                "type": "",
                "download": [{
                    "protocol": "m3u8",
                    "urls": data_info["mainUrl"],
                    # "maxDown" : 1,
                    "unfixIp": True
                }]
            })

        return info
