#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>

import os
import socket
import logging
import traceback
import functools
import inspect
import ctypes
import uuid


# def get_main():
#     try:
#         from .. import main
#     except Exception as e:
#         import main
#
#     return main


def get_caller_info(call_deep=0):
    try:
        fn, lno, func, sinfo = traceback.extract_stack()[-(2 + call_deep)]
    except ValueError:  # pragma: no cover
        fn, lno, func = "(unknown file)", 0, "(unknown function)"
    try:
        fn = os.path.basename(fn)
    except:
        pass
    try:
        from .asyncio import get_task_name_with_thread
        thread_name = get_task_name_with_thread()
    except:
        thread_name = ""
    callmethod = "<%s:%d %s %s> " % (fn, lno, func, thread_name)
    return callmethod


def format_exception(e):
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


def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


def stop_thread(thread):
    _async_raise(thread.ident, SystemExit)
