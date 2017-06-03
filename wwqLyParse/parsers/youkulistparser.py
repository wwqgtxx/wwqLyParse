#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib.request, io, os, sys, json, re, threading, queue, logging

from pyquery.pyquery import PyQuery

try:
    from ..common import *
except Exception as e:
    from common import *

__MODULE_CLASS_NAMES__ = ["YouKuListParser1", "YouKuListParser2"]


class YouKuListParser1(Parser):
    filters = ["v.youku.com/v_show"]
    types = ["list"]

    def Parse(self, input_text):
        html = getUrl(input_text)
        m = re.findall('<a class="desc-link" href="(//list\.youku\.com/show/id_[^\s]+\.html)"', html)
        new_url = "http:" + m[0]
        try:
            from ..main import Parse as main_parse
        except Exception as e:
            from main import Parse as main_parse
        result = main_parse(input_text=new_url, types="list")
        if result:
            return result[0]


class YouKuListParser2(Parser):
    filters = ["list.youku.com/show"]
    types = ["list"]

    def Parse(self, input_text):
        html = getUrl(input_text)
        m = re.findall('showid:"([0-9]+)",', html)  # showid:"307775"
        logging.info(m[0])

        html = PyQuery(html)
        p_title = html("li.p-row.p-title")
        p_title("li>a").remove()
        p_title("li>span").remove()
        title = p_title.text().replace("：", '')

        data = {
            "data": [],
            "more": False,
            "title": title,
            "total": 0,
            "type": "list",
            "caption": "优酷视频全集"
        }
        last_num = 0
        while True:
            new_url = "http://list.youku.com/show/episode?id=" + m[0] + "&stage=reload_" + str(last_num) + "&callback=a"
            json_data = getUrl(new_url)[14:-2]
            info = json.loads(json_data)
            if info.get("error", None) == 0 and info.get("message", None) == "success":
                new_html = info.get("html", None)
                if new_html:
                    new_html = PyQuery(new_html)
                    items = new_html("a")
                    for item in items:
                        item = PyQuery(item)
                        num = int(item.text())
                        url = "http:" + item.attr("href")
                        title = "%s 第%02d集" % (data["title"], num)
                        info = {
                            "name": title,
                            "no": title,
                            "subtitle": title,
                            "url": url
                        }
                        data["data"].append(info)
                        last_num = num
                    last_num += 1
                else:
                    continue
            else:
                break
        data["total"] = len(data["data"])
        return data
