#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
from .base import *
import logging
import re
import gzip
import socket
import functools
import http.client
import http.cookiejar
import urllib.request
import urllib.error


class UrlLibGetUrlStreamReader(GetUrlStreamReader):
    decoded_encoding = []

    def __init__(self, resp: http.client.HTTPResponse):
        self.resp = resp

    def _read(self, size):
        return self.resp.read(size)

    def __enter__(self):
        self.resp.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.resp.__exit__(exc_type, exc_val, exc_tb)


class UrlLibGetUrlImpl(GetUrlImpl):
    def __init__(self, service):
        super().__init__(service)
        self.common_cookie_jar = self.new_cookie_jar()

    def new_cookie_jar(self):
        return http.cookiejar.CookieJar()

    def _get_opener(self):
        opener = urllib.request.build_opener()
        if self.service.http_proxy:
            proxy_handler = urllib.request.ProxyHandler({
                'http': self.service.http_proxy,
                'https': self.service.http_proxy
            })
            opener.add_handler(proxy_handler)
        return opener

    def _get_url_urllib(self, url_json, o_url, encoding, headers, data, method, callmethod, verify, cookies, cookie_jar,
                        stream):
        try:
            # url 包含中文时 parse.quote_from_bytes(o_url.encode('utf-8'), ':/&%?=+')
            logging.debug("get %s", o_url)
            if cookie_jar is None:
                cookie_jar = self.common_cookie_jar
            if cookies is EMPTY_COOKIES:
                cookies = {}
                cookie_jar = self.new_cookie_jar()
            if cookies:
                for k, v in cookies.items():
                    cookie_item = http.cookiejar.Cookie(
                        version=0, name=k, value=str(v),
                        port=None, port_specified=None,
                        domain='', domain_specified=None, domain_initial_dot=None,
                        path='/', path_specified=None,
                        secure=None,
                        expires=None,
                        discard=None,
                        comment=None,
                        comment_url=None,
                        rest=None,
                        rfc2109=False,
                    )
                    cookie_jar.set_cookie(cookie_item)

            req = urllib.request.Request(o_url, headers=headers if headers else self.service.fake_headers, data=data,
                                         method=method)
            opener = self._get_opener()
            opener.add_handler(urllib.request.HTTPCookieProcessor(cookie_jar))

            resp = opener.open(req)
            result = GetUrlResponse(headers=dict(resp.info()),
                                    url=str(resp.geturl()),
                                    status_code=resp.getcode(),
                                    url_json=url_json)
            if stream:
                result.content = UrlLibGetUrlStreamReader(resp)
            else:
                with resp as response:
                    blob = response.read()
                    if resp.info().get('Content-Encoding', '') == 'gzip':
                        data = gzip.decompress(blob)
                    else:
                        data = blob
                    if encoding == "raw":
                        result.content = data
                    else:
                        if not encoding:
                            match = re.search('charset\s*=\s*(\w+)', resp.info().get('Content-Type', ''))
                            if match:
                                encoding = match.group(1)
                            else:
                                encoding = "utf-8"
                        result.content = data.decode(encoding, 'ignore')
            return result
        except socket.timeout:
            logging.warning(callmethod + 'request attempt timeout')
        except urllib.error.URLError:
            logging.warning(callmethod + 'request attempt URLError')
        except http.client.RemoteDisconnected:
            logging.warning(callmethod + 'request attempt RemoteDisconnected')
        except http.client.IncompleteRead:
            logging.warning(callmethod + 'request attempt IncompleteRead')
        # except Cancelled:
        #     raise
        except:
            logging.exception(callmethod + "get url " + url_json + "fail")
        return None

    def get_url(self, url_json, url_json_dict, callmethod):
        retry_num = GET_URL_RETRY_NUM
        for i in range(retry_num):
            return self._get_url_urllib(url_json=url_json, callmethod=callmethod, **url_json_dict)
