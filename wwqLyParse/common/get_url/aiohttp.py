#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
from .base import *
import logging
import weakref
import aiohttp


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


class AioHttpGetUrlStreamReader(GetUrlStreamReaderAsync):
    decoded_encoding = GetUrlStreamReaderAsync.decoded_encoding + ['br']

    def __init__(self, resp: aiohttp.ClientResponse, loop: asyncio.AbstractEventLoop):
        super().__init__(loop)
        self.resp = resp

    async def _read_async(self, size):
        return await asyncio.async_run_in_loop(self.resp.content.read(size), loop=self.loop)

    async def __aenter__(self):
        await asyncio.async_run_in_loop(self.resp.__aenter__(), loop=self.loop)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await asyncio.async_run_in_loop(self.resp.__aexit__(exc_type, exc_val, exc_tb), loop=self.loop)


async def __close_connector(connector: TCPConnector):
    logging.debug("close %s" % connector)
    await connector.close()


def _close_connector(loop: asyncio.AbstractEventLoop, connector: TCPConnector):
    try:
        asyncio.run_coroutine_threadsafe(__close_connector(connector), loop).result(1)
    except:
        pass


class AioHttpGetUrlImpl(GetUrlImpl):

    def __init__(self, service):
        super().__init__(service)
        logging.getLogger("chardet").setLevel(logging.WARNING)
        self.common_loop = service.loop
        self.common_connector = TCPConnector(limit=GET_URL_PARALLEL_LIMIT, loop=self.common_loop)
        self.common_cookie_jar = self.new_cookie_jar()
        self.common_client_timeout = aiohttp.ClientTimeout(sock_connect=GET_URL_CONNECT_TIMEOUT,
                                                           sock_read=GET_URL_RECV_TIMEOUT)
        logging.debug("init %s" % self.common_connector)
        weakref.finalize(self, _close_connector, self.common_loop, self.common_connector)

    def new_cookie_jar(self):
        return aiohttp.CookieJar(loop=self.common_loop)

    async def _get_url_aiohttp(self, url_json, o_url, encoding, headers, data, method, callmethod, verify,
                               cookies, cookie_jar, retry_num, stream, connector=None):
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
                                            status_code=resp.status,
                                            url_json=url_json)
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
            cookie_jar = self.new_cookie_jar()
        try:
            async with aiohttp.ClientSession(connector=connector, connector_owner=False,
                                             cookies=cookies, cookie_jar=cookie_jar) as _session:
                return await __get_url_aiohttp(_session)
        except aiohttp.ClientError as e:
            logging.error(callmethod + 'request %s ClientError! Error message: %s' % (o_url, e))
        except:
            logging.exception(callmethod + "get url " + url_json + "fail")

    async def get_url(self, url_json, url_json_dict, callmethod):
        return await self._get_url_aiohttp(url_json=url_json, callmethod=callmethod, retry_num=GET_URL_RETRY_NUM,
                                           **url_json_dict)
