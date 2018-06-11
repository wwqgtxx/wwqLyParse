#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>

from .workerpool import *

import sys
import logging
import functools
import threading
import atexit
import urllib.request, json, re, gzip, socket, urllib.error, http.client, urllib

try:
    import requests
    import requests.adapters
except:
    requests = None

aiohttp = None
# if sys.version_info[0:2] >= (3, 6):
try:
    import aiohttp
    import asyncio
except:
    pass

from .lru_cache import LRUCache
from .key_lock import KeyLockDict
from .utils import get_caller_info

URL_CACHE_MAX = 10000
URL_CACHE_TIMEOUT = 6 * 60 * 60
URL_CACHE_POOL = 50
URL_RETRY_NUM = 3
url_cache = LRUCache(size=URL_CACHE_MAX, timeout=URL_CACHE_TIMEOUT)
get_url_key_lock = KeyLockDict()

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

common_loop = None
common_connector = None
common_cookie_jar = None
common_client_timeout = None
common_session = None

if aiohttp:
    common_loop = asyncio.SelectorEventLoop()


    def _run_forever():
        asyncio.set_event_loop(common_loop)
        common_loop.run_forever()


    threading.Thread(target=_run_forever, name="GetUrlLoopThread", daemon=True).start()
    common_connector = aiohttp.TCPConnector(limit=URL_CACHE_POOL, loop=common_loop)
    common_cookie_jar = aiohttp.CookieJar(loop=common_loop)
    common_client_timeout = aiohttp.ClientTimeout(total=0.01)
    logging.debug("init %s" % common_connector)
    atexit.register(common_connector.close)
    del _run_forever
elif requests:
    def _get_session(size=50, retry=URL_RETRY_NUM):
        session = requests.Session()

        session.mount("http://",
                      requests.adapters.HTTPAdapter(pool_connections=size, pool_maxsize=size, max_retries=retry))
        session.mount('https://',
                      requests.adapters.HTTPAdapter(pool_connections=size, pool_maxsize=size, max_retries=retry))
        return session


    common_session = _get_session()
    del _get_session


def get_url(o_url, encoding='utf-8', headers=None, data=None, method=None, cookies=None, verify=True, allow_cache=True,
            use_pool=True, pool=pool_get_url):
    def _get_url_urllib(url_json, o_url, encoding, headers, data, method, callmethod, use_pool):
        try:
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

    def _get_url_requests(url_json, o_url, encoding, headers, data, method, callmethod, use_pool, session):
        try:
            resp = session.request(method=method if method else "GET", url=o_url,
                                   headers=headers if headers else fake_headers, data=data, cookies=cookies,
                                   verify=verify)
            if encoding == "raw":
                html_text = resp.content
            else:
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

    async def _get_url_aiohttp(url_json, o_url, encoding, headers, data, method, callmethod, connector, cookie_jar,
                               retry_num):
        async def __get_url_aiohttp(session: aiohttp.ClientSession):
            for i in range(0, retry_num + 1):
                try:
                    async with session.request(method=method if method else "GET", url=o_url,
                                               headers=headers if headers else fake_headers, data=data,
                                               timeout=common_client_timeout,
                                               ssl=verify) as resp:
                        if encoding == "raw":
                            return await resp.read()
                        else:
                            return await resp.text(encoding=encoding)
                except asyncio.TimeoutError:
                    if i == retry_num:
                        raise
                    logging.warning(callmethod + 'request %s TimeoutError! retry %d in %d.' % (o_url, i+1, retry_num))
                except aiohttp.ClientError:
                    if i == retry_num:
                        raise
                    logging.warning(callmethod + 'request %s ClientError! retry %d in %d.' % (o_url, i+1, retry_num))
                except:
                    logging.exception(callmethod + "get url " + url_json + "fail")

        try:
            if cookies is not None:
                async with aiohttp.ClientSession(connector=connector, connector_owner=False,
                                                 cookies=cookies) as _session:
                    return await __get_url_aiohttp(_session)
            else:
                async with aiohttp.ClientSession(connector=connector, connector_owner=False,
                                                 cookie_jar=cookie_jar) as _session:
                    return await __get_url_aiohttp(_session)
        except aiohttp.ClientError as e:
            logging.error(callmethod + 'request %s ClientError! Error message: %s' % (o_url, e))

    callmethod = get_caller_info()
    url_json = {"o_url": o_url, "encoding": encoding, "headers": headers, "data": data, "method": method,
                "cookies": cookies}
    url_json = json.dumps(url_json, sort_keys=True, ensure_ascii=False)

    def _do_get():
        if allow_cache:
            if url_json in url_cache:
                html_text = url_cache[url_json]
                logging.debug(callmethod + "cache get:" + url_json)
                return html_text
            logging.debug(callmethod + "normal get:" + url_json)
        else:
            logging.debug(callmethod + "nocache get:" + url_json)
            # use_pool = False
        retry_num = URL_RETRY_NUM

        if aiohttp:
            future = asyncio.run_coroutine_threadsafe(
                _get_url_aiohttp(url_json, o_url, encoding, headers, data, method, callmethod, common_connector,
                                 common_cookie_jar, retry_num), loop=common_loop)
            result = future.result()
            if allow_cache and result:
                url_cache[url_json] = result
            return result

        if requests:
            fn = functools.partial(_get_url_requests, url_json, o_url, encoding, headers, data, method, callmethod,
                                   use_pool, common_session)
            retry_num = 1
        else:
            fn = functools.partial(_get_url_urllib, url_json, o_url, encoding, headers, data, method, callmethod,
                                   use_pool)

        for i in range(retry_num):
            if use_pool:
                result = pool.apply(fn)
            else:
                result = fn()
            if result is not None:
                if allow_cache and result:
                    url_cache[url_json] = result
                return result
        return None

    if allow_cache:
        with get_url_key_lock[url_json]:
            return _do_get()
    else:
        return _do_get()
