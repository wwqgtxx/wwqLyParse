#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
from .base import *
from ..selectors import DefaultSelector
from ..concurrent_futures import ThreadPoolExecutor
import logging
import weakref
import aiohttp
import asyncio
import threading


class TCPConnector(aiohttp.TCPConnector):
    _logger = logging.getLogger("aiohttp")

    def _get(self, key):
        conn = super(TCPConnector, self)._get(key)
        url = "%s://%s:%d" % ("https" if key.is_ssl else "http", key.host, key.port)
        if conn is None:
            self._logger.debug("create new connection for %s" % url)
        else:
            self._logger.debug("reused connection for %s" % url)
        return conn


class AioHttpGetUrlStreamReader(GetUrlStreamReader):
    def __init__(self, resp: aiohttp.ClientResponse, loop: asyncio.AbstractEventLoop):
        self.resp = resp
        self.loop = loop

    def _read(self, size):
        return asyncio.run_coroutine_threadsafe(self.resp.content.read(size), loop=self.loop).result()

    def __enter__(self):
        asyncio.run_coroutine_threadsafe(self.resp.__aenter__(), loop=self.loop).result()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        asyncio.run_coroutine_threadsafe(self.resp.__aexit__(exc_type, exc_val, exc_tb), loop=self.loop).result()


class AioHttpGetUrlImpl(GetUrlImpl):

    def __init__(self, service):
        super().__init__(service)
        logging.getLogger("chardet").setLevel(logging.WARNING)
        self.common_loop = self._get_async_loop()
        self.common_connector = TCPConnector(limit=GET_URL_PARALLEL_LIMIT, loop=self.common_loop)
        self.common_cookie_jar = aiohttp.CookieJar(loop=self.common_loop)
        self.common_client_timeout = aiohttp.ClientTimeout(sock_connect=GET_URL_CONNECT_TIMEOUT,
                                                           sock_read=GET_URL_RECV_TIMEOUT)
        logging.debug("init %s" % self.common_connector)
        weakref.finalize(self, self.common_connector.close)

    def _get_async_loop(self):
        loop = asyncio.SelectorEventLoop(DefaultSelector())
        loop.set_default_executor(ThreadPoolExecutor())

        def _run_forever():
            logging.debug("start loop %s", loop)
            asyncio.set_event_loop(loop)
            loop.run_forever()

        threading.Thread(target=_run_forever, name="GetUrlLoopThread", daemon=True).start()
        return loop

    async def _get_url_aiohttp(self, url_json, o_url, encoding, headers, data, method, callmethod, verify, cookies,
                               retry_num, stream, connector=None, cookie_jar=None):
        async def __get_url_aiohttp(session: aiohttp.ClientSession):
            for i in range(0, retry_num + 1):
                try:
                    resp = await session.request(method=method if method else "GET", url=o_url,
                                                 headers=headers if headers else self.service.fake_headers, data=data,
                                                 timeout=self.common_client_timeout,
                                                 ssl=None if verify else False,
                                                 proxy=self.service.http_proxy or None)
                    result = GetUrlResponse(headers=dict(resp.headers),
                                            url=str(resp.url),
                                            status_code=resp.status)
                    if stream:
                        result.content = AioHttpGetUrlStreamReader(resp, self.common_loop)
                    else:
                        async with resp as resp:
                            if encoding == "raw":
                                result.content = await resp.read()
                            else:
                                result.content = await resp.text(encoding=encoding)
                    return result
                except asyncio.TimeoutError:
                    if i == retry_num:
                        raise
                    logging.warning(
                        callmethod + 'request %s TimeoutError! retry %d in %d.' % (o_url, i + 1, retry_num))
                except aiohttp.ClientSSLError:
                    logging.exception(
                        callmethod + 'request %s ClientSSLError' % o_url)
                    return
                except aiohttp.ClientError:
                    if i == retry_num:
                        raise
                    logging.warning(
                        callmethod + 'request %s ClientError! retry %d in %d.' % (o_url, i + 1, retry_num))
                except:
                    logging.exception(callmethod + "get url " + url_json + "fail")

        if connector is None:
            connector = self.common_connector
        if cookie_jar is None:
            cookie_jar = self.common_cookie_jar
        if cookies is EMPTY_COOKIES:
            cookies = {}
        if cookies is not None:
            cookie_jar = None
        try:
            async with aiohttp.ClientSession(connector=connector, connector_owner=False,
                                             cookies=cookies, cookie_jar=cookie_jar) as _session:
                return await __get_url_aiohttp(_session)
        except aiohttp.ClientError as e:
            logging.error(callmethod + 'request %s ClientError! Error message: %s' % (o_url, e))
        except:
            logging.exception(callmethod + "get url " + url_json + "fail")

    def get_url(self, url_json, url_json_dict, callmethod, pool=None):
        retry_num = GET_URL_RETRY_NUM
        future = asyncio.run_coroutine_threadsafe(
            self._get_url_aiohttp(url_json=url_json, callmethod=callmethod, retry_num=retry_num,
                                  **url_json_dict), loop=self.common_loop)
        result = future.result()
        return result
