#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import math
import logging
import urllib.request


def url_size(url, headers=None):
    error = None
    for n in range(3):
        try:
            if headers:
                response = urllib.request.urlopen(urllib.request.Request(url, headers=headers), None)
            else:
                response = urllib.request.urlopen(url)
            size = response.headers['content-length']
            if size is not None:
                return int(size)
        except Exception as e:
            error = e
    logging.error(error)
    return -1


def gen_bitrate(size_byte, time_s, unit_k=1024):
    if (size_byte <= 0) or (time_s <= 0):
        return '-1'  # can not gen bitrate
    raw_rate = size_byte * 8 / time_s  # bps
    kbps = raw_rate / unit_k
    bitrate = str(round(kbps, 1)) + 'kbps'
    return bitrate


# make a 2.3 number, with given length after .
def num_len(n, l=3):
    t = str(float(n))
    p = t.split('.')
    if l < 1:
        return p[0]
    if len(p[1]) > l:
        p[1] = p[1][:l]
    while len(p[1]) < l:
        p[1] += '0'
    t = ('.').join(p)
    # done
    return t


# byte to size
def byte2size(size_byte, flag_add_byte=False):
    unit_list = [
        'Byte',
        'KB',
        'MB',
        'GB',
        'TB',
        'PB',
        'EB',
    ]

    # check size_byte
    size_byte = int(size_byte)
    if size_byte < 1024:
        return str(size_byte) + unit_list[0]

    # get unit
    unit_i = int(math.floor(math.log(size_byte, 1024)))
    unit = unit_list[unit_i]
    size_n = size_byte / pow(1024, unit_i)

    size_t = num_len(size_n, 2)

    # make final size_str
    size_str = size_t + ' ' + unit

    # check flag
    if flag_add_byte:
        size_str += ' (' + str(size_byte) + ' Byte)'
    # done
    return size_str


def _second_to_time(time_s):
    def _number(raw):
        f = float(raw)
        if int(f) == f:
            return int(f)
        return f

    raw = _number(time_s)
    sec = math.floor(raw)
    ms = raw - sec
    minute = math.floor(sec / 60)
    sec -= minute * 60
    hour = math.floor(minute / 60)
    minute -= hour * 60
    # make text, and add ms
    t = str(minute).zfill(2) + ':' + str(sec).zfill(2) + '.' + str(round(ms * 1e3))
    if hour > 0:  # check add hour
        t = str(hour).zfill(2) + ':' + t
    return t
