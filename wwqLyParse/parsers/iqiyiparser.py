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

__all__ = ["IQiYiParser"]

import json
import time
import hashlib
import random


def get_macid():
    '''获取macid,此值是通过mac地址经过算法变换而来,对同一设备不变'''
    macid = ''
    chars = 'abcdefghijklnmopqrstuvwxyz0123456789'
    size = len(chars)
    for i in range(32):
        macid += list(chars)[random.randint(0, size - 1)]
    return macid


def get_vf(url_params):
    '''计算关键参数vf'''
    sufix = ''
    for j in range(8):
        for k in range(4):
            v4 = 13 * (66 * k + 27 * j) % 35
            if (v4 >= 10):
                v8 = v4 + 88
            else:
                v8 = v4 + 49
            sufix += chr(v8)
    url_params += sufix
    m = hashlib.md5()
    m.update(url_params.encode('utf-8'))
    vf = m.hexdigest()
    return vf


def getvps(tvid, vid):
    tm = int(time.time() * 1000)
    host = 'http://cache.video.qiyi.com'
    src = '/vps?tvid=' + tvid + '&vid=' + vid + '&v=0&qypid=' + tvid + '_12&src=01012001010000000000&t=' + str(
        tm) + '&k_tag=1&k_uid=' + get_macid() + '&rs=1'
    vf = get_vf(src)
    req_url = host + src + '&vf=' + vf
    html = get_url(req_url, allow_cache=False)
    return json.loads(html)


class IQiYiParser(Parser):
    filters = ['http(s?)://www.iqiyi.com/']
    un_supports = ['www.iqiyi.com/(lib/m|a_)']
    types = ["formats"]

    stream_types = [
        {'id': '4K-H264', 'container': 'flv', 'video_profile': '(6)4K-H264'},
        {'id': '4K-H265', 'container': 'flv', 'video_profile': '(6)4K-H265'},
        {'id': '1080P-H264', 'container': 'flv', 'video_profile': '(5)1080P-H264'},
        {'id': '1080P-H265', 'container': 'flv', 'video_profile': '(5)1080P-H265'},
        {'id': '720P-H264', 'container': 'flv', 'video_profile': '(4)720P-H264'},
        {'id': '720P-H265', 'container': 'flv', 'video_profile': '(4)720P-H265'},
        {'id': '540P-H265', 'container': 'flv', 'video_profile': '(3)540P-H265'},
        {'id': '540P-H264', 'container': 'flv', 'video_profile': '(3)540P-H264'},
        {'id': '360P-H264', 'container': 'flv', 'video_profile': '(2)360P-H264'},
        {'id': '210P-H264', 'container': 'flv', 'video_profile': '(1)210P-H264'},
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

    parse_timeout = 60

    def get_stream_type(self, stream_id):
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
            stream_type = {'id': stream_id, 'container': 'flv', 'video_profile': stream_id}
        return stream_type

    def get_vid_and_title(self, url):
        html = get_url(url)
        video_info = match1(html, ":video-info='(.+?)'")
        if video_info:
            video_info = json.loads(video_info)
            logging.debug(video_info)
            tvid = str(video_info['tvId'])
            videoid = str(video_info['vid'])
            title = str(video_info['name'])
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
        return tvid, videoid, title

    def get_vps_data(self, tvid, videoid):
        vps_data = getvps(tvid, videoid)
        assert vps_data['code'] == 'A00000', 'can\'t play this video!!'

        logging.debug(vps_data)

        return vps_data

    def parse(self, input_text, *k, **kk):
        data = {
            "type": "formats",
            "name": "",
            "icon": "",
            "provider": "爱奇艺",
            "caption": "WWQ爱奇艺视频解析(桌面端接口)",
            # "warning" : "提示信息",
            # "sorted" : 1,
            "data": []
        }
        url = input_text
        html = get_url(url)
        tvid, videoid, title = self.get_vid_and_title(url)
        data["name"] = title
        vps_data = self.get_vps_data(tvid, videoid)
        url_prefix = vps_data['data']['vp']['du']
        stream = vps_data['data']['vp']['tkl'][0]
        vs_array = stream['vs']

        for vs in vs_array:
            bid = vs['bid']
            stream_type = self.get_stream_type(bid)
            info = {
                "label": '-'.join([stream_type['video_profile'], stream_type['container']]),
                "code": stream_type['id'],
                "ext": stream_type['container'],
                "size": byte2size(vs['vsize']),
                # "type" : "",
                # "download": []
            }

            info1 = info.copy()
            data["data"].append(info1)
            info2 = info.copy()
            info2["label"] = '-'.join([info["label"], "单线程"])
            info2["code"] = '-'.join([str(info["code"]), "S"])
            data["data"].append(info2)

        return data

    def parse_url(self, input_text, label, min=None, max=None, *k, **kk):
        def _worker(url, url_list):
            try:
                if len(url_list) > 5:
                    return
                json_data = json.loads(get_url(url, allow_cache=False))
                logging.debug(json_data)
                down_url = json_data['l']
                # url_head = r1(r'https?://([^/]*)', down_url)
                if down_url not in url_list:
                    url_list.append(down_url)
            except GreenletExit:
                pass

        use_pool = True
        if "-S" in label:
            label = label.split("-S")[0]
            use_pool = False
        url = input_text
        data = []
        tvid, videoid, title = self.get_vid_and_title(url)
        vps_data = self.get_vps_data(tvid, videoid)
        url_prefix = vps_data['data']['vp']['du']
        stream = vps_data['data']['vp']['tkl'][0]
        vs_array = stream['vs']
        for vs in vs_array:
            bid = vs['bid']
            fs_array = vs['fs']
            stream_type = self.get_stream_type(bid)
            if label == stream_type['id']:
                url_dict = dict()
                for seg_info in fs_array:
                    url = url_prefix + seg_info['l']
                    url_list = list()
                    url_dict[url] = url_list
                    info = {
                        "protocol": "http",
                        "urls": url_list,
                        "duration": seg_info['d'],
                        "length": seg_info['b'],
                        # "maxDown" : 1,
                        "unfixIp": True
                    }
                    data.append(info)
                if use_pool:
                    with WorkerPool(10) as pool:
                        for _ in range(10):
                            for seg_info in fs_array:
                                url = url_prefix + seg_info['l']
                                url_list = url_dict[url]
                                pool.spawn(_worker, url, url_list)
                        pool.join(timeout=self.parse_timeout)

                for seg_info in fs_array:
                    url = url_prefix + seg_info['l']
                    url_list = url_dict[url]
                    if len(url_list) == 0:
                        _worker(url, url_list)

                return data
        return []
