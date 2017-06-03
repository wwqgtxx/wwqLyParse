#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib.request, io, os, sys, json, re, threading, queue, logging

from pyquery.pyquery import PyQuery

try:
    from ..common import *
except Exception as e:
    from common import *

__MODULE_CLASS_NAMES__ = ["LeListParser1", "LeListParser2"]


class LeListParser1(Parser):
    filters = ["www.le.com/ptv/vplay/"]
    types = ["list"]

    def Parse(self, input_text):
        html = getUrl(input_text)
        html = PyQuery(html)
        html2_url = html("a.more").attr("href")
        try:
            from ..main import Parse as main_parse
        except Exception as e:
            from main import Parse as main_parse
        result = main_parse(input_text=html2_url, types="list")
        if result:
            return result[0]


class LeListParser2(Parser):
    filters = ["www.le.com/tv/"]
    types = ["list"]

    def Parse(self, input_text):
        html2 = getUrl(input_text)
        html2 = PyQuery(html2)
        w120 = html2("div.gut > div.listTab > div.listPic > div.list > dl.w120 > dt > a")
        total = len(w120)
        title = html2("div.gut > div.listTab > div.listPic > div.tab:first-child > p.p1 > i").text()
        data = {
            "data": [],
            "more": False,
            "title": title,
            "total": total,
            "type": "list",
            "caption": "乐视视频全集"
        }
        for i in w120:
            i = PyQuery(i)
            url = i.attr("href")
            title = i("a > img").attr("title")
            info = {
                "name": title,
                "no": title,
                "subtitle": title,
                "url": url
            }
            data["data"].append(info)
        return data
