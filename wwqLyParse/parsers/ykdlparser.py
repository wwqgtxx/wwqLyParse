#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib.request, io, os, sys, json, re, math, subprocess, traceback, logging

try:
    from ..common import *
except Exception as e:
    from common import *

__all__ = ["YKDLParser"]
try:
    from .yougetparser import YouGetParser

    class YKDLParser(YouGetParser):

        un_supports = YouGetParser.un_supports  # + ['www.iqiyi.com']
        bin = './ykdl/ykdl.py'
        name = "YouKuDownLoader解析"

        def _get_py_bin(self):
            py_bin = sys.executable
            if "wwqLyParse64.exe" in py_bin:
                py_bin = py_bin.replace("wwqLyParse64.exe", "wwqLyParse64-ykdl.exe")
            elif "wwqLyParse32.exe" in py_bin:
                py_bin = py_bin.replace("wwqLyParse32.exe", "wwqLyParse32-ykdl.exe")
            return py_bin

        def _get_proxy_args(self, port):
            return ["--proxy", "http://localhost:%s" % port]

        # make arg
        def _make_arg(self, url, _format=None, use_info=False, *k, **kk):
            arg = []
            # NOTE ignore __default__ format
            if _format and (_format != '__default__'):
                arg += ['--format', _format]
            arg += ['-i']
            arg += ['--debug']
            arg += ['--json', url]
            return arg

        def get_version(self):
            try:
                stdout, stderr = self._run(['-h'], need_stderr=True, use_hps=False)
                if "Errno" in stderr:
                    return ""
                return stdout.split('(')[1].split(')')[0]
            except Exception as e:
                logging.exception("get version error")
            return ""

except:
    logging.exception("can't load yougetparser.py,it need to be super class")
    __all__ = []
