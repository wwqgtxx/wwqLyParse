#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib, io, os, sys, json, re, math, subprocess, time, binascii, math, logging, random, queue

from pyquery.pyquery import PyQuery

from uuid import uuid4
from math import floor
import hashlib
import tempfile

try:
    from ..common import *
except Exception as e:
    from common import *

__all__ = ["QQListParser", "QQListParserX"]


class QQListParser(Parser):
    filters = ['v.qq.com/detail/']
    un_supports = []
    types = ["list"]

    def parse(self, input_text, *k, **kk):
        html = get_url(input_text)
        html = PyQuery(html)
        title = ""
        for meta in html('meta[itemprop="name"]'):
            meta = PyQuery(meta)
            title = meta.attr("content")
            break
        data = {
            "data": [],
            "more": False,
            "title": title,
            "total": 0,
            "type": "list",
            "caption": "QQ视频全集"
        }
        for a in html(".mod_episode a"):
            a = PyQuery(a)
            _title = ""
            for span in PyQuery(a("span")):
                span = PyQuery(span)
                if span.attr("itemprop") == "episodeNumber":
                    _title = "第%s集" % span.text()
                elif span.has_class("mark_v"):
                    _title += span.children("img").attr("alt")
            info = {
                "name": _title,
                "no": _title,
                "subtitle": _title,
                "url": a.attr("href")
            }
            data["data"].append(info)
        data["total"] = len(data["data"])

        return data


class QQListParserX(Parser):
    filters = ['v.qq.com/x/']
    un_supports = []
    types = ["list"]

    def parse(self, input_text, *k, **kk):
        m = re.findall(r'//v.qq.com/x/cover/([^\s]+)/', input_text)
        if not m:
            m = re.findall(r'//v.qq.com/x/cover/([^\s]+)\.html', input_text)
        url = ''
        if m:
            url = m[0]
            if url:
                url = "/detail/%s/%s.html" % (url[0], url)
            else:
                html = get_url(input_text)
                html = PyQuery(html)
                url = html("a._main_title").attr("href")
                if not url:
                    url = html('a[_stat="videolist:title"]').attr("href")
        if url:
            url = "https://v.qq.com" + str(url)
            logging.info("change %s to %s" % (input_text, url))
            return ReCallMainParseFunc(input_text=url, types="list")
