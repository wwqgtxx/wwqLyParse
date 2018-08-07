#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
from .base import *
from ..workerpool import *
import warnings
import logging
import functools
import requests
import requests.adapters


class RequestsGetUrlImpl(GetUrlImplBase):
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
                          use_pool):
        try:
            if cookies is EMPTY_COOKIES:
                cookies = {}
                session = self._get_session()
            else:
                session = self.common_session
            with session.request(method=method if method else "GET", url=o_url,
                                 headers=headers if headers else self.service.fake_headers, data=data,
                                 cookies=cookies,
                                 verify=verify,
                                 timeout=self.common_timeout) as resp:
                if encoding == "response":
                    html_text = {
                        "data": bytes(resp.content),
                        "headers": dict(resp.headers),
                        "url": str(resp.url),
                        "status_code": resp.status_code,
                    }
                elif encoding == "response_without_data":
                    html_text = {
                        "data": None,
                        "headers": dict(resp.headers),
                        "url": str(resp.url),
                        "status_code": resp.status_code,
                    }
                elif encoding == "raw":
                    html_text = resp.content
                else:
                    if encoding is not None:
                        resp.encoding = encoding
                    html_text = resp.text
                return html_text
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
