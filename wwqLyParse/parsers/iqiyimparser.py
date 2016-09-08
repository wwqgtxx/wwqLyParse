#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib,io,os,sys,json,re,math,subprocess,time,binascii,math,logging

from uuid import uuid4
from random import random,randint
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


class IQiYiMParser(Parser):

    filters = ['http://www.iqiyi.com/']
    unsupports = ['www.iqiyi.com/(lib/m|a_)']
    types = ["formats"]
    
    stream_types = [
        {'id': 'high', 'container': 'mp4', 'video_profile': '(2)高清'},
        {'id': 'standard', 'container': 'mp4', 'video_profile': '(1)标清'},
    ]

    supported_stream_types = [ 'high', 'standard']

    stream_to_bid = {  '4k': 10, 'fullhd' : 5, 'suprt-high' : 4, 'super' : 3, 'high' : 2, 'standard' :1, 'topspeed' :96}
    
    M = [1732584193, -271733879]
    M.extend([~M[0], ~M[1]])
    I_table = [7, 12, 17, 22, 5, 9, 14, 20, 4, 11, 16, 23, 6, 10, 15, 21]
    C_base = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8388608, 432]


    def L(self,n, t):
        trunc = self.trunc
        if t is None:
            t = 0
        return trunc(((n >> 1) + (t >> 1) << 1) + (n & 1) + (t & 1))


    def rshift(self,val, n):
        return val >> n if val >= 0 else (val+0x100000000) >> n


    def trunc(self,n):
        n = n % 0x100000000
        if n > 0x7fffffff:
            n -= 0x100000000
        return n


    def gen_sc(self,tvid, Z):
        def transform(string, mod):
            num = int(string, 16)
            return (num >> 8 * (i % 4) & 255 ^ i % mod) << ((a & 3) << 3)

        L = self.L
        rshift = self.rshift
        C_base = self.C_base
        M = self.M
        I_table = self.I_table
        trunc = self.trunc
        
        C = list(C_base)
        o = list(M)
        k = str(Z - 7)
        for i in range(13):
            a = i
            C[a >> 2] |= ord(k[a]) << 8 * (a % 4)

        for i in range(16):
            a = i + 13
            start = (i >> 2) * 8
            r = '03967743b643f66763d623d637e30733'
            C[a >> 2] |= transform(''.join(reversed(r[start:start + 8])), 7)

        for i in range(16):
            a = i + 29
            start = (i >> 2) * 8
            r = '7038766939776a32776a32706b337139'
            C[a >> 2] |= transform(r[start:start + 8], 1)

        for i in range(9):
            a = i + 45
            if i < len(tvid):
                C[a >> 2] |= ord(tvid[i]) << 8 * (a % 4)

        for a in range(64):
            i = a
            I = i >> 4
            C_index = [i, 5 * i + 1, 3 * i + 5, 7 * i][I] % 16 + rshift(a, 6)
            m = L(
                    L(
                        o[0],
                        [
                            trunc(o[1] & o[2]) | trunc(~o[1] & o[3]),
                            trunc(o[3] & o[1]) | trunc(~o[3] & o[2]),
                            o[1] ^ o[2] ^ o[3],
                            o[2] ^ trunc(o[1] | ~o[3])
                        ][I]
                    ),
                    L(
                        trunc(int(abs(math.sin(i + 1)) * 4294967296)),
                        C[C_index] if C_index < len(C) else None
                    )
                )
            I = I_table[4 * I + i % 4]
            o = [
                    o[3],
                    L(o[1], trunc(trunc(m << I) | rshift(m, 32 - I))),
                    o[1],
                    o[2],
                ]

        new_M = [L(o[0], M[0]), L(o[1], M[1]), L(o[2], M[2]), L(o[3], M[3])]
        s = [new_M[a >> 3] >> (1 ^ a & 7) * 4 & 15 for a in range(32)]
        return binascii.hexlify(bytes(s))[1::2]
           
    def getVMS(self,tvid,vid,rate):
        #tm ->the flash run time for md5 usage
        #um -> vip 1 normal 0
        #authkey -> for password protected video ,replace '' with your password
        #puid user.passportid may empty?
        #TODO: support password protected video
        t = int(time.time() * 1000)
        sc = self.gen_sc(tvid, t).decode('utf-8')
        vmsreq= 'http://cache.m.iqiyi.com/jp/tmts/{}/{}/?platForm=h5&rate={}&tvid={}&vid={}&cupid=qc_100001_100186&type=mp4&olimit=0&agenttype=13&src=d846d0c32d664d32b6b54ea48997a589&sc={}&t={}&__jsT=null'.format(tvid, vid, rate, tvid, vid, sc, t - 7)
        return json.loads(getUrl(vmsreq,allowCache = False)[13:])
    
   
    def Parse(self,input_text):
        data = {
            "type" : "formats",
            "name" : "",
            "icon" : "",
            "provider" : "爱奇艺",
            "caption" : "WWQ爱奇艺视频解析(移动端MP4接口)",
            #"warning" : "提示信息",
            "sorted" : 1,
            "data" : []
        }
        url = input_text
        html = getUrl(url)
        tvid = r1(r'#curid=(.+)_', url) or \
               r1(r'tvid=([^&]+)', url) or \
               r1(r'data-player-tvid="([^"]+)"', html)
        videoid = r1(r'#curid=.+_(.*)$', url) or \
                  r1(r'vid=([^&]+)', url) or \
                  r1(r'data-player-videoid="([^"]+)"', html)
        #self.vid = (tvid, videoid)

        for stream in self.stream_types:
            info = self.getVMS(tvid, videoid,self.stream_to_bid[stream['id']])
            if info["code"] == "A00000":
                size = url_size(info['data']['m3u'])
                if "duration" in info['data']:
                    time_s = info['data']["duration"]
                    time_s = round(time_s, 3)
                    bitrate = gen_bitrate(size,time_s)
                else:
                    time_s = 0
                    bitrate = ""
                try:
                    size_str = byte2size(size, False)
                except Exception as e:
                    logging.exception()
                    #import traceback
                    #traceback.print_exc()
                    size_str = "0"
                data["name"] = info['data']['playInfo']['vn']
                data["data"].append({
                        "label" : ('-').join([stream['video_profile'],stream['container'],size_str,bitrate]),
                        "code" : stream['id'],
                        "ext" : stream['container'],
                        "size" : size_str,
                        #"type" : "",
                        "download" : [{
                            "protocol" : "http",
                            "urls" :  info['data']['m3u'],
                            "duration" : time_s*1e3,
                            "length" : size,
                            #"maxDown" : 1,
                            "unfixIp" : True
                        }]
                    })
                #streams[stream] = {'container': 'mp4', 'video_profile': stream, 'src' : [info['data']['m3u']], 'size' : url_size(info['data']['m3u'])}
        return data
                    