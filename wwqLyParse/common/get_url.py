#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>

from .workerpool import *

try:
    import requests
    import requests.adapters
except:
    requests = None

import logging
import functools
import urllib.request, json, re, gzip, socket, urllib.error, http.client, urllib

from .lru_cache import LRUCache
from .utils import get_caller_info

URL_CACHE_MAX = 10000
URL_CACHE_TIMEOUT = 6 * 60 * 60
URL_CACHE_POOL = 50
url_cache = LRUCache(size=URL_CACHE_MAX, timeout=URL_CACHE_TIMEOUT)

pool_get_url = WorkerPool(URL_CACHE_POOL, thread_name_prefix="GetUrlPool")
# pool_clean_url_cache = WorkerPool(1, thread_name_prefix="CleanUrlCache")

fake_headers = {
    'Connection': 'keep-alive',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) ' +
                  'Chrome/53.0.2785.104 Safari/537.36 Core/1.53.2669.400 QQBrowser/9.6.10990.400'
}


class FuckSession(object):
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __enter__(self):
        return None


def get_session(size=50, retry=3):
    if requests:
        session = requests.Session()
        session.mount("http://",
                      requests.adapters.HTTPAdapter(pool_connections=size, pool_maxsize=size, max_retries=retry))
        session.mount('https://',
                      requests.adapters.HTTPAdapter(pool_connections=size, pool_maxsize=size, max_retries=retry))
        return session
    else:
        return FuckSession()


if requests:
    common_session = get_session()
else:
    common_session = None


def get_url(o_url, encoding='utf-8', headers=None, data=None, method=None, cookies=None, verify=True, allow_cache=True,
            use_pool=True, pool=pool_get_url, session=common_session):
    def _get_url(url_json, o_url, encoding, headers, data, method, allowCache, callmethod, use_pool):
        try:
            html_text = None
            if requests and session:
                try:
                    req = requests.Request(method=method if method else "GET", url=o_url,
                                           headers=headers if headers else fake_headers, data=data, cookies=cookies)
                    prepped = req.prepare()
                    resp = session.send(prepped, verify=verify)
                    if encoding == "raw":
                        html_text = resp.content
                    else:
                        resp.encoding = encoding
                        html_text = resp.text
                        if o_url.startswith("http://") and re.match(r'http://\d+\.\d+\.\d+\.\d+:89/cookie/flash.js',
                                                                    html_text):
                            logging.warning("get 'cookie/flash.js' in html ,retry")
                            return _get_url(url_json, o_url, encoding, headers, data, method, allowCache, callmethod,
                                            use_pool)
                except requests.exceptions.RequestException as e:
                    logging.warning(callmethod + 'requests error %s' % e)

            else:
                # url 包含中文时 parse.quote_from_bytes(o_url.encode('utf-8'), ':/&%?=+')
                req = urllib.request.Request(o_url, headers=headers if headers else {}, data=data, method=method)
                with urllib.request.urlopen(req) as response:
                    headers = response.info()
                    cType = headers.get('Content-Type', '')
                    match = re.search('charset\s*=\s*(\w+)', cType)
                    if match:
                        encoding = match.group(1)
                    blob = response.read()
                    if headers.get('Content-Encoding', '') == 'gzip':
                        data = gzip.decompress(blob)
                    else:
                        data = blob
                    if encoding == "raw":
                        html_text = data
                    else:
                        html_text = data.decode(encoding, 'ignore')
            if allowCache and html_text:
                url_cache[url_json] = html_text
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

    callmethod = get_caller_info()
    url_json = {"o_url": o_url, "encoding": encoding, "headers": headers, "data": data, "method": method,
                "cookies": cookies}
    url_json = json.dumps(url_json, sort_keys=True, ensure_ascii=False)
    if allow_cache and session == common_session:
        if url_json in url_cache:
            html_text = url_cache[url_json]
            logging.debug(callmethod + "cache get:" + url_json)
            return html_text
        logging.debug(callmethod + "normal get:" + url_json)
    else:
        logging.debug(callmethod + "nocache get:" + url_json)
        # use_pool = False

    if requests and session:
        retry_num = 1
    else:
        retry_num = 10

    fn = functools.partial(_get_url, url_json, o_url, encoding, headers, data, method, allow_cache, callmethod,
                           use_pool)

    for i in range(retry_num):
        if use_pool:
            result = pool.apply(fn)
        else:
            result = fn()
        if result is not None:
            return result
    return None
