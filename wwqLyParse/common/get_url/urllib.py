#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
from .base import *
from ..workerpool import *
import logging
import re
import gzip
import socket
import functools
import http.client
import urllib.request
import urllib.error


class UrlLibGetUrlImpl(GetUrlImplBase):
    def __init__(self, service):
        super().__init__(service)
        if self.service.http_proxy:
            proxy_handler = urllib.request.ProxyHandler({
                'http': self.service.http_proxy,
                'https': self.service.http_proxy
            })
            opener = urllib.request.build_opener(proxy_handler)
            urllib.request.install_opener(opener)

    def _get_url_urllib(self, url_json, o_url, encoding, headers, data, method, callmethod, verify, cookies, use_pool):
        try:
            # url 包含中文时 parse.quote_from_bytes(o_url.encode('utf-8'), ':/&%?=+')
            logging.debug("get %s", o_url)
            req = urllib.request.Request(o_url, headers=headers if headers else self.service.fake_headers, data=data,
                                         method=method)
            with urllib.request.urlopen(req) as response:
                headers = response.info()
                blob = response.read()
                if headers.get('Content-Encoding', '') == 'gzip':
                    data = gzip.decompress(blob)
                else:
                    data = blob
                if encoding == "response":
                    html_text = {
                        "data": bytes(data),
                        "headers": dict(headers),
                        "url": str(response.geturl()),
                        "status_code": response.getcode(),
                    }
                    logging.debug(html_text)
                elif encoding == "response_without_data":
                    html_text = {
                        "data": None,
                        "headers": dict(headers),
                        "url": str(response.geturl()),
                        "status_code": response.getcode(),
                    }
                    logging.debug(html_text)
                elif encoding == "raw":
                    html_text = data
                else:
                    if not encoding:
                        match = re.search('charset\s*=\s*(\w+)', headers.get('Content-Type', ''))
                        if match:
                            encoding = match.group(1)
                        else:
                            encoding = "utf-8"
                    html_text = data.decode(encoding, 'ignore')
            return html_text
        except socket.timeout:
            logging.warning(callmethod + 'request attempt timeout')
        except urllib.error.URLError:
            logging.warning(callmethod + 'request attempt URLError')
        except http.client.RemoteDisconnected:
            logging.warning(callmethod + 'request attempt RemoteDisconnected')
        except http.client.IncompleteRead:
            logging.warning(callmethod + 'request attempt IncompleteRead')
        except GreenletExit as e:
            if use_pool:
                return None
            else:
                raise e
        except:
            logging.exception(callmethod + "get url " + url_json + "fail")
        return None

    def get_url(self, url_json, url_json_dict, callmethod, pool=None):
        retry_num = GET_URL_RETRY_NUM
        fn = functools.partial(self._get_url_urllib, url_json=url_json, callmethod=callmethod,
                               use_pool=pool is not None,
                               **url_json_dict)
        for i in range(retry_num):
            if pool is not None:
                result = pool.apply(fn)
            else:
                result = fn()
            return result
        return None
