#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>

import sys
import logging
import functools
import threading
import weakref
import uuid
import base64
import asyncio
import urllib.request, json, re, gzip, socket, urllib.error, http.client, urllib

requests = None
aiohttp = None

try:
    import requests
    import requests.adapters
except:
    pass

# if sys.version_info[0:2] >= (3, 6):
try:
    import aiohttp
except:
    pass

from .workerpool import *
from .selectors import DefaultSelector
from .lru_cache import LRUCache
from .key_lock import KeyLockDict, FUCK_KEY_LOCK
from .connection_server import ConnectionServer
from .utils import get_caller_info

URL_CACHE_MAX = 10000
URL_CACHE_TIMEOUT = 6 * 60 * 60
URL_CACHE_POOL = 50
URL_RETRY_NUM = 3

FAKE_HEADERS = {
    'Connection': 'keep-alive',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) ' +
                  'Chrome/53.0.2785.104 Safari/537.36 Core/1.53.2669.400 QQBrowser/9.6.10990.400'
}


class GetUrlService(object):

    def __init__(self):
        self.url_cache = LRUCache(size=URL_CACHE_MAX, timeout=URL_CACHE_TIMEOUT)
        self.url_key_lock = KeyLockDict()
        self.pool_get_url = WorkerPool(URL_CACHE_POOL + 1, thread_name_prefix="GetUrlPool")
        self.fake_headers = FAKE_HEADERS.copy()
        self.address_get_url = r'\\.\pipe\%s-%s-%s' % ("wwqLyParse", 'get_url', uuid.uuid4().hex)
        self.common_loop = None
        self.common_connector = None
        self.common_cookie_jar = None
        self.common_client_timeout = None
        self.common_session = None
        self.inited = False

    def init(self):
        if not self.inited:
            logging.getLogger("chardet").setLevel(logging.WARNING)
            if aiohttp:
                self.common_loop = self._get_async_loop()
                from .aiohttp import TCPConnector
                self.common_connector = TCPConnector(limit=URL_CACHE_POOL, loop=self.common_loop)
                self.common_cookie_jar = aiohttp.CookieJar(loop=self.common_loop)
                self.common_client_timeout = aiohttp.ClientTimeout(total=1 * 60)
                logging.debug("init %s" % self.common_connector)
                weakref.finalize(self, self.common_connector.close)
            elif requests:
                self.common_session = self._get_session()
            address_get_url = self.address_get_url
            logging.info("listen address:'%s'" % address_get_url)
            cs = ConnectionServer(address_get_url, self._handle)
            self.pool_get_url.spawn(cs.run)
            self.inited = True

    def _handle(self, data):
        args = json.loads(data.decode("utf-8"))
        url = args.get("url")
        data = args.get("data")
        encoding = args.get("encoding", args.get("charset"))
        headers = args.get("headers")
        cookies = args.get("cookies")
        method = args.get("method")
        if encoding == 'ignore':
            encoding = 'raw'
        result = self.get_url(o_url=url, encoding=encoding, headers=headers, data=data, cookies=cookies, method=method,
                              allow_cache=False)
        if encoding == 'raw':
            return result
        if encoding == "response":
            return json.dumps(result).encode("utf-8")
        return result.encode("utf-8")

    def _get_async_loop(self):
        loop = asyncio.SelectorEventLoop(DefaultSelector())

        def _run_forever():
            logging.debug("start loop %s", loop)
            asyncio.set_event_loop(loop)
            loop.run_forever()

        threading.Thread(target=_run_forever, name="GetUrlLoopThread", daemon=True).start()
        return loop

    def _get_session(self, size=50, retry=URL_RETRY_NUM):
        session = requests.Session()

        session.mount("http://",
                      requests.adapters.HTTPAdapter(pool_connections=size, pool_maxsize=size,
                                                    max_retries=retry))
        session.mount('https://',
                      requests.adapters.HTTPAdapter(pool_connections=size, pool_maxsize=size,
                                                    max_retries=retry))
        return session

    def _get_url_key_lock(self, url_json, allow_cache):
        if allow_cache:
            return self.url_key_lock[url_json]
        else:
            return FUCK_KEY_LOCK

    def _get_url_urllib(self, url_json, o_url, encoding, headers, data, method, callmethod, verify, cookies, use_pool):
        try:
            # url 包含中文时 parse.quote_from_bytes(o_url.encode('utf-8'), ':/&%?=+')
            logging.debug("get %s", o_url)
            req = urllib.request.Request(o_url, headers=headers if headers else self.fake_headers, data=data,
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
                        "data": base64.b64encode(data).decode(),
                        "headers": dict(headers),
                        "url": str(response.geturl())
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

    def _get_url_requests(self, url_json, o_url, encoding, headers, data, method, callmethod, verify, cookies,
                          use_pool, session):
        try:
            resp = session.request(method=method if method else "GET", url=o_url,
                                   headers=headers if headers else self.fake_headers, data=data, cookies=cookies,
                                   verify=verify)
            if encoding == "response":
                html_text = {
                    "data": base64.b64encode(resp.content).decode(),
                    "headers": dict(resp.headers),
                    "url": str(resp.url)
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

    async def _get_url_aiohttp(self, url_json, o_url, encoding, headers, data, method, callmethod, verify, cookies,
                               retry_num, connector=None, cookie_jar=None):
        async def __get_url_aiohttp(session: aiohttp.ClientSession):
            for i in range(0, retry_num + 1):
                try:
                    async with session.request(method=method if method else "GET", url=o_url,
                                               headers=headers if headers else self.fake_headers, data=data,
                                               timeout=self.common_client_timeout,
                                               ssl=verify) as resp:
                        if encoding == "response":
                            return {
                                "data": base64.b64encode(await resp.read()).decode(),
                                "headers": dict(resp.headers),
                                "url": str(resp.url)
                            }
                        elif encoding == "raw":
                            return await resp.read()
                        else:
                            return await resp.text(encoding=encoding)
                except asyncio.TimeoutError:
                    if i == retry_num:
                        raise
                    logging.warning(
                        callmethod + 'request %s TimeoutError! retry %d in %d.' % (o_url, i + 1, retry_num))
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
        if cookies is not None:
            cookie_jar = None
        try:
            async with aiohttp.ClientSession(connector=connector, connector_owner=False,
                                             cookies=cookies, cookie_jar=cookie_jar) as _session:
                return await __get_url_aiohttp(_session)
        except aiohttp.ClientError as e:
            logging.error(callmethod + 'request %s ClientError! Error message: %s' % (o_url, e))

    def get_url(self, o_url, encoding=None, headers=None, data=None, method=None, cookies=None, verify=True,
                allow_cache=True, use_pool=True, pool=None, force_flush_cache=False, callmethod=None):
        self.init()
        # if encoding is None:
        #     encoding = 'utf-8'
        if pool is None:
            pool = self.pool_get_url
        if callmethod is None:
            callmethod = get_caller_info(1)
        url_json_dict = {"o_url": o_url, "encoding": encoding, "headers": headers, "data": data, "method": method,
                         "cookies": cookies, "verify": verify}
        url_json = json.dumps(url_json_dict, sort_keys=False, ensure_ascii=False)

        with self._get_url_key_lock(url_json, allow_cache):
            if force_flush_cache:
                self.url_cache.pop(url_json, None)
                logging.debug(callmethod + "force_flush_cache get:" + url_json)
            if allow_cache:
                if url_json in self.url_cache:
                    html_text = self.url_cache[url_json]
                    logging.debug(callmethod + "cache get:" + url_json)
                    return html_text
                logging.debug(callmethod + "normal get:" + url_json)
            else:
                logging.debug(callmethod + "nocache get:" + url_json)
                # use_pool = False
            retry_num = URL_RETRY_NUM

            if aiohttp:
                future = asyncio.run_coroutine_threadsafe(
                    self._get_url_aiohttp(url_json=url_json, callmethod=callmethod, retry_num=retry_num,
                                          **url_json_dict), loop=self.common_loop)
                result = future.result()
                if allow_cache and result:
                    self.url_cache[url_json] = result
                return result

            if requests:
                fn = functools.partial(self._get_url_requests, url_json=url_json, callmethod=callmethod,
                                       use_pool=use_pool, session=self.common_session,
                                       **url_json_dict)
                retry_num = 1
            else:
                fn = functools.partial(self._get_url_urllib, url_json=url_json, callmethod=callmethod,
                                       use_pool=use_pool,
                                       **url_json_dict)

            for i in range(retry_num):
                if use_pool:
                    result = pool.apply(fn)
                else:
                    result = fn()
                if result is not None:
                    if allow_cache and result:
                        self.url_cache[url_json] = result
                    return result
            return None


get_url_service = GetUrlService()
get_url = get_url_service.get_url
