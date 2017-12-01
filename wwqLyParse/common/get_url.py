#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>

try:
    import gevent
    from gevent.pool import Pool
    from gevent.queue import Queue
    from gevent import joinall

except Exception:
    gevent = None
    from .simplepool import Pool
    from .simplepool import joinall
    from queue import Queue

try:
    import requests

    session = requests.Session()
except:
    requests = None
    session = None

import logging
import urllib.request, json, re, gzip, socket, urllib.error, http.client, urllib

from .lru_cache import LRUCache
from .utils import get_caller_info

URL_CACHE_MAX = 1000
URL_CACHE_TIMEOUT = 6 * 60 * 60
URL_CACHE_POOL = 20
url_cache = LRUCache(URL_CACHE_TIMEOUT)

pool_get_url = Pool(URL_CACHE_POOL)
pool_clean_url_cache = Pool(1)

fake_headers = {
    'Connection': 'keep-alive',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) ' +
                  'Chrome/53.0.2785.104 Safari/537.36 Core/1.53.2669.400 QQBrowser/9.6.10990.400'
}


def get_url(o_url, encoding='utf-8', headers=None, data=None, method=None, allow_cache=True, use_pool=True,
            pool=pool_get_url):
    def _get_url(result_queue, url_json, o_url, encoding, headers, data, method, allowCache, callmethod):
        try:
            if requests and session:
                req = requests.Request(method=method if method else "GET", url=o_url,
                                       headers=headers if headers else fake_headers, data=data)
                prepped = req.prepare()
                resp = session.send(prepped)
                if encoding == "raw":
                    html_text = resp.content
                else:
                    resp.encoding = encoding
                    html_text = resp.text
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
            if allowCache:
                url_cache[url_json] = html_text
            result_queue.put(html_text)
            return
        except socket.timeout:
            logging.warning(callmethod + 'request attempt %s timeout' % str(i + 1))
        except urllib.error.URLError:
            logging.warning(callmethod + 'request attempt %s URLError' % str(i + 1))
        except http.client.RemoteDisconnected:
            logging.warning(callmethod + 'request attempt %s RemoteDisconnected' % str(i + 1))
        except http.client.IncompleteRead:
            logging.warning(callmethod + 'request attempt %s IncompleteRead' % str(i + 1))
        except:
            logging.exception(callmethod + "get url " + url_json + "fail")
        result_queue.put(None)
        return

    callmethod = get_caller_info()
    url_json = {"o_url": o_url, "encoding": encoding, "headers": headers, "data": data, "method": method}
    url_json = json.dumps(url_json, sort_keys=True, ensure_ascii=False)
    if allow_cache:
        if url_json in url_cache:
            html_text = url_cache[url_json]
            logging.debug(callmethod + "cache get:" + url_json)
            return html_text
        logging.debug(callmethod + "normal get:" + url_json)
    else:
        logging.debug(callmethod + "nocache get:" + url_json)
        use_pool = False

    if requests and session:
        retry_num = 1
    else:
        retry_num = 10

    for i in range(retry_num):
        queue = Queue(1)
        if use_pool:
            pool.spawn(_get_url, queue, url_json, o_url, encoding, headers, data, method, allow_cache, callmethod)
        else:
            _get_url(queue, url_json, o_url, encoding, headers, data, method, allow_cache, callmethod)
        result = queue.get()
        if result is not None:
            return result
    return None