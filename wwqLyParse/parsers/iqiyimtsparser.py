#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib, io, os, sys, json, re, math, subprocess, time, binascii, math, logging

from uuid import uuid4
from random import random, randint
from math import floor
import hashlib

try:
    from ..common import *
except Exception as e:
    from common import *

__all__ = ["IQiYiMTsParser"]


class IQiYiMTsParser(Parser):
    filters = ['http(s?)://www.iqiyi.com/']
    un_supports = ['www.iqiyi.com/(lib/m|a_)']
    types = ["formats"]

    stream_types = [
        {'id': '4K-H264', 'container': 'ts', 'video_profile': '(6)4K-H264'},
        {'id': '4K-H265', 'container': 'ts', 'video_profile': '(6)4K-H265'},
        {'id': '1080P-H264', 'container': 'ts', 'video_profile': '(5)1080P-H264'},
        {'id': '1080P-H265', 'container': 'ts', 'video_profile': '(5)1080P-H265'},
        {'id': '720P-H264', 'container': 'ts', 'video_profile': '(4)720P-H264'},
        {'id': '720P-H265', 'container': 'ts', 'video_profile': '(4)720P-H265'},
        {'id': '540P-H265', 'container': 'ts', 'video_profile': '(3)540P-H265'},
        {'id': '540P-H264', 'container': 'ts', 'video_profile': '(3)540P-H264'},
        {'id': '360P-H264', 'container': 'ts', 'video_profile': '(2)360P-H264'},
        {'id': '210P-H264', 'container': 'ts', 'video_profile': '(1)210P-H264'},
    ]

    vd_2_id = {
        96: '210P-H264',
        1: '360P-H264',
        2: '540P-H264',
        21: '540P-H265',
        4: '720P-H264',
        17: '720P-H265',
        5: '1080P-H264',
        18: '1080P-H265',
        19: '4K-H265',
        10: '4K-H264',
    }

    async def get_vms(self, tvid, vid):
        t = int(time.time() * 1000)
        src = '76f90cbd92f94a2e925d83e8ccd22cb7'
        key = 'd5fb4bd9d50c4be6948c97edd7254b0e'
        sc = hashlib.new('md5', bytes(str(t) + key + vid, 'utf-8')).hexdigest()
        vmsreq = 'http://cache.m.iqiyi.com/tmts/{0}/{1}/?t={2}&sc={3}&src={4}'.format(tvid, vid, t, sc, src)
        return json.loads(await get_url_service.get_url_async(vmsreq, allow_cache=False))

    def getStream_type(self, stream_id):
        try:
            stream_id = self.vd_2_id[stream_id]
            stream_type = None
            for item in self.stream_types:
                if item["id"] == stream_id:
                    stream_type = item
                    break
        except:
            stream_id = str(stream_id)
            logging.warning("can't match stream_id " + stream_id)
            stream_type = {'id': stream_id, 'container': 'ts', 'video_profile': stream_id}
        return stream_type

    async def parse(self, input_text, *k, **kk):
        data = {
            "type": "formats",
            "name": "",
            "icon": "",
            "provider": "爱奇艺",
            "caption": "WWQ爱奇艺视频解析(移动端TS接口)",
            # "warning" : "提示信息",
            # "sorted" : 1,
            "data": []
        }
        url = input_text
        html = await get_url_service.get_url_async(url)
        video_info = match1(html, ":video-info='(.+?)'")
        if video_info:
            video_info = json.loads(video_info)
            logging.debug(video_info)
            tvid = str(video_info['tvId'])
            videoid = str(video_info['vid'])
            title = video_info['name']
        else:
            tvid = match1(html,
                          '#curid=(.+)_',
                          'data-player-tvid="([^"]+)"',
                          'tvid=([^&]+)',
                          'tvId:([^,]+)',
                          r'''param\['tvid'\]\s*=\s*"(.+?)"''',
                          r'"tvid":\s*"(\d+)"'
                          )
            videoid = match1(html,
                             '#curid=.+_(.*)$',
                             'data-player-videoid="([^"]+)"',
                             'vid=([^&]+)',
                             'vid:"([^"]+)',
                             r'''param\['vid'\]\s*=\s*"(.+?)"''',
                             r'"vid":\s*"(\w+)"'
                             )
            title = match1(html, '<title>([^<]+)').split('-')[0]
        # self.vid = (tvid, videoid)
        info = await self.get_vms(tvid, videoid)
        assert info['code'] == 'A00000', 'can\'t play this video'
        data["name"] = title
        used_id = []
        if 'ctl' in info['data']:
            for stream_id in info['data']['ctl']["vip"]["bids"]:
                v = info['data']['ctl']['configs'][str(stream_id)]['vid']
                vip_info = await self.get_vms(tvid, v)
                if vip_info['code'] == 'A00000':
                    vip_url = vip_info['data']['m3u']
                    stream_type = self.getStream_type(stream_id)
                    used_id.append(stream_type['id'])
                    data["data"].append({
                        "label": ('-').join([stream_type['video_profile'], stream_type['container']]),
                        "code": stream_type['id'],
                        "ext": stream_type['container'],
                        # "size": 0,
                        # "type" : "",
                        "download": [{
                            "protocol": "m3u8",
                            "urls": vip_url,
                            # "maxDown" : 1,
                            "unfixIp": True
                        }]
                    })
        for stream in info['data']['vidl']:
            stream_id = stream['vd']
            stream_type = self.getStream_type(stream_id)
            if stream_type['id'] in used_id:
                break
            data["data"].append({
                "label": ('-').join([stream_type['video_profile'], stream_type['container']]),
                "code": stream_type['id'],
                "ext": stream_type['container'],
                # "size": 0,
                # "type" : "",
                "download": [{
                    "protocol": "m3u8",
                    "urls": stream['m3u'],
                    # "maxDown" : 1,
                    "unfixIp": True
                }]
            })

        return data
