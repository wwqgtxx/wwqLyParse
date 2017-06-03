#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib.request, io, os, sys, json, re, math, subprocess, traceback, logging

try:
    from ..common import *
except Exception as e:
    from common import *

__MODULE_CLASS_NAMES__ = []


class LypPvParser(Parser):
    try:
        try:
            from ..lyp_pv import run
        except Exception as e:
            from lyp_pv import run
        filters = run.GetVersion()['filter']
    except Exception as e:
        filters = []
    types = ["formats"]
    unsupports = ['www.iqiyi.com', 'list.iqiyi.com', 'www.le.com']

    # parse functions
    def Parse(self, url):
        try:
            from ..lyp_pv import run
        except Exception as e:
            from lyp_pv import run
        logging.info("call lyp_pv.run.Parse(" + url + ")")
        out = run.Parse(url)
        if "data" in out:
            for data in out['data']:
                old_label = data['label']
                data["code"] = run._parse_label(old_label)
                data['label'] = re.compile('\(\d\)\s*').sub('', str(old_label))
                parts = data['label'].split('_')
                num = int(parts[0])
                if num == -3:
                    parts[0] = "0"
                elif num == -1:
                    parts[0] = "1"
                elif num == 0:
                    parts[0] = "2"
                elif num == 2:
                    parts[0] = "3"
                elif num == 4:
                    parts[0] = "4"
                elif num == 7:
                    parts[0] = "5"
                data['label'] = ('_').join(parts)
            out["caption"] = "负锐解析"
            out.pop("icon")
            out.pop("warning")
        return out

    def ParseURL(self, url, label, min=None, max=None):
        try:
            from ..lyp_pv import run
        except Exception as e:
            from lyp_pv import run
        hd = float(label)
        logging.info("call lyp_pv.run._do_parse(" + url + "," + str(hd) + "," + str(hd) + ")")
        pvinfo = run._do_parse(url, hd_min=hd, hd_max=hd)
        if 'error' in pvinfo:
            return pvinfo
        result = run._t_parse_url(pvinfo, hd)
        if "iqiyi" in url:
            for item in result:
                item["unfixIp"] = True
        return result

    def getLypPvVersion(self):
        try:
            try:
                from ..lyp_pv import run
            except Exception as e:
                from lyp_pv import run
                logging.debug("call lyp_pv.run._lyyc_about()")
            info = run._lyyc_about()
            return "负锐解析[" + str(info['pack_version']) + "]" + str(info['version'])
        except Exception as e:
            logging.exception()
            # print(e)
            # import traceback
            # traceback.print_exc()
        return ""
