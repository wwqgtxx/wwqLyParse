#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>

import os
import socket
import logging
import traceback
import functools


def get_main():
    try:
        from .. import main
    except Exception as e:
        import main

    return main


def get_main_parse():
    return functools.partial(get_main().parse, use_inside=True)


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


def print_exception(e):
    line = traceback.format_exception(Exception, e, e.__traceback__)
    text = ''.join(line)
    return text


def get_item_from_str(string, key):
    string = str(string)
    if string.startswith(key):
        string_array = string.split(key, 1)
        if len(string_array) == 2:
            return string_array[1].strip()


def mime_to_container(mime):
    mapping = {
        'video/3gpp': '3gp',
        'video/mp4': 'mp4',
        'video/webm': 'webm',
        'video/x-flv': 'flv',
    }
    if mime in mapping:
        return mapping[mime]
    else:
        return mime.split('/')[1]


def is_in(a, b, strict=True):
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
