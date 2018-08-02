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

if sys.version_info[0] == 3:
    WR_ord = int
else:
    WR_ord = ord

__all__ = []  # ["LeParser"]


class LeParser(Parser):
    filters = ['http://www.le.com/ptv/vplay/']
    un_supports = []
    types = ["formats"]

    stream_types = [
        {'id': '1080p', 'container': 'm3u8', 'video_profile': '(5)1080P'},
        {'id': '1300', 'container': 'm3u8', 'video_profile': '(4)超清'},
        {'id': '1000', 'container': 'm3u8', 'video_profile': '(3)高清'},
        {'id': '720p', 'container': 'm3u8', 'video_profile': '(2)标清'},
        {'id': '350', 'container': 'm3u8', 'video_profile': '(1)流畅'}
    ]

    supported_stream_types = ['1080p', '1300', '1000', '720p', '350']

    def decode_m3u8(self, data):
        version = data[0:5]
        if version.lower() == b'vc_01':
            # get real m3u8
            loc2 = data[5:]
            length = len(loc2)
            loc4 = [0] * (2 * length)
            for i in range(length):
                loc4[2 * i] = WR_ord(loc2[i]) >> 4
                loc4[2 * i + 1] = WR_ord(loc2[i]) & 15
            loc6 = loc4[len(loc4) - 11:] + loc4[:len(loc4) - 11]
            loc7 = [0] * length
            for i in range(length):
                loc7[i] = (loc6[2 * i] << 4) + loc6[2 * i + 1]
            return ''.join([chr(i) for i in loc7])
        else:
            # directly return
            return data

    def calcTimeKey(self, t):
        ror = lambda val, r_bits: ((val & (2 ** 32 - 1)) >> r_bits % 32) | (
                val << (32 - (r_bits % 32)) & (2 ** 32 - 1))
        magic = 185025305
        return ror(t, magic % 17) ^ magic

    def get_stream_type(self, stream_id):
        try:
            stream_type = None
            for item in self.stream_types:
                if item["id"] == stream_id:
                    stream_type = item
                    break
        except:
            stream_id = str(stream_id)
            logging.warning("can't match stream_id " + stream_id)
            stream_type = {'id': stream_id, 'container': 'm3u8', 'video_profile': stream_id}
        return stream_type

    def get_vid(self, url):
        return match1(url, 'vplay/(\d+).html', '#record/(\d+)')

    def get_first_json(self, vid):
        # normal process
        url = 'http://player-pc.le.com/mms/out/video/playJson?id={}&platid=1&splatid=101&format=1&tkey={}&domain=www.le.com&region=cn&source=1000&accesyx=1'.format(
            vid, self.calcTimeKey(int(time.time())))
        r = get_url(url, allow_cache=False)
        data = json.loads(r)
        return data

    def get_available_stream_id(self, data):
        return list(data["playurl"]["dispatch"].keys())

    def parse(self, input_text, *k, **kk):
        info = {
            "type": "formats",
            "name": "",
            "icon": "",
            "provider": "乐视",
            "caption": "WWQ乐视视频解析",
            # "warning" : "提示信息",
            # "sorted" : 1,
            "data": []
        }

        vid = self.get_vid(input_text)
        data = self.get_first_json(vid)
        logging.debug(data)
        data = data['msgs']

        info['name'] = data['playurl']['title']
        available_stream_id = self.get_available_stream_id(data)
        for stream in available_stream_id:
            stream_type = self.get_stream_type(stream)
            info['data'].append({
                "label": '-'.join([stream_type['video_profile'], stream_type['container']]),
                "code": stream_type['id'],
                "ext": stream_type['container'],
                # "size": 0,
                # "type" : "",
                # "download": [{
                #     "protocol": "m3u8",
                #     "urls": vip_url,
                #     # "maxDown" : 1,
                #     "unfixIp": True
                # }]
            })

        return info

    def get_m3u8_from_location(self, location):
        suffix = '&r=' + str(int(time.time() * 1000)) + '&appid=500'
        m3u8 = get_url(location + suffix, encoding="raw", allow_cache=False)
        return m3u8

    def parse_url(self, input_text, label, min=None, max=None, *k, **kk):
        info = {
            "protocol": "m3u8",
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
        vid = self.get_vid(input_text)
        data = self.get_first_json(vid)
        data = data['msgs']
        available_stream_id = self.get_available_stream_id(data)
        with WorkerPool() as pool:
            result_queue = queue.Queue()
            location_list = list()
            if label in available_stream_id:
                stream = label
                for _ in range(3):
                    s_url = data["playurl"]["domain"][0] + data["playurl"]["dispatch"][stream][0]
                    uuid = hashlib.sha1(s_url.encode('utf8')).hexdigest() + '_0'
                    s_url = s_url.replace('tss=0', 'tss=ios')
                    s_url += "&m3v=1&termid=1&format=1&hwtype=un&ostype=MacOS10.12.4&p1=1&p2=10&p3=-&expect=3&tn={}&vid={}&uuid={}&sign=letv".format(
                        random.random(), vid, uuid)
                    r2 = get_url(s_url, allow_cache=False)
                    data2 = json.loads(r2)

                    # hold on ! more things to do
                    # to decode m3u8 (encoded)
                    if "nodelist" in data2:
                        for node in data2["nodelist"]:
                            location = node["location"]
                            if location not in location_list:
                                location_list.append(location)
                                pool.spawn(call_method_and_save_to_queue, result_queue, self.get_m3u8_from_location,
                                           args=(location,), kwargs={})
                    else:
                        location = data2["location"]
                        if location not in location_list:
                            location_list.append(location)
                            pool.spawn(call_method_and_save_to_queue, result_queue, self.get_m3u8_from_location,
                                       args=(location,), kwargs={})
                m3u8 = result_queue.get()
                while not m3u8:
                    m3u8 = result_queue.get()
                m3u8_list = self.decode_m3u8(m3u8)
                with tempfile.NamedTemporaryFile(suffix=".m3u8") as f:
                    f.write(m3u8_list)
                    file_url = f.name
                    info["urls"] = ["file:///" + file_url]
                # file_name = put_new_http_cache_data(m3u8_list, ".m3u8")
                # file_url = get_http_cache_data_url(file_name)
                # info["urls"] = [file_url]

        return [info]
