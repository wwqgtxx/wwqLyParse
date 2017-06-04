#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
try:
    import gevent
    from gevent import monkey
    from gevent.pool import Pool
    from gevent.queue import Queue
    from gevent import joinall

    monkey.patch_all()
except Exception:
    gevent = None
    from simplepool import Pool
    from simplepool import joinall
    from queue import Queue

import logging
import sys
import os
import uuid

COMMON_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "./__init__.py"))


def get_real_path(abstract_path):
    return os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(COMMON_PATH)), abstract_path))


sys.path.insert(0, get_real_path('./lib/flask_lib'))
sys.path.insert(0, get_real_path('./lib/requests_lib'))

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s{%(name)s}%(filename)s[line:%(lineno)d]<%(funcName)s> pid:%(process)d %(threadName)s %(levelname)s : %(message)s',
                    datefmt='%H:%M:%S', stream=sys.stdout)

if not os.environ.get("NOT_LOGGING", None):
    if gevent:
        logging.info("gevent.monkey.patch_all()")
        logging.info("use gevent.pool")
    else:
        logging.info("use simple pool")

try:
    import requests

    session = requests.Session()
except:
    requests = None
    session = None

import urllib.request, io, os, sys, json, re, gzip, time, socket, math, urllib.error, http.client, gc, threading, \
    urllib, traceback, importlib, glob

urlcache = {}
URLCACHE_MAX = 1000
URLCACHE_POOL = 20

pool_getUrl = Pool(URLCACHE_POOL)
pool_cleanUrlcache = Pool(1)

fake_headers = {
    'Connection': 'keep-alive',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) ' +
                  'Chrome/53.0.2785.104 Safari/537.36 Core/1.53.2669.400 QQBrowser/9.6.10990.400'
}


def getUrl(oUrl, encoding='utf-8', headers=None, data=None, method=None, allowCache=True, usePool=True,
           pool=pool_getUrl):
    def cleanUrlcache():
        global urlcache
        if (len(urlcache) <= URLCACHE_MAX):
            return
        sortedDict = sorted(urlcache.items(), key=lambda d: d[1]["lasttimestap"], reverse=True)
        newDict = {}
        for (k, v) in sortedDict[:int(URLCACHE_MAX - URLCACHE_MAX / 10)]:  # 从数组中取索引start开始到end-1的记录
            newDict[k] = v
        del sortedDict
        del urlcache
        urlcache = newDict
        gc.collect()
        logging.debug("urlcache has been cleaned")

    def _getUrl(result_queue, url_json, oUrl, encoding, headers, data, method, allowCache, callmethod):
        try:
            if requests and session:
                req = requests.Request(method=method if method else "GET", url=oUrl,
                                       headers=headers if headers else fake_headers, data=data)
                prepped = req.prepare()
                resp = session.send(prepped)
                if encoding == "raw":
                    html_text = resp.content
                else:
                    if encoding != 'utf-8':
                        resp.encoding = encoding
                    html_text = resp.text
            else:
                # url 包含中文时 parse.quote_from_bytes(oUrl.encode('utf-8'), ':/&%?=+')
                req = urllib.request.Request(oUrl, headers=headers if headers else {}, data=data, method=method)
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
                urlcache[url_json] = {"html_text": html_text, "lasttimestap": int(time.time())}
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
    url_json = {"oUrl": oUrl, "encoding": encoding, "headers": headers, "data": data, "method": method}
    url_json = json.dumps(url_json, sort_keys=True, ensure_ascii=False)
    if allowCache:
        global urlcache
        global URLCACHE_MAX
        urlcache_temp = urlcache
        if url_json in urlcache_temp:
            item = urlcache_temp[url_json]
            html_text = item["html_text"]
            item["lasttimestap"] = int(time.time())
            logging.debug(callmethod + "cache get:" + url_json)
            if len(urlcache_temp) > URLCACHE_MAX:
                pool_cleanUrlcache.spawn(cleanUrlcache)
            del urlcache_temp
            return html_text
        logging.debug(callmethod + "normal get:" + url_json)
    else:
        logging.debug(callmethod + "nocache get:" + url_json)
        usePool = False

    if requests and session:
        retry_num = 1
    else:
        retry_num = 10

    for i in range(retry_num):
        queue = Queue(1)
        if usePool:
            pool.spawn(_getUrl, queue, url_json, oUrl, encoding, headers, data, method, allowCache, callmethod)
        else:
            _getUrl(queue, url_json, oUrl, encoding, headers, data, method, allowCache, callmethod)
        result = queue.get()
        if result is not None:
            return result
    return None


