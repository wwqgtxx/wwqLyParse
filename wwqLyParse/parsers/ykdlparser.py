#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib.request,io,os,sys,json,re,math,subprocess,traceback

try:
    from ..lib import conf,bridge
except Exception as e:
    from lib import conf,bridge

try:
    from ..common import *
except Exception as e:
    from common import *
    
try:
    from . import yougetparser
except Exception as e:
    import yougetparser
    


class YKDLParser(yougetparser.YouGetParser):
        
    bin = './ykdl/ykdl.py'
        
    # make arg
    def _make_arg(self,url, _format=None):
        arg = self._make_proxy_arg()
        # NOTE ignore __default__ format
        if _format and (_format != '__default__'):
            arg += ['--format', _format]
        arg += ['-i']
        arg += ['--json', url]
        return arg
        

    def Parse(self,url,types=None):
        if (types is not None) and ("formats" not in types):
            return
        if ('www.iqiyi.com' in url):
            return []
        if re.search('www.iqiyi.com/(lib/m|a_)',url):
            return []
        out =  self._Parse(url,types)
        if "data" in out:
            for data in out['data']:
                data['label'] = data['label'] + ("@ykdl")
            out["caption"]= "YouKuDownLoader解析"
            out['sorted']= True
        return out

    def ParseURL(self,url,label,min=None,max=None):
        assert "@ykdl" in label
        out = self._ParseURL(url,label,min,max)
        if "iqiyi" in url:
            for item in out:
                item["unfixIp"] = True
        return out
        


