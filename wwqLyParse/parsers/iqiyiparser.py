#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib, io, os, sys, json, re, math, subprocess, time, logging

from uuid import uuid4
from random import random, randint
from math import floor
import hashlib

try:
    from ..common import *
except Exception as e:
    from common import *

import os
import socket

try:
    from ..lib import bridge
except Exception as e:
    from lib import bridge

__MODULE_CLASS_NAMES__ = []

CONFIG = {
    "host": "127.0.0.1",
    "port": 48271,
    "key": None,
}


class IQiYiParser(Parser):
    filters = ['http://www.iqiyi.com/']
    unsupports = ['www.iqiyi.com/(lib/m|a_)']
    types = ["formats"]

    stream_types = [
        {'id': '4k', 'container': 'f4v', 'video_profile': '(6)4K'},
        {'id': 'fullhd', 'container': 'f4v', 'video_profile': '(5)1080P'},
        {'id': 'suprt-high', 'container': 'f4v', 'video_profile': '(4)720P'},
        {'id': 'super', 'container': 'f4v', 'video_profile': '(3)超清'},
        {'id': 'high', 'container': 'f4v', 'video_profile': '(2)高清'},
        {'id': 'standard', 'container': 'f4v', 'video_profile': '(1)标清'},
        {'id': 'topspeed', 'container': 'f4v', 'video_profile': '(0)最差'},
    ]

    stream_to_bid = {'4k': 10, 'fullhd': 5, 'suprt-high': 4, 'super': 3, 'high': 2, 'standard': 1, 'topspeed': 96}

    def _run_kill_271_cmd5(self):
        py_bin = bridge.pn(bridge.pjoin(bridge.get_root_path(), './lib/AIRSDK_Compiler/bin/adl.exe'))
        y_bin = bridge.pn(bridge.pjoin(bridge.get_root_path(), './lib/kill_271_cmd5/handwich_bridge.xml'))
        args = [py_bin, y_bin, '--']
        args += ['--ip', CONFIG["host"], '--port', str(CONFIG["port"])]
        if CONFIG["key"] != None:
            args += ['--key', str(CONFIG["key"])]
        logging.debug(args)
        p = subprocess.Popen(args, shell=False, cwd=bridge.get_root_path(), close_fds=True)

    def checkinit(self):
        url = 'http://%s:%d/' % (
            CONFIG["host"], CONFIG["port"]) + 'handwich_bridge/call?core=cmd5&f=about'
        if CONFIG["key"] != None:
            url += '?key=' + str(CONFIG["key"])
        result = getUrl(url, allowCache=False, usePool=False)
        if result is None:
            logging.debug('core not loaded')
            return False
        info = json.loads(result)
        if info[0] != 'ret':
            logging.debug('core not loaded, ' + str(info))
            return False
        logging.debug('core ' + "cmd5" + ', ' + str(info[1]))
        return True

    def init(self):
        for n in range(3):
            if IsOpen(CONFIG["host"], CONFIG["port"]) and self.checkinit():
                return
            else:
                self._run_kill_271_cmd5()
            for i in range(5):
                if not IsOpen(CONFIG["host"], CONFIG["port"]):
                    time.sleep(1 + i)
                else:
                    url = 'http://%s:%d/' % (
                        CONFIG["host"],
                        CONFIG["port"]) + 'handwich_bridge/load_core?id=cmd5&path=' + urllib.parse.quote(
                        bridge.pn(bridge.pjoin(bridge.get_root_path(), './lib/kill_271_cmd5/kill_271_cmd5.swf')))
                    if CONFIG["key"] != None:
                        url += '?key=' + str(CONFIG["key"])
                    getUrl(url, allowCache=False, usePool=False)
                    if self.checkinit():
                        return
            CONFIG["port"] += 1
        raise Exception("can't init server")

    def closeServer(self):
        if IsOpen(CONFIG["host"], CONFIG["port"]):
            url = 'http://%s:%d/' % (CONFIG["host"], CONFIG["port"]) + 'handwich_bridge/exit'
            if CONFIG["key"] != None:
                url += '?key=' + str(CONFIG["key"])
            getUrl(url, allowCache=False, usePool=False)

    def getVRSXORCode(self, arg1, arg2):
        loc3 = arg2 % 3
        if loc3 == 1:
            return arg1 ^ 121
        if loc3 == 2:
            return arg1 ^ 72
        return arg1 ^ 103

    def getVrsEncodeCode(self, vlink):
        loc6 = 0
        loc2 = ''
        loc3 = vlink.split("-")
        loc4 = len(loc3)
        # loc5=loc4-1
        for i in range(loc4 - 1, -1, -1):
            loc6 = self.getVRSXORCode(int(loc3[loc4 - i - 1], 16), i)
            loc2 += chr(loc6)
        return loc2[::-1]

    def getDispathKey(self, rid):
        tp = ")(*&^flash@#$%a"  # magic from swf
        time = json.loads(getUrl("http://data.video.qiyi.com/t?tn=" + str(random()), allowCache=False))["t"]
        t = str(int(floor(int(time) / (10 * 60.0))))
        return hashlib.new("md5", bytes(t + tp + rid, "utf-8")).hexdigest()

    def getvf(self, vmsreq):
        url = 'http://%s:%d/' % (
            CONFIG["host"], CONFIG["port"]) + 'handwich_bridge/call?core=cmd5&f=calc&a=' + urllib.parse.quote(
            json.dumps([vmsreq, vmsreq]))
        if CONFIG["key"] != None:
            url += '?key=' + str(CONFIG["key"])
        results = json.loads(getUrl(url, allowCache=False, usePool=False))
        return results[1]

    def getVMS(self, tvid, videoid):
        # tm ->the flash run time for md5 usage
        # um -> vip 1 normal 0
        vid = videoid
        tm = str(randint(2000, 4000))
        uid = ''  # self.gen_uid

        vmsreq = '/vms?key=fvip&src=1702633101b340d8917a69cf8a4b8c7c' + \
                 "&tvId=" + tvid + "&vid=" + vid + "&vinfo=1&tm=" + tm + \
                 "&qyid=" + uid + "&puid=" + \
                 "&authkey=" + hashlib.new('md5', bytes(hashlib.new('md5', b'').hexdigest() + str(tm) + tvid,
                                                        'utf-8')).hexdigest() + \
                 "&um=1" + "&pf=b6c13e26323c537d" + "&thdk=" + '' + "&thdt=" + '' + "&rs=1" + "&k_tag=1" + "&qdv=1"

        vmsreq = 'http://cache.video.qiyi.com' + vmsreq + "&vf=" + self.getvf(vmsreq)
        # vmsreq='http://cache.video.qiyi.com/vms?key=fvip&src=1702633101b340d8917a69cf8a4b8c7c&tvId=451038600&vid=faca833cc73ec8d7d8d248199bc3e7b8&vinfo=1&tm=7807&qyid=&puid=&authKey=04494c4efd643082cb7852621f7a8e6c&um=0&pf=b6c13e26323c537d&thdk=&thdt=&rs=1&k_tag=1&qdv=1&vf=30ed40c5e2dc8bdc532c7c0c1df13994'


        return json.loads(getUrl(vmsreq, headers={'Accept-Encoding': 'gzip, deflate, sdch'}, allowCache=False))

    def getInfo(self, url):
        html = getUrl(url)
        tvid = r1(r'#curid=(.+)_', url) or \
               r1(r'tvid=([^&]+)', url) or \
               r1(r'data-player-tvid="([^"]+)"', html)
        videoid = r1(r'#curid=.+_(.*)$', url) or \
                  r1(r'vid=([^&]+)', url) or \
                  r1(r'data-player-videoid="([^"]+)"', html)
        # self.vid = (tvid, videoid)

        info = self.getVMS(tvid, videoid)

        assert info["code"] == "A000000"

        info["data"]["vi"]["vn"] = info["data"]["vi"]["vn"].replace('\u200b', '')
        title = info["data"]["vi"]["vn"]

        assert title != "广告宣传片"

        return info

    def Parse(self, input_text, types=None):
        self.init()
        data = {
            "type": "formats",
            "name": "",
            "icon": "",
            "provider": "爱奇艺",
            "caption": "WWQ爱奇艺视频解析",
            # "warning" : "提示信息",
            "sorted": 1,
            "data": []
        }
        info = self.getInfo(input_text)

        data["name"] = info["data"]["vi"]["vn"]

        # data.vp = json.data.vp
        #  data.vi = json.data.vi
        #  data.f4v = json.data.f4v
        # if movieIsMember data.vp = json.data.np

        # for highest qualities
        # for http://www.iqiyi.com/v_19rrmmz5yw.html  not vp -> np
        assert info["data"]['vp']["tkl"] != ''
        vs = info["data"]["vp"]["tkl"][0]["vs"]

        for stream in self.stream_types:
            for i in vs:
                if self.stream_to_bid[stream['id']] == i['bid']:
                    video_links = i["fs"]  # now in i["flvs"] not in i["fs"]
                    if not i["fs"][0]["l"].startswith("/"):
                        tmp = self.getVrsEncodeCode(i["fs"][0]["l"])
                        if tmp.endswith('mp4'):
                            video_links = i["flvs"]
                    # self.stream_urls[stream['id']] = video_links
                    size = 0
                    time_s = 0
                    for l in video_links:
                        size += l['b']
                        time_s += l['d'] / 1e3
                    time_s = round(time_s, 3)
                    bitrate = gen_bitrate(size, time_s)
                    try:
                        size_str = byte2size(size, False)
                        size = byte2size(size, True)
                    except Exception as e:
                        logging.exception()
                        # import traceback
                        # traceback.print_exc()
                        size_str = "0"
                        size = 0
                    data["data"].append({
                        "label": ('-').join(
                            [stream['video_profile'], stream['container'], i['scrsz'], size_str, bitrate]),
                        "code": stream['id'],
                        "ext": stream['container'],
                        "size": size_str,
                        # "type" : "",
                    })
                    # streams[stream['id']] = {'container': stream['container'], 'video_profile': stream['video_profile'], 'size' : size}
                    break
        return data

    def ParseURL(self, input_text, label, min=None, max=None):
        self.init()
        datas = []

        stream_id = label
        gen_uid = uuid4().hex
        info = self.getInfo(input_text)
        inio_baseurl = info["data"]["vp"]["du"].split("/")
        assert info["data"]['vp']["tkl"] != ''
        vs = info["data"]["vp"]["tkl"][0]["vs"]

        urls = []
        for i in vs:
            if self.stream_to_bid[stream_id] == i['bid']:
                video_links = i["fs"]  # now in i["flvs"] not in i["fs"]
                if not i["fs"][0]["l"].startswith("/"):
                    tmp = self.getVrsEncodeCode(i["fs"][0]["l"])
                    if tmp.endswith('mp4'):
                        video_links = i["flvs"]
                # self.stream_urls[stream['id']] = video_links
                for ii in video_links:
                    vlink = ii["l"]
                    if not vlink.startswith("/"):
                        # vlink is encode
                        vlink = self.getVrsEncodeCode(vlink)
                    key = self.getDispathKey(vlink.split("/")[-1].split(".")[0])
                    baseurl = [x for x in inio_baseurl]
                    baseurl.insert(-1, key)
                    url = "/".join(
                        baseurl) + vlink + '?su=' + gen_uid + '&qyid=' + uuid4().hex + '&client=&z=&bt=&ct=&tn=' + str(
                        randint(10000, 20000))
                    result = json.loads(getUrl(url, allowCache=False))["l"]
                    # print(result)
                    urls.append(result)
        # download should be complete in 10 minutes
        # because the url is generated before start downloading
        # and the key may be expired after 10 minutes
        for url in urls:
            data = {
                "protocol": "http",
                "urls": url,
                # "maxDown" : 1,
                "unfixIp": True
            }
            datas.append(data)
        # data["urls"] = urls
        return datas

    def closeParser(self):
        self.closeServer()
        return
