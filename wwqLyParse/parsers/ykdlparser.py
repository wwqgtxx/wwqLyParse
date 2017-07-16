#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib.request, io, os, sys, json, re, math, subprocess, traceback

try:
    from ..lib import conf, bridge
except Exception as e:
    from lib import conf, bridge

try:
    from ..common import *
except Exception as e:
    from common import *

__MODULE_CLASS_NAMES__ = ["YKDLParser"]
try:
    try:
        from . import yougetparser
    except Exception as e:
        import yougetparser


    class YKDLParser(yougetparser.YouGetParser):

        # unsupports = ['list.iqiyi.com']
        bin = './ykdl/ykdl.py'
        name = "YouKuDownLoader解析"

        # make arg
        def _make_arg(self, url, _format=None, use_info=False, *k, **kk):
            arg = self._make_proxy_arg()
            # NOTE ignore __default__ format
            if _format and (_format != '__default__'):
                arg += ['--format', _format]
            arg += ['-i']
            arg += ['--debug']
            arg += ['--json', url]
            return arg

        def _run(self, arg, need_stderr=False):
            return super(YKDLParser, self)._run(arg, need_stderr)

except:
    logging.exception("can't load yougetparser.py,it need to be super class")
    __MODULE_CLASS_NAMES__ = []
