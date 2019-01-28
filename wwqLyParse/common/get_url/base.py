#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
from .. import asyncio

URL_CACHE_MAX = 10000
URL_CACHE_TIMEOUT = 1 * 60 * 60
GET_URL_PARALLEL_LIMIT = 50
GET_URL_RETRY_NUM = 3
GET_URL_CONNECT_TIMEOUT = 3
GET_URL_RECV_TIMEOUT = 30
GET_URL_CHECK_RESP_RETRY_NUM = 1000

FAKE_HEADERS = {
    'Connection': 'keep-alive',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) ' +
                  'Chrome/53.0.2785.104 Safari/537.36 Core/1.53.2669.400 QQBrowser/9.6.10990.400'
}

EMPTY_COOKIES = "!!!EMPTY_COOKIES!!!"


class GetUrlResponse(object):
    def __init__(self, headers=None, url=None, status_code=None, content=None, url_json=None):
        self.headers = headers
        self.url = url
        self.status_code = status_code
        self.content = content
        self.url_json = url_json

    def copy(self):
        new = self.__class__()
        new.__dict__.update(self.__dict__)
        return new

    def get_wrapper(self):
        if isinstance(self.content, str):
            return GetUrlResponseContentStrWrapper(self)
        if isinstance(self.content, bytes):
            return GetUrlResponseContentBytesWrapper(self)
        if isinstance(self.content, GetUrlStreamReader):
            return GetUrlResponseContentStreamReaderWrapper(self)
        return self.copy()


class GetUrlImpl(object):
    def __init__(self, service):
        self.service = service

    def new_cookie_jar(self):
        raise NotImplementedError

    def get_url(self, url_json, url_json_dict, callmethod) -> GetUrlResponse:
        raise NotImplementedError


class GetUrlStreamReader(object):
    decoded_encoding = ['gzip', 'deflate']

    def read(self, size=4096):
        try:
            return self._read(size)
        except Exception as e:
            raise GetUrlStreamReadError() from e

    async def read_async(self, size=4096):
        return await asyncio.async_run_func_or_co(self._read, size)

    def _read(self, size):
        raise NotImplementedError

    def __enter__(self):
        raise NotImplementedError

    def __exit__(self, exc_type, exc_val, exc_tb):
        raise NotImplementedError

    async def __aenter__(self):
        return await asyncio.async_run_func_or_co(self.__enter__)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return await asyncio.async_run_func_or_co(self.__exit__, exc_type, exc_val, exc_tb)


class GetUrlStreamReaderAsync(GetUrlStreamReader):
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop

    def _read(self, size=4096):
        return asyncio.run_in_other_loop(self._read_async(size), self.loop)

    def __enter__(self):
        return asyncio.run_in_other_loop(self.__aenter__(), self.loop)

    def __exit__(self, exc_type, exc_val, exc_tb):
        return asyncio.run_in_other_loop(self.__aexit__(exc_type, exc_val, exc_tb), self.loop)

    async def read_async(self, size=4096):
        try:
            return await self._read_async(size)
        except Exception as e:
            raise GetUrlStreamReadError() from e

    async def _read_async(self, size):
        raise NotImplementedError

    async def __aenter__(self):
        raise NotImplementedError

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        raise NotImplementedError


class GetUrlStreamReadError(ConnectionError):
    pass


class GetUrlResponseContentStreamReaderWrapper(GetUrlStreamReader):
    def __init__(self, response: GetUrlResponse):
        self.headers = response.headers
        self.url = response.url
        self.status_code = response.status_code
        self.content = response.content
        self.url_json = response.url_json

    @property
    def decoded_encoding(self):
        return self.content.decoded_encoding

    @decoded_encoding.setter
    def decoded_encoding(self, value):
        self.content.decoded_encoding = value

    def read(self, size=4096):
        return self.content.read(size)

    def __enter__(self):
        return self.content.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.content.__exit__(exc_type, exc_val, exc_tb)

    async def read_async(self, size=4096):
        return await self.content.read_async(size)

    async def __aenter__(self):
        return await self.content.__aenter()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return await self.content.__aexit__(self, exc_type, exc_val, exc_tb)


class GetUrlResponseContentStrWrapper(str):
    def __new__(cls, response: GetUrlResponse):
        ob = super(GetUrlResponseContentStrWrapper, cls).__new__(cls, response.content)
        ob.headers = response.headers
        ob.url = response.url
        ob.status_code = response.status_code
        ob.content = response.content
        ob.url_json = response.url_json
        return ob


class GetUrlResponseContentBytesWrapper(bytes):
    def __new__(cls, response: GetUrlResponse):
        ob = super(GetUrlResponseContentBytesWrapper, cls).__new__(cls, response.content)
        ob.headers = response.headers
        ob.url = response.url
        ob.status_code = response.status_code
        ob.content = response.content
        ob.url_json = response.url_json
        return ob
