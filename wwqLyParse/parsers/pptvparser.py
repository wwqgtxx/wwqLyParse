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

__all__ = ["PPTVParser"]

import binascii
from xml.dom.minidom import parseString


def lshift(a, b):
    return (a << b) & 0xffffffff


def rshift(a, b):
    if a >= 0:
        return a >> b
    return (0x100000000 + a) >> b


def le32_pack(b_str):
    result = 0
    result |= b_str[0]
    result |= (b_str[1] << 8)
    result |= (b_str[2] << 16)
    result |= (b_str[3] << 24)
    return result


def tea_core(data, key_seg):
    delta = 2654435769

    d0 = le32_pack(data[:4])
    d1 = le32_pack(data[4:8])

    sum_ = 0
    for rnd in range(32):
        sum_ = (sum_ + delta) & 0xffffffff
        p1 = (lshift(d1, 4) + key_seg[0]) & 0xffffffff
        p2 = (d1 + sum_) & 0xffffffff
        p3 = (rshift(d1, 5) + key_seg[1]) & 0xffffffff

        mid_p = p1 ^ p2 ^ p3
        d0 = (d0 + mid_p) & 0xffffffff

        p4 = (lshift(d0, 4) + key_seg[2]) & 0xffffffff
        p5 = (d0 + sum_) & 0xffffffff
        p6 = (rshift(d0, 5) + key_seg[3]) & 0xffffffff

        mid_p = p4 ^ p5 ^ p6
        d1 = (d1 + mid_p) & 0xffffffff

    return bytes(unpack_le32(d0) + unpack_le32(d1))


def ran_hex(size):
    result = []
    for i in range(size):
        result.append(hex(int(15 * random.random()))[2:])
    return ''.join(result)


def zpad(b_str, size):
    size_diff = size - len(b_str)
    return b_str + bytes(size_diff)


def gen_key(t):
    key_seg = [1896220160, 101056625, 100692230, 7407110]
    t_s = hex(int(t))[2:].encode('utf8')
    input_data = zpad(t_s, 16)
    out = tea_core(input_data, key_seg)
    return out[:8].hex() + ran_hex(16)


def unpack_le32(i32):
    result = []
    result.append(i32 & 0xff)
    i32 = rshift(i32, 8)
    result.append(i32 & 0xff)
    i32 = rshift(i32, 8)
    result.append(i32 & 0xff)
    i32 = rshift(i32, 8)
    result.append(i32 & 0xff)
    return result


def get_elem(elem, tag):
    return elem.getElementsByTagName(tag)


def get_attr(elem, attr):
    return elem.getAttribute(attr)


def get_text(elem):
    return elem.firstChild.nodeValue


def shift_time(time_str):
    ts = time_str[:-4]
    return time.mktime(time.strptime(ts)) - 60


def parse_pptv_xml(dom):
    channel = get_elem(dom, 'channel')[0]
    title = get_attr(channel, 'nm')
    file_list = get_elem(channel, 'file')[0]
    item_list = get_elem(file_list, 'item')
    streams_cnt = len(item_list)
    item_mlist = []
    for item in item_list:
        rid = get_attr(item, 'rid')
        file_type = get_attr(item, 'ft')
        size = get_attr(item, 'filesize')
        width = get_attr(item, 'width')
        height = get_attr(item, 'height')
        bitrate = get_attr(item, 'bitrate')
        res = '{}x{}@{}kbps'.format(width, height, bitrate)
        item_meta = (file_type, rid, size, res)
        item_mlist.append(item_meta)

    dt_list = get_elem(dom, 'dt')
    dragdata_list = get_elem(dom, 'dragdata') or get_elem(dom, 'drag')

    stream_mlist = []
    for dt in dt_list:
        file_type = get_attr(dt, 'ft')
        serv_time = get_text(get_elem(dt, 'st')[0])
        expr_time = get_text(get_elem(dt, 'key')[0])
        serv_addr = get_text(get_elem(dt, 'sh')[0])
        stream_meta = (file_type, serv_addr, expr_time, serv_time)
        stream_mlist.append(stream_meta)

    segs_mlist = []
    for dd in dragdata_list:
        file_type = get_attr(dd, 'ft')
        seg_list = get_elem(dd, 'sgm')
        segs = []
        segs_size = []
        for seg in seg_list:
            rid = get_attr(seg, 'rid')
            size = get_attr(seg, 'fs')
            segs.append(rid)
            segs_size.append(size)
        segs_meta = (file_type, segs, segs_size)
        segs_mlist.append(segs_meta)
    return title, item_mlist, stream_mlist, segs_mlist