def call_method_and_save_to_queue(queue, method, args, kwargs):
    queue.put(method(*args, **kwargs))


http_cache_data = dict()


def put_new_http_cache_data(data, suffix="None"):
    name = str(uuid.uuid4()) + suffix
    http_cache_data[name] = data
    return name


def get_http_cache_data(name, need_delete=True):
    if need_delete:
        return http_cache_data.pop(name, None)
    else:
        return http_cache_data.get(name, None)


def get_http_cache_data_url(name):
    if "args" in globals():
        args = globals()["args"]
        host = args.host
        port = args.port
    else:
        host = "127.0.0.1"
        port = "5000"
    return "http://%s:%s/cache/%s" % (host, port, name)


def get_all_filename_by_dir(dir, suffix=".py"):
    list_dirs = os.walk(dir)
    filenames = []
    for dirName, subdirList, fileList in list_dirs:
        for file_name in fileList:
            if file_name[-len(suffix):] == suffix:
                if file_name != "__init__.py":
                    filenames.append(file_name[0:-len(suffix)])
    logging.debug("<%s> has %s" % (dir, str(filenames)))
    return filenames


imported_class_map = {}
imported_module_map = {}


def import_by_name(class_names=None, module_names=None, prefix="", super_class=object, showinfo=True):
    lib_class_map = {}
    if class_names is not None:
        lib_names = class_names
        for lib_name in lib_names:
            if "." in lib_name:
                full_name = prefix + lib_name
                list_lib_name = lib_name.split(".")
                lib_name = list_lib_name[-1]
                module_name = prefix
                module_name += "".join(list_lib_name[0:-1])
            else:
                full_name = prefix + lib_name.lower() + "." + lib_name
                module_name = prefix + lib_name.lower()
            try:
                lib_class_map[lib_name] = imported_class_map[full_name]
            except:
                try:
                    lib_module = importlib.import_module(module_name)
                    lib_class = getattr(lib_module, lib_name)
                    if isinstance(lib_class(), super_class):
                        imported_class_map[full_name] = lib_class
                        lib_class_map[lib_name] = lib_class
                        if showinfo:
                            logging.debug("successful load " + str(lib_class) + " is a instance of " + str(super_class))
                    else:
                        logging.warning(str(lib_class) + " is not a instance of " + str(super_class))
                except:
                    logging.exception("load " + str(lib_name) + " fail")
    elif module_names is not None:
        lib_names = module_names
        for lib_name in lib_names:
            try:
                for item in imported_module_map[prefix + lib_name]:
                    lib_class_map[item["lib_name"]] = item["lib_class"]
            except:
                try:
                    lib_module = importlib.import_module(prefix + lib_name)
                    lib_module_class_names = getattr(lib_module, "__MODULE_CLASS_NAMES__")
                    imported_module_map[prefix + lib_name] = []
                    for lib_module_class_name in lib_module_class_names:
                        try:
                            lib_class = getattr(lib_module, lib_module_class_name)
                            if isinstance(lib_class(), super_class):
                                imported_module_map[prefix + lib_name].append({
                                    "lib_name": lib_class.__name__,
                                    "lib_class": lib_class
                                })
                                imported_class_map[prefix + lib_name + "." + lib_class.__name__] = lib_class
                                lib_class_map[lib_class.__name__] = lib_class
                                if showinfo:
                                    logging.debug(
                                        "successful load " + str(lib_class) + " is a instance of " + str(super_class))
                            else:
                                logging.warning(str(lib_class) + " is not a instance of " + str(super_class))
                        except:
                            logging.exception("load " + str(lib_module_class_name) + " fail")
                except:
                    logging.exception("load " + str(prefix + lib_name) + " fail")
    return lib_class_map


def new_objects(class_map, showinfo=False, *k, **kk):
    _objects = []
    for _class in class_map.values():
        try:
            _object = _class(*k, **kk)
            _objects.append(_object)
            if showinfo:
                logging.debug("successful new " + str(_object))
        except:
            logging.exception("new " + str(_class) + " fail")
    return _objects


