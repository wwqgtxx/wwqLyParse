#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>

import os
import socket
import logging
import traceback


def get_main():
    try:
        from .. import main
    except Exception as e:
        import main

    return main


def get_main_parse():
    return get_main().parse


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
