#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib, io, os, sys, json, re, math, subprocess, time, binascii, math, logging, random, queue

from uuid import uuid4
from math import floor
import hashlib
import tempfile

try:
    from ..common import *
except Exception as e:
    from common import *

__all__ = ["PPTVListParser"]


class PPTVListParser(Parser):
    filters = ['v.pptv.com/show/']
    un_supports = []
    types = ["list"]

    async def parse(self, input_text, *k, **kk):
        ppi = json.loads(await get_url_service.get_url_async("https://ppi.api.pptv.com/ppi.php"))["ppi"]
        logging.debug(ppi)

        html = await get_url_service.get_url_async(input_text)
        # cid = match1(html, 'webcfg\s*=\s*{"id":\s*(\d+)')
        pid = match1(html, 'webcfg\s*=\s*{.*"pid":\s*(\d+)')
        json_url = "http://apis.web.pptv.com/show/videoList?from=web&version=1.0.0&format=json&pid={}&cat_id=2&vt=22".format(
            pid)
        json_data = json.loads(await get_url_service.get_url_async(json_url, cookies={"ppi": ppi}))
        logging.debug(json_data)
        title = ""
        data = {
            "data": [],
            "more": False,
            "title": title,
            "total": json_data["data"]["total"],
            "type": "list",
            "caption": "PPTV视频全集"
        }

        for i in json_data["data"]["list"]:
            title = i["title"]
            data["title"] = match1(title, '(.*) 第\d+集')
            title = match1(title, '(第\d+集)')
            info = {
                "name": title,
                "no": title,
                "subtitle": title,
                "url": i["url"]
            }
            data["data"].append(info)

        # json_url = "http://apis.web.pptv.com/show/star?cid={}".format(cid)
        # json_data = json.loads(await get_url_service.get_url_async(json_url, cookies={"ppi": ppi}))
        # logging.debug(json_data)
        # data["title"] = json_data["info"][0]["title"]

        return data