# mergs 3 meta_data
def merge_meta(item_mlist, stream_mlist, segs_mlist):
    streams = {}
    for i in segs_mlist:
        streams[i[0]] = {}

    for item in item_mlist:
        stream = streams[item[0]]
        stream['rid'] = item[1]
        stream['size'] = item[2] or 12653713
        stream['res'] = item[3]

    for s in stream_mlist:
        stream = streams[s[0]]
        stream['serv_addr'] = s[1]
        stream['expr_time'] = s[2]
        stream['serv_time'] = s[3]

    for seg in segs_mlist:
        stream = streams[seg[0]]
        stream['segs'] = seg[1]
        stream['segs_size'] = seg[2]

    return streams


def make_url(stream):
    host = stream['serv_addr']
    rid = stream['rid']
    key = gen_key(shift_time(stream['serv_time']))
    key_expr = stream['expr_time']

    src = []
    for i, seg in enumerate(stream['segs']):
        url = 'http://{}/{}/{}?key={}&k={}'.format(host, i, rid, key, key_expr)
        url += '&fpp.ver=1.3.0.23&type=ppbox.launcher'
        src.append(url)
    return src


class PPTVParser(Parser):
    filters = ['v.pptv.com/show/']
    un_supports = []
    types = ["formats"]

    stream_types = [
        {'id': '270p', 'container': 'mp4', 'video_profile': '(1)270P'},
        {'id': '480p', 'container': 'mp4', 'video_profile': '(2)480P'},
        {'id': '720p', 'container': 'mp4', 'video_profile': '(3)720P'},
        {'id': '1080p', 'container': 'mp4', 'video_profile': '(4)1080P'},
        {'id': '1080ph', 'container': 'mp4', 'video_profile': '(5)1080P高码'}
    ]

    supported_stream_types = ['270p', '480p', '720p', '1080p', '1080ph']

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

    def parse(self, input_text, *k, **kk):
        info = {
            "type": "formats",
            "name": "",
            "icon": "",
            "provider": "PPTV",
            "caption": "WWQ PPTV视频解析",
            # "warning" : "提示信息",
            # "sorted" : 1,
            "data": []
        }

        html = get_url(input_text)
        for _ in range(3):
            if """document.write('<meta http-equiv="Refresh" Content="0; Url='+u+'">')""" in html:
                logging.debug(html)
                html = get_url(input_text, force_flush_cache=True)
            else:
                break
        # logging.debug(html)
        vid = match1(html, 'webcfg\s*=\s*{"id":\s*(\d+)')
        xml = get_url(
            'http://web-play.pptv.com/webplay3-0-{}.xml?zone=8&version=4&username=&ppi=302c3333&type=ppbox.launcher&pageUrl=http%3A%2F%2Fv.pptv.com&o=0&referrer=&kk=&scver=1&appplt=flp&appid=pptv.flashplayer.vod&appver=3.4.3.3&nddp=1'.format(
                vid), allow_cache=False)
        # logging.debug(xml)
        dom = parseString(xml)
        m_title, m_items, m_streams, m_segs = parse_pptv_xml(dom)
        xml_streams = merge_meta(m_items, m_streams, m_segs)
        logging.debug(xml_streams)

        info["name"] = m_title

        for stream_id in xml_streams:
            stream_data = xml_streams[stream_id]
            src = make_url(stream_data)
            s = self.supported_stream_types[int(stream_id)]
            stream_type = self.get_stream_type(s)
            d_arr = []
            for i in src:
                d_arr.append({
                    "protocol": "http",
                    "urls": [i],
                    # "maxDown" : 1,
                    "unfixIp": True
                })
            info['data'].append({
                "label": '-'.join([stream_type['video_profile'], stream_type['container']]),
                "code": stream_type['id'],
                "ext": stream_type['container'],
                "size": byte2size(stream_data['size']),
                # "type" : "",
                "download": d_arr
            })

        return info