def get_caller_info():
    try:
        fn, lno, func, sinfo = traceback.extract_stack()[-3]
    except ValueError:  # pragma: no cover
        fn, lno, func = "(unknown file)", 0, "(unknown function)"
    try:
        fn = os.path.basename(fn)
    except:
        pass
    callmethod = "<%s:%d %s> " % (fn, lno, func)
    return callmethod


def isin(a, b, strict=True):
    result = False
    if isinstance(a, list):
        for item in a:
            if item in b:
                result = True
            elif strict:
                result = False
    else:
        result = (a in b)
    return result


def url_size(url, headers={}):
    for n in range(3):
        try:
            if headers:
                response = urllib.request.urlopen(urllib.request.Request(url, headers=headers), None)
            else:
                response = urllib.request.urlopen(url)
            size = response.headers['content-length']
            if size != None:
                return int(size)
        except Exception as e:
            error = e
    logging.error(error)
    return -1


def IsOpen(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, int(port)))
        s.shutdown(2)
        logging.info(get_caller_info() + '%d is open' % port)
        return True
    except:
        logging.info(get_caller_info() + '%d is down' % port)
        return False


def gen_bitrate(size_byte, time_s, unit_k=1024):
    if (size_byte <= 0) or (time_s <= 0):
        return '-1'  # can not gen bitrate
    raw_rate = size_byte * 8 / time_s  # bps
    kbps = raw_rate / unit_k
    bitrate = str(round(kbps, 1)) + 'kbps'
    return bitrate


# make a 2.3 number, with given length after .
def num_len(n, l=3):
    t = str(float(n))
    p = t.split('.')
    if l < 1:
        return p[0]
    if len(p[1]) > l:
        p[1] = p[1][:l]
    while len(p[1]) < l:
        p[1] += '0'
    t = ('.').join(p)
    # done
    return t


# byte to size
def byte2size(size_byte, flag_add_byte=False):
    unit_list = [
        'Byte',
        'KB',
        'MB',
        'GB',
        'TB',
        'PB',
        'EB',
    ]

    # check size_byte
    size_byte = int(size_byte)
    if size_byte < 1024:
        return size_byte + unit_list[0]

    # get unit
    unit_i = math.floor(math.log(size_byte, 1024))
    unit = unit_list[unit_i]
    size_n = size_byte / pow(1024, unit_i)

    size_t = num_len(size_n, 2)

    # make final size_str
    size_str = size_t + ' ' + unit

    # check flag
    if flag_add_byte:
        size_str += ' (' + str(size_byte) + ' Byte)'
    # done
    return size_str


def _second_to_time(time_s):
    def _number(raw):
        f = float(raw)
        if int(f) == f:
            return int(f)
        return f

    raw = _number(time_s)
    sec = math.floor(raw)
    ms = raw - sec
    minute = math.floor(sec / 60)
    sec -= minute * 60
    hour = math.floor(minute / 60)
    minute -= hour * 60
    # make text, and add ms
    t = str(minute).zfill(2) + ':' + str(sec).zfill(2) + '.' + str(round(ms * 1e3))
    if hour > 0:  # check add hour
        t = str(hour).zfill(2) + ':' + t
    return t


# DEPRECATED in favor of match1()
def r1(pattern, text):
    m = re.search(pattern, text)
    if m:
        return m.group(1)


def match1(text, *patterns):
    """Scans through a string for substrings matched some patterns (first-subgroups only).

    Args:
        text: A string to be scanned.
        patterns: Arbitrary number of regex patterns.

    Returns:
        When only one pattern is given, returns a string (None if no match found).
        When more than one pattern are given, returns a list of strings ([] if no match found).
    """

    if len(patterns) == 1:
        pattern = patterns[0]
        match = re.search(pattern, text)
        if match:
            return match.group(1)
        else:
            return None
    else:
        ret = []
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                ret.append(match.group(1))
        return ret


def debug(input):
    print(((str(input))).encode('gbk', 'ignore').decode('gbk'))


class Parser(object):
    filters = []
    unsupports = []
    types = []

    def Parse(self, url):
        pass

    def ParseURL(self, url, label, min=None, max=None):
        pass

    def getfilters(self):
        return self.filters

    def getunsupports(self):
        return self.unsupports

    def gettypes(self):
        return self.types

    def closeParser(self):
        return


class UrlHandle():
    filters = []

    def urlHandle(url):
        pass

    def getfilters(self):
        return self.filters

    def closeUrlHandle(self):
        return
