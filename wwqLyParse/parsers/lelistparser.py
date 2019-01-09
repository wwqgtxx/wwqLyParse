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

    async def parse(self, input_text, *k, **kk):
        html = await get_url_service.get_url_async(input_text)
        pid = match1(html, r'pid:\s*(\w+),')
        if pid:
            html2_url = "http://www.le.com/tv/%s.html" % pid
            return ReCallMainParseFunc(input_text=html2_url, types="list")


class LeListParser2(Parser):
    filters = ["www.le.com/tv/"]
    types = ["list"]

    async def parse(self, input_text, *k, **kk):
        html2 = await get_url_service.get_url_async(input_text)
        html2 = PyQuery(html2)
        title = html2("div.top_tit > h2").text()
        try:
            pid = match1(input_text, r'http://www.le.com/tv/(\w+).html')
            api_url = "http://d.api.m.le.com/detail/episode?pid={}&platform=pc&page=1&pagesize=1000&type=1".format(pid)
            api_data = await get_url_service.get_url_async(api_url)
            safe_print(api_data)
            api_json = json.loads(api_data)
            assert api_json["code"] == "200"
            api_json_data = api_json["data"]
            total = api_json_data["total"]
            data = {
                "data": [],
                "more": False,
                "title": title,
                "total": total,
                "type": "list",
                "caption": "乐视视频全集"
            }
            for item in api_json_data["list"]:
                if item.get("isyugao", 0) != 0:
                    continue
                item_title = item["title"]
                info = {
                    "name": item_title,
                    "no": item_title,
                    "subtitle": item["sub_title"],
                    "url": "http://www.le.com/ptv/vplay/{}.html".format(item["vid"]),
                    "icon": item["pic"]
                }
                data["data"].append(info)
            return data
        except AsyncCancelled:
            raise
        except:
            logging.exception("parse error rollback to old function")
            return await self.old_parse(input_text, *k, **kk)

    async def old_parse(self, input_text, *k, **kk):
        html2 = await get_url_service.get_url_async(input_text)
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
