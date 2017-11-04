#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib.request, io, os, sys, json, re, threading, queue, logging

from pyquery.pyquery import PyQuery

try:
    from ..common import *
except Exception as e:
    from common import *

__MODULE_CLASS_NAMES__ = ["FilesParser1", "FilesParser2", "FilesParser3"]


class FilesParser1(Parser):
    filters = [r"^file:///[^\s]+\.m3u8$"]
    types = ["formats"]

    def parse(self, input_text, *k, **kk):
        return {
            "type": "formats",
            "name": "m3u8",
            "sorted": 1,
            "data": [
                {
                    "label": "m3u8",
                    "download": [{
                        "protocol": "m3u8",
                        "urls": [input_text],
                    }]
                }
            ]
        }


class FilesParser2(Parser):
    filters = [r"^(http|https)://"]
    types = ["formats"]

    def parse(self, input_text, *k, **kk):
        data = get_url(input_text)
        if str(data).startswith("#EXTM3U"):
            return {
                "type": "formats",
                "name": "m3u8",
                "sorted": 1,
                "data": [
                    {
                        "label": "m3u8",
                        "download": [{
                            "protocol": "m3u8",
                            "urls": [input_text],
                        }]
                    }
                ]
            }
        else:
            return {}


class FilesParser3(Parser):
    filters = [r"^file:///[^\s]+\.list$"]
    types = ["collection"]

    def parse(self, input_text, *k, **kk):
        data = {
            "data": [],
            "more": False,
            "title": '',
            "total": 0,
            "type": "collection",
            "caption": "XXX全集"
        }
        last_num = 0
        with open(input_text[8:]) as f:
            for line in f.readlines():
                url = line.strip()
                title = "%d" % (last_num + 1)
                info = {
                    "name": title,
                    "no": title,
                    "subtitle": title,
                    "url": url,
                    "unsure": False
                }
                data["data"].append(info)
                last_num += 1
        data["total"] = len(data["data"])
        return data
