#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib.request, io, os, sys, json, re, threading, queue, logging

from pyquery.pyquery import PyQuery

try:
    from ..common import *
except Exception as e:
    from common import *

__all__ = ["YouKuListParser1", "YouKuListParser2", "YouKuListParser3", "YouKuListParser4"]


class YouKuListParser1(Parser):
    filters = ["v.youku.com/v_show"]
    types = ["list"]

    def parse(self, input_text, *k, **kk):
        html = get_url(input_text)
        # html = PyQuery(html)
        # m = html("div.tvinfom > h2 > a").attr("href")
        # if not m:
        #     return []
        # new_url = "http:" + m
        m = re.findall('<a href="(//list\.youku\.com/show/id_[^\s]+\.html)"', html)
        if not m:
            m = re.findall('(//list\.youku\.com/show/id_[^\s]+\.html)', html)
            if not m:
                return []
        new_url = "https:" + m[0]
        logging.debug(new_url)
        return ReCallMainParseFunc(input_text=new_url, types="list")


class YouKuListParser2(Parser):
    filters = ["v.youku.com/v_show"]
    types = ["collection"]

    def parse(self, input_text, *k, **kk):
        html = get_url(input_text)
        m = re.findall('(//list\.youku\.com/albumlist/show/id_[^\s]+\.html)', html)
        if not m:
            return []
        new_url = "https:" + m[0]
        logging.debug(new_url)
        return ReCallMainParseFunc(input_text=new_url, types="list")


class YouKuListParser3(Parser):
    # http://list.youku.com/show/id_z2ae8ee1c837b11e18195.html
    # official playlist
    filters = ["list.youku.com/show"]
    types = ["list"]

    def parse(self, input_text, *k, **kk):
        html = get_url(input_text)
        m = re.findall('showid:"([0-9]+)",', html)  # showid:"307775"
        if not m:
            return []
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
            new_url = "https://list.youku.com/show/episode?id=" + m[0] + "&stage=reload_" + str(
                last_num) + "&callback=a"
            json_data = get_url(new_url)[14:-2]
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
                        title = "第%02d集" % num
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


class YouKuListParser4(Parser):
    # http://list.youku.com/albumlist/show/id_2336634.html
    # UGC playlist
    filters = ["list.youku.com/albumlist/show"]
    types = ["collection"]

    def parse(self, input_text, *k, **kk):
        html = get_url(input_text)
        html = PyQuery(html)
        p_title = html("div.pl-title")
        title = p_title.attr("title")
        list_id = re.search('https?://list.youku.com/albumlist/show/id_(\d+)\.html', input_text).group(1)
        ep = 'https://list.youku.com/albumlist/items?id={}&page={}&size=20&ascending=1&callback=a'

        first_u = ep.format(list_id, 1)
        xhr_page = get_url(first_u)
        json_data = json.loads(xhr_page[14:-2])
        # print(json_data)
        # video_cnt = json_data['data']['total']
        xhr_html = json_data['html']
        # print(xhr_html)
        data = {
            "data": [],
            "more": False,
            "title": title,
            "total": 0,
            "type": "collection",
            "caption": "优酷视频全集"
        }
        last_num = 1
        while True:
            new_url = ep.format(list_id, last_num)
            json_data = get_url(new_url)[14:-2]
            info = json.loads(json_data)
            if info.get("error", None) == 1 and info.get("message", None) == "success":
                new_html = info.get("html", None)
                if new_html:
                    new_html = PyQuery(new_html)
                    items = new_html("a[target='video'][data-from='2-1']")
                    for item in items:
                        item = PyQuery(item)
                        url = "http:" + item.attr("href")
                        title = item.attr("title")
                        info = {
                            "name": title,
                            "no": title,
                            "subtitle": title,
                            "url": url
                        }
                        data["data"].append(info)
                    last_num += 1
                else:
                    break
            else:
                break
        data["total"] = len(data["data"])
        # print(data)

        return data
