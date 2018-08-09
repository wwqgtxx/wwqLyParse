#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>

URL_CACHE_MAX = 10000
URL_CACHE_TIMEOUT = 1 * 60 * 60
GET_URL_PARALLEL_LIMIT = 50
GET_URL_RETRY_NUM = 3
GET_URL_CONNECT_TIMEOUT = 3
GET_URL_RECV_TIMEOUT = 30

FAKE_HEADERS = {
    'Connection': 'keep-alive',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) ' +
                  'Chrome/53.0.2785.104 Safari/537.36 Core/1.53.2669.400 QQBrowser/9.6.10990.400'
}

EMPTY_COOKIES = "!!!EMPTY_COOKIES!!!"


class GetUrlImpl(object):
    def __init__(self, service):
        self.service = service

    def get_url(self, url_json, url_json_dict, callmethod, pool=None):
        raise NotImplementedError


class GetUrlStreamReader(object):
    decoded_encoding = ['gzip', 'deflate']

    def read(self, size=4096):
        try:
            return self._read(size)
        except Exception as e:
            raise GetUrlStreamReadError() from e

    def _read(self, size):
        raise NotImplementedError

    def __enter__(self):
        raise NotImplementedError

    def __exit__(self, exc_type, exc_val, exc_tb):
        raise NotImplementedError


class GetUrlStreamReadError(ConnectionError):
    pass


class GetUrlResponse(object):
    def __init__(self, headers=None, url=None, status_code=None, content=None):
        self.headers = headers
        self.url = url
        self.status_code = status_code
        self.content = content
