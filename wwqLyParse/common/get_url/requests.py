#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
from .base import *
from ..workerpool import *
import warnings
import logging
import functools
import urllib3
import requests
import requests.adapters


class RequestsGetUrlStreamReader(GetUrlStreamReader):
    def __init__(self, resp: requests.Response):
        self.resp = resp
        self.raw = self.resp.raw  # type:urllib3.HTTPResponse

    def _read(self, size):
        return self.raw.read(size, decode_content=True)

    def __enter__(self):
        self.resp.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.resp.__exit__(exc_type, exc_val, exc_tb)


class RequestsGetUrlImpl(GetUrlImpl):
    def __init__(self, service):
        super().__init__(service)
        warnings.filterwarnings("ignore", module="urllib3")
        logging.getLogger("chardet").setLevel(logging.WARNING)
        self.common_http_adapter = self._get_http_adapter()
        self.common_session = self._get_session()
        self.common_timeout = (GET_URL_CONNECT_TIMEOUT, GET_URL_RECV_TIMEOUT)

    def _get_http_adapter(self, size=GET_URL_PARALLEL_LIMIT, retry=GET_URL_RETRY_NUM):
        return requests.adapters.HTTPAdapter(pool_connections=size,
                                             pool_maxsize=size,
                                             max_retries=retry)

    def _get_session(self, use_common_http_adapter=True):
        session = requests.Session()

        http_adapter = self.common_http_adapter if use_common_http_adapter else self._get_http_adapter()
        session.mount("http://", http_adapter)
        session.mount('https://', http_adapter)
        if self.service.http_proxy:
            session.proxies = {
                "http": self.service.http_proxy,
                "https": self.service.http_proxy,
            }
        return session

    def _get_url_requests(self, url_json, o_url, encoding, headers, data, method, callmethod, verify, cookies,
                          use_pool, stream):
        try:
            if cookies is EMPTY_COOKIES:
                cookies = {}
                session = self._get_session()
            else:
                session = self.common_session
            resp = session.request(method=method if method else "GET", url=o_url,
                                   headers=headers if headers else self.service.fake_headers, data=data,
                                   cookies=cookies,
                                   verify=verify,
                                   stream=True,
                                   timeout=self.common_timeout)
            result = GetUrlResponse(headers=dict(resp.headers),
                                    url=str(resp.url),
                                    status_code=resp.status_code)
            if stream:
                result.content = RequestsGetUrlStreamReader(resp)
            else:
                with resp as resp:
                    if encoding == "raw":
                        result.content = resp.content
                    else:
                        if encoding is not None:
                            resp.encoding = encoding
                        result.content = resp.text
            return result
        except requests.exceptions.RequestException as e:
            logging.warning(callmethod + 'requests error %s' % e)
        except GreenletExit as e:
            if use_pool:
                return None
            else:
                raise e
        except:
            logging.exception(callmethod + "get url " + url_json + "fail")
        return None

    def get_url(self, url_json, url_json_dict, callmethod, pool=None):
        fn = functools.partial(self._get_url_requests, url_json=url_json, callmethod=callmethod,
                               use_pool=pool is not None, **url_json_dict)
        if pool is not None:
            result = pool.apply(fn)
        else:
            result = fn()
        return result
