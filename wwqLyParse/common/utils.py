#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>

import os
import math
import re
import socket
import logging
import traceback
import urllib.request


def get_main():
    try:
        from .. import main
    except Exception as e:
        import main

    return main


def get_main_parse():
    return get_main().parse


def call_method_and_save_to_queue(queue, method, args, kwargs):
    queue.put(method(*args, **kwargs))


def get_caller_info():
    try:
        fn, lno, func, sinfo = traceback.extract_stack()[-3]
    except ValueError:  # pragma: no cover
        fn, lno, func = "(unknown file)", 0, "(unknown function)"
    try:
        fn = os.path.basename(fn)
    except:
        pass
    callmethod = "<%s:%d %s> " % (fn, lno, func)
    return callmethod


def isin(a, b, strict=True):
    result = False
    if isinstance(a, list):
        for item in a:
            if item in b:
                result = True
            elif strict:
                result = False
    else:
        result = (a in b)
    return result


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


def is_open(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, int(port)))
        s.shutdown(2)
        logging.info(get_caller_info() + '%d is open' % port)
        return True
    except:
        logging.info(get_caller_info() + '%d is down' % port)
        return False


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


# DEPRECATED in favor of match1()
def r1(pattern, text):
    m = re.search(pattern, text)
    if m:
        return m.group(1)


def match1(text, *patterns):
    """Scans through a string for substrings matched some patterns (first-subgroups only).

    Args:
        text: A string to be scanned.
        patterns: Arbitrary number of regex patterns.

    Returns:
        When only one pattern is given, returns a string (None if no match found).
        When more than one pattern are given, returns a list of strings ([] if no match found).
    """

    if len(patterns) == 1:
        pattern = patterns[0]
        match = re.search(pattern, text)
        if match:
            return match.group(1)
        else:
            return None
    else:
        ret = []
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                ret.append(match.group(1))
        return ret
