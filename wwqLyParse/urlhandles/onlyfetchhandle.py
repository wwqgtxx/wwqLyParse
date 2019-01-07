#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib.request, io, os, sys, json, re, threading, queue, logging

try:
    from ..common import *
except Exception as e:
    from common import *

__all__ = ["OnlyFetchUrlHandle"]


class OnlyFetchUrlHandle(UrlHandle):
    filters = ['^(http|https)://']
    order = sys.maxsize

    async def url_handle(self, url):
        await get_url_service.get_url_async(url)
        return url

    @staticmethod
    @get_url_service.reg_check_response_func
    def pptv_check_response(resp: GetUrlResponse):
        if isinstance(resp.content, str):
            if "v.pptv.com" in resp.url:
                if "您所请求的网址（URL）无法获取" in resp.content:
                    return False
                if """document.write('<meta http-equiv="Refresh" Content="0; Url='+u+'">')""" in resp.content:
                    return False
        return True

    @staticmethod
    @get_url_service.reg_check_response_func
    def cookie_flash_check_response(resp: GetUrlResponse):
        if isinstance(resp.content, str):
            if "/cookie/flash.js" in resp.content:
                print(resp.content)
                logging.debug('detected "/cookie/flash.js" ,retry!')
                return False
        return True
