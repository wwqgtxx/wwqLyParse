#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib.request, io, os, sys, json, re

from pyquery.pyquery import PyQuery

try:
    from ..common import *
except Exception as e:
    from common import *

__all__ = ["IndexParser"]


class IndexParser(Parser):
    filters = ['^http://www.le.com$']
    types = ["collection"]

    def parse(self, input_text, *k, **kk):
        return self.Parse_le(input_text)

    def Parse_le(self, input_text):
        html = PyQuery(get_url(input_text))
        items = html('dt.d_tit')
        title = "LETV"
        i = 0
        data = {
            "data": [],
            "more": False,
            "title": title,
            "total": i,
            "type": "collection"
        }
        for item in items:
            a = PyQuery(item).children('a')
            name = a.text()
            no = a.text()
            subtitle = a.text()
            url = a.attr('href')
            if url is None:
                continue
            if not re.match('^http://www\.le\.com/.+\.html', url):
                continue
            info = {
                "name": name,
                "no": no,
                "subtitle": subtitle,
                "url": url,
                "caption": "首页地址列表"
            }
            data["data"].append(info)
            i = i + 1
        total = i
        data["total"] = total
        return data
