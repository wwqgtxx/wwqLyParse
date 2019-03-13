#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
from .base import *
from ..async_pool import AsyncPool
from .. import asyncio
from ..for_path import get_real_path, PY35
from ..lru_cache import LRUCache
from ..key_lock import AsyncKeyLockDict, ASYNC_FUCK_KEY_LOCK
from ..utils import get_caller_info
import configparser
import re
import json
import logging
import threading
import functools
import selectors


class GetUrlService(object):

    def __init__(self):
        self.url_cache = LRUCache(size=URL_CACHE_MAX, timeout=URL_CACHE_TIMEOUT, use_lock=False)
        self.url_key_lock = None  # type:AsyncKeyLockDict
        self.loop = None  # type:asyncio.AbstractEventLoop
        self.pool_get_url = None  # type:AsyncPool
        self.fake_headers = FAKE_HEADERS.copy()
        self.check_response_func_list = list()
        self.check_response_retry_num = GET_URL_CHECK_RESP_RETRY_NUM
        self.ssl_verify = True
        self.http_proxy = None
        self.impl = None  # type:GetUrlImpl
        self.inited = False
        self.init_lock = threading.Lock()

    def init(self):
        with self.init_lock:
            if not self.inited:
                configparser.RawConfigParser.OPTCRE = re.compile(
                    r'(?P<option>[^=\s][^=]*)\s*(?P<vi>[=])\s*(?P<value>.*)$')
                config = configparser.ConfigParser()
                config.read(get_real_path("./config.ini"))
                self.http_proxy = config.get("get_url", "http_proxy", fallback=None)
                self.ssl_verify = config.getboolean("get_url", "ssl_verify", fallback=True)
                self.url_key_lock = AsyncKeyLockDict()
                force_use_selector = selectors.DefaultSelector is not selectors.SelectSelector
                if self.http_proxy:
                    force_use_selector = True
                self.loop = asyncio.new_running_async_loop("GetUrlLoop",
                                                           force_use_selector=force_use_selector)
                self.pool_get_url = AsyncPool(GET_URL_PARALLEL_LIMIT, thread_name_prefix="GetUrlPool", loop=self.loop)
                if self.impl is None:
                    try:
                        if not PY35:
                            from .aiohttp import AioHttpGetUrlImpl
                        else:
                            from .aiohttp352 import AioHttpGetUrlImpl
                            self.ssl_verify = False
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
            return ASYNC_FUCK_KEY_LOCK

    def new_headers_from_fake(self, _dict=None, **kwargs):
        headers = self.fake_headers.copy()
        if _dict:
            headers.update(_dict)
        if kwargs:
            headers.update(kwargs)
        return headers

    def new_cookie_jar(self):
        self.init()
        return self.impl.new_cookie_jar()

    def force_flush_cache(self, response, callmethod=None):
        self.init()
        if callmethod is None:
            callmethod = get_caller_info(1)
        return asyncio.run_in_other_loop(
            self._force_flush_cache_async(response, callmethod=callmethod), loop=self.loop)

    async def force_flush_cache_async(self, response, callmethod=None):
        self.init()
        if callmethod is None:
            callmethod = get_caller_info(1)
        return await asyncio.async_run_in_loop(
            self._force_flush_cache_async(response, callmethod=callmethod), loop=self.loop, cancel_connect=False)

    async def _force_flush_cache_async(self, response, callmethod=None):
        self.init()
        if callmethod is None:
            callmethod = get_caller_info(1)
        url_json = getattr(response, "url_json", response)
        if url_json is not None:
            async with self._get_url_key_lock(url_json, True):
                self.url_cache.pop(url_json, None)
                logging.debug(callmethod + "force_flush_cache:" + url_json)

    def get_url(self, o_url, encoding=None, headers=None, data=None, method=None, cookies=None, cookie_jar=None,
                verify=None, allow_cache=True, callmethod=None, stream=False):
        self.init()
        if callmethod is None:
            callmethod = get_caller_info(1)
        return asyncio.run_in_other_loop(
            self._get_url_async(o_url, encoding=encoding, headers=headers, data=data, method=method,
                                cookies=cookies, cookie_jar=cookie_jar, verify=verify,
                                allow_cache=allow_cache, callmethod=callmethod, stream=stream), loop=self.loop)

    async def get_url_async(self, o_url, encoding=None, headers=None, data=None, method=None, cookies=None,
                            cookie_jar=None, verify=None, allow_cache=True, callmethod=None, stream=False):
        self.init()
        if callmethod is None:
            callmethod = get_caller_info(1)
        return await asyncio.async_run_in_loop(
            self._get_url_async(o_url, encoding=encoding, headers=headers, data=data, method=method,
                                cookies=cookies, cookie_jar=cookie_jar, verify=verify,
                                allow_cache=allow_cache, callmethod=callmethod, stream=stream),
            loop=self.loop, cancel_connect=False)

    async def _get_url_async(self, o_url, encoding=None, headers=None, data=None, method=None, cookies=None,
                             cookie_jar=None, verify=None, allow_cache=True, callmethod=None, stream=False):
        self.init()
        # if encoding is None:
        #     encoding = 'utf-8'
        if verify is None:
            verify = self.ssl_verify
        if callmethod is None:
            callmethod = get_caller_info(1)
        if data:
            allow_cache = False
        else:
            data = None
        if cookie_jar is not None:
            allow_cache = False
        if stream:
            allow_cache = False
        url_json_dict = {"o_url": o_url}
        if encoding is not None:
            url_json_dict["encoding"] = encoding
        if headers is not None:
            url_json_dict["headers"] = headers
        if method is not None:
            url_json_dict["method"] = method
        if cookies is not None:
            url_json_dict["cookies"] = cookies
        if cookie_jar is not None:
            url_json_dict["cookie_jar"] = str(cookie_jar)
        if len(url_json_dict) == 1:
            url_json = o_url
        else:
            url_json = json.dumps(url_json_dict, sort_keys=False, ensure_ascii=False)
        url_json_dict["encoding"] = encoding
        url_json_dict["headers"] = headers
        url_json_dict["method"] = method
        url_json_dict["cookies"] = cookies
        url_json_dict["cookie_jar"] = cookie_jar
        url_json_dict["data"] = data
        url_json_dict["verify"] = verify
        url_json_dict["stream"] = stream

        async with self._get_url_key_lock(url_json, allow_cache):
            result = None
            if allow_cache:
                if url_json in self.url_cache:
                    result = self.url_cache[url_json]
                    logging.debug(callmethod + "cache get:" + url_json)
                else:
                    logging.debug(callmethod + "normal get:" + url_json)
            else:
                logging.debug(callmethod + "nocache get:" + url_json)
            for i in range(0, self.check_response_retry_num + 1):
                if result is None:
                    result = await self.pool_get_url.apply(
                        asyncio.async_run_func_or_co(self.impl.get_url, url_json=url_json,
                                                     url_json_dict=url_json_dict,
                                                     callmethod=callmethod))
                    if result is None:
                        return None
                cr = self._check_response(result)
                if cr is None:
                    break
                else:
                    logging.warning(callmethod + 'request %s check_response by %s fail! retry %d in %d.'
                                    % (o_url, cr, i + 1, self.check_response_retry_num))
                    self.force_flush_cache(result, callmethod)
                    result = None
            if allow_cache and result and result.status_code == 200:
                self.url_cache[url_json] = result
            if result is None:
                return None
            return result.get_wrapper()

    def _check_response(self, response: GetUrlResponse, func=None):
        check_response_func_list = self.check_response_func_list.copy()
        if func is not None:
            check_response_func_list.append(func)
        for func in check_response_func_list:
            t = func(response)
            if not t:
                return func
        return None

    def reg_check_response_func(self, func):
        if func not in self.check_response_func_list:
            logging.debug("reg %s to %s" % (func, self))
            self.check_response_func_list.append(func)
        return func


get_url_service = GetUrlService()

__all__ = ["GetUrlService", "get_url_service", "EMPTY_COOKIES"]
