#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
from .base import *
from ..workerpool import *
from ..for_path import get_real_path
from ..lru_cache import LRUCache
from ..key_lock import KeyLockDict, FUCK_KEY_LOCK
from ..utils import get_caller_info
import configparser
import re
import json
import logging


class GetUrlService(object):

    def __init__(self):
        self.url_cache = LRUCache(size=URL_CACHE_MAX, timeout=URL_CACHE_TIMEOUT)
        self.url_key_lock = KeyLockDict()
        self.pool_get_url = WorkerPool(GET_URL_PARALLEL_LIMIT, thread_name_prefix="GetUrlPool")
        self.fake_headers = FAKE_HEADERS.copy()
        self.ssl_verify = True
        self.http_proxy = None
        self.impl = None  # type:GetUrlImpl
        self.inited = False

    def init(self):
        if not self.inited:
            configparser.RawConfigParser.OPTCRE = re.compile(r'(?P<option>[^=\s][^=]*)\s*(?P<vi>[=])\s*(?P<value>.*)$')
            config = configparser.ConfigParser()
            config.read(get_real_path("./config.ini"))
            self.http_proxy = config.get("get_url", "http_proxy", fallback=None)
            self.ssl_verify = config.getboolean("get_url", "ssl_verify", fallback=True)
            if self.impl is None:
                try:
                    from .aiohttp import AioHttpGetUrlImpl
                    self.impl = AioHttpGetUrlImpl(self)
                except:
                    pass
            if self.impl is None:
                try:
                    from .requests import RequestsGetUrlImpl
                    self.impl = RequestsGetUrlImpl(self)
                except:
                    pass
            if self.impl is None:
                try:
                    from .urllib import UrlLibGetUrlImpl
                    self.impl = UrlLibGetUrlImpl(self)
                except:
                    pass
            logging.debug(self.impl)
            self.inited = True

    def _get_url_key_lock(self, url_json, allow_cache):
        if allow_cache:
            return self.url_key_lock[url_json]
        else:
            return FUCK_KEY_LOCK

    def get_url(self, o_url, encoding=None, headers=None, data=None, method=None, cookies=None, verify=None,
                allow_cache=True, use_pool=True, pool=None, force_flush_cache=False, callmethod=None,
                only_content=True, stream=False):
        self.init()
        # if encoding is None:
        #     encoding = 'utf-8'
        if pool is None:
            pool = self.pool_get_url
        if not use_pool:
            pool = None
        if verify is None:
            verify = self.ssl_verify
        if callmethod is None:
            callmethod = get_caller_info(1)
        if data:
            allow_cache = False
        else:
            data = None
        if stream:
            allow_cache = False
            only_content = False
        url_json_dict = {"o_url": o_url, "encoding": encoding, "headers": headers, "method": method, "cookies": cookies}
        url_json = json.dumps(url_json_dict, sort_keys=False, ensure_ascii=False)
        url_json_dict["data"] = data
        url_json_dict["verify"] = verify
        url_json_dict["stream"] = stream

        with self._get_url_key_lock(url_json, allow_cache):
            if force_flush_cache:
                self.url_cache.pop(url_json, None)
                logging.debug(callmethod + "force_flush_cache get:" + url_json)
            if allow_cache:
                if url_json in self.url_cache:
                    result = self.url_cache[url_json]
                    logging.debug(callmethod + "cache get:" + url_json)
                    if only_content:
                        return result.content
                    else:
                        return result
                logging.debug(callmethod + "normal get:" + url_json)
            else:
                logging.debug(callmethod + "nocache get:" + url_json)
                # use_pool = False

            result = self.impl.get_url(url_json=url_json, url_json_dict=url_json_dict, callmethod=callmethod, pool=pool)
            if allow_cache and result:
                self.url_cache[url_json] = result
            if only_content:
                return result.content
            else:
                return result


get_url_service = GetUrlService()
get_url = get_url_service.get_url

__all__ = ["GetUrlService", "get_url_service", "get_url", "EMPTY_COOKIES"]
