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
        self.common_session = self._get_session()

    def _get_session(self, size=50, retry=URL_RETRY_NUM):
        session = requests.Session()

        session.mount("http://",
                      requests.adapters.HTTPAdapter(pool_connections=size, pool_maxsize=size,
                                                    max_retries=retry))
        session.mount('https://',
                      requests.adapters.HTTPAdapter(pool_connections=size, pool_maxsize=size,
                                                    max_retries=retry))
        if self.service.http_proxy:
            session.proxies = {
                "http": self.service.http_proxy,
                "https": self.service.http_proxy,
            }
        return session

    def _get_url_requests(self, url_json, o_url, encoding, headers, data, method, callmethod, verify, cookies,
                          use_pool, session):
        try:
            resp = session.request(method=method if method else "GET", url=o_url,
                                   headers=headers if headers else self.service.fake_headers, data=data,
                                   cookies=cookies,
                                   verify=verify)
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
                               use_pool=pool is not None, session=self.common_session,
                               **url_json_dict)
        if pool is not None:
            result = pool.apply(fn)
        else:
            result = fn()
        return result
