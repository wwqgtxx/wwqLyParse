#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib.request, io, os, sys, json, re, threading, queue, logging

from pyquery.pyquery import PyQuery

try:
    from ..common import *
except Exception as e:
    from common import *

__all__ = ["LeListParser1", "LeListParser2"]


class LeListParser1(Parser):
    filters = ["www.le.com/ptv/vplay/"]
    types = ["list"]

    def parse(self, input_text, *k, **kk):
        html = get_url(input_text)
        pid = match1(html, r'pid:\s*(\w+),')
        if pid:
            html2_url = "http://www.le.com/tv/%s.html" % pid
            return ReCallMainParseFunc(input_text=html2_url, types="list")


class LeListParser2(Parser):
    filters = ["www.le.com/tv/"]
    types = ["list"]

    def parse(self, input_text, *k, **kk):
        html2 = get_url(input_text)
        html2 = PyQuery(html2)
        show_cnt = html2("div#first_videolist div.show_cnt > div")
        title = html2("div.top_tit > h2").text()
        total = len(show_cnt)
        data = {
            "data": [],
            "more": False,
            "title": title,
            "total": total,
            "type": "list",
            "caption": "乐视视频全集"
        }
        for i in show_cnt:
            col = PyQuery(i)
            a = col("dt > a")
            title = a.text()
            url = a.attr("href")
            subtitle = col("dd.d_cnt").text() or title
            info = {
                "name": title,
                "no": title,
                "subtitle": subtitle,
                "url": url
            }
            data["data"].append(info)
        return data
