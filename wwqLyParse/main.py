#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
if __name__ == "__main__":
    # import sys
    #
    # sys.modules["gevent"] = None

    try:
        import gevent
        from gevent import monkey

        monkey.patch_all()
    except Exception:
        gevent = None
    import os
    import sys

    _srcdir = os.path.dirname(os.path.realpath(__file__))
    _filepath = os.path.dirname(sys.argv[0])
    sys.path.insert(0, os.path.join(_filepath, _srcdir))

    print(sys.path)

    del sys
    del os

import sys
import os
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s{%(name)s}%(filename)s[line:%(lineno)d]<%(funcName)s> pid:%(process)d %(threadName)s %(levelname)s : %(message)s',
                    datefmt='%H:%M:%S', stream=sys.stdout)

if __name__ == "__main__":
    if not os.environ.get("NOT_LOGGING", None):
        if gevent:
            logging.info("gevent.monkey.patch_all()")
            logging.info("use gevent.pool")
            logging.info("use %s" % gevent.config.loop)
            logging.info("gevent version: %s" % gevent.__version__)
            try:
                import gevent.libuv.loop
                logging.info(gevent.libuv.loop.get_version())
            except Exception:
                pass
        else:
            logging.info("use simple pool")

try:
    from .common import *
except Exception as e:
    from common import *

if __name__ == "__main__":
    if not os.environ.get("NOT_LOGGING", None):
        if gevent:
            try:
                gevent.config.resolver = 'dnspython'
            except Exception:
                pass
            logging.info("use %s" % gevent.config.resolver)

try:
    from .lib.lib_wwqLyParse import *
except Exception as e:
    from lib.lib_wwqLyParse import *

import re, threading, sys, json, os, time, logging, importlib
from argparse import ArgumentParser
from typing import Dict, Tuple, List

# try:
#     from flask import Flask, request, abort
# except Exception:
#     from .flask import Flask, request, abort
# app = Flask(__name__)

version = {
    'port_version': "0.5.0",
    'type': 'parse',
    'version': '',
    'uuid': '{C35B9DFC-559F-49E2-B80B-79B66EC77471}',
    'filter': [],
    'name': 'WWQ猎影解析插件',
    'author': 'wwqgtxx',
    'copyright': 'wwqgtxx',
    'license': 'GPLV3',
    'home': '',
    'note': ''
}

PARSE_TIMEOUT = 90  # must > 5
CLOSE_TIMEOUT = 10
RECV_TIMEOUT = 60

parser_class_map = import_by_name(module_names=get_all_filename_by_dir('./parsers'), prefix="parsers.",
                                  super_class=Parser)
urlhandle_class_map = import_by_name(module_names=get_all_filename_by_dir('./urlhandles'), prefix="urlhandles.",
                                     super_class=UrlHandle)


def url_handle_parse(input_text, url_handles_name=None):
    start_time = time.time()
    if url_handles_name is not None:
        _url_handle_class_map = import_by_name(class_names=url_handles_name, prefix="urlhandles.",
                                               super_class=UrlHandle)
    else:
        _url_handle_class_map = urlhandle_class_map
    url_handles = new_objects(_url_handle_class_map)
    for url_handle_obj in url_handles:
        for filter_str in url_handle_obj.get_filters():
            if re.match(filter_str, input_text):
                try:
                    logging.debug(url_handle_obj)
                    result = url_handle_obj.url_handle(input_text)
                    if (result is not None) and (result is not ""):
                        input_text = result
                    end_time = time.time()
                    if (end_time - start_time) > PARSE_TIMEOUT / 2:
                        break
                except Exception as e:
                    logging.exception(str(url_handle_obj))
                    # print(e)
                    # import traceback
                    # traceback.print_exc()
    if re.match(r'^(http|https)://', input_text):
        try:
            get_url(input_text)
        except GreenletExit:
            return None
        except Exception:
            logging.exception("get_url for cache")
    end_time = time.time()
    if (end_time - start_time) >= PARSE_TIMEOUT:
        return None
    return input_text


def init_version():
    parsers = new_objects(parser_class_map)
    url_handles = new_objects(urlhandle_class_map)
    for parser in parsers:
        for filter_str in parser.get_filters():
            version['filter'].append(filter_str)
    for url_handle_obj in url_handles:
        for filter_str in url_handle_obj.get_filters():
            version['filter'].append(filter_str)

    with open(get_real_path('./version.txt')) as f:
        ver = f.readline().strip()
        version['version'] = ver

    version['name'] = get_name().decode() + version['version'] + "[Include "
    try:
        version['name'] = version['name'] + parser_class_map["YouGetParser"]().get_version() + "&"
    except:
        logging.warning("YouGetParser version get error")
    try:
        version['name'] = version['name'] + parser_class_map["YKDLParser"]().get_version() + "&"
    except:
        logging.warning("YKDLParser version get error")
    try:
        version['name'] = version['name'] + parser_class_map["AnnieParser"]().get_version() + "&"
    except:
        logging.warning("AnnieParser version get error")
    version['name'] = version['name'] + "]" + " Running on Python %s" % sys.version


def parse_password(input_text, kk):
    if "||" in input_text:
        input_text = str(input_text).split("||")
        kk["password"] = input_text[1]
        input_text = input_text[0]
    return input_text


def get_version():
    return version


def parse(input_text, types=None, parsers_name=None, url_handles_name=None, use_inside=False, *k, **kk):
    if parsers_name is not None:
        _parser_class_map = import_by_name(class_names=parsers_name, prefix="parsers.", super_class=Parser)
    else:
        _parser_class_map = parser_class_map
    parsers = new_objects(_parser_class_map)

    def run(queue, parser, input_text, *k, **kk):
        try:
            logging.debug(parser)
            result = parser.parse(input_text, *k, **kk)
            if type(result) == dict:
                if "error" in result:
                    logging.error(result["error"])
                    return
                if ("data" in result) and (result["data"] is not None) and (result["data"] != []):
                    for data in result['data']:
                        if ('label' in data) and (data['label'] is not None) and (data['label'] != ""):
                            data['label'] = str(data['label']) + "@" + parser.__class__.__name__
                        if ('code' in data) and (data['code'] is not None) and (data['code'] != ""):
                            data['code'] = str(data['code']) + "@" + parser.__class__.__name__
                    q_result = {"result": result, "parser": parser}
                    queue.put(q_result)
            elif type(result) == list:
                queue.put(result)
        except GreenletExit:
            logging.warning("%s timeout exit" % parser)
        except Exception as e:
            logging.exception(str(parser))
            # print(e)
            # import traceback
            # traceback.print_exc()

    input_text = parse_password(input_text, kk)

    input_text = url_handle_parse(input_text, url_handles_name)
    if not input_text:
        return None
    results = []
    t_results = []
    q_results = Queue()
    with WorkerPool() as pool:
        for parser in parsers:
            for filter_str in parser.get_filters():
                if (types is None) or (not parser.get_types()) or (is_in(types, parser.get_types(), strict=False)):
                    if re.search(filter_str, input_text):
                        support = True
                        for un_support in parser.get_un_supports():
                            if re.search(un_support, input_text):
                                support = False
                                break
                        if support:
                            pool.spawn(run, q_results, parser, input_text, *k, **kk)
        pool.join(timeout=PARSE_TIMEOUT)
    while not q_results.empty():
        result = q_results.get()
        if type(result) == dict:
            t_results.append(result)
        if type(result) == list:
            t_results.extend(result)
    if use_inside:
        return t_results
    for t_result in t_results:
        data = t_result["result"]
        try:
            if "sorted" not in data or data["sorted"] != 1:
                data["data"] = sorted(data["data"], key=lambda d: d["label"], reverse=True)
                logging.info("sorted the " + str(t_result["parser"]) + "'s data['data']")
        except:
            pass
        results.append(data)
    return results


def parse_url(input_text, label, min=None, max=None, url_handles_name=None, *k, **kk):
    def run(queue, parser, input_text, label, min, max, *k, **kk):
        try:
            logging.debug(parser)
            result = parser.parse_url(input_text, label, min, max, *k, **kk)
            if (result is not None) and (result != []):
                if "error" in result:
                    logging.error(result["error"])
                    return
                queue.put(result)
        except GreenletExit:
            logging.warning("%s timeout exit" % parser)
        except Exception as e:
            logging.exception(str(parser))

    t_label = label.split("@")
    label = t_label[0]
    parser_name = t_label[1]
    parser_class_map = import_by_name(class_names=[parser_name], prefix="parsers.", super_class=Parser)
    parsers = new_objects(parser_class_map)

    input_text = parse_password(input_text, kk)

    input_text = url_handle_parse(input_text, url_handles_name)
    if not input_text:
        return None
    parser = parsers[0]
    q_results = Queue(1)
    with WorkerPool() as pool:
        pool.spawn(run, q_results, parser, input_text, label, min, max, *k, **kk)
        pool.join(timeout=PARSE_TIMEOUT)
    if not q_results.empty():
        result = q_results.get()
    else:
        result = []
    return result


def debug(text):
    try:
        text = json.dumps({"output": text}, ensure_ascii=False)
    except:
        pass
    info = "\n------------------------------------------------------------\n"
    info += (str(text)).encode('gbk', 'ignore').decode('gbk')
    info += "\n------------------------------------------------------------"
    logging.debug(info)


def close():
    parsers = new_objects(parser_class_map)
    url_handles = new_objects(urlhandle_class_map)

    def exit():
        time.sleep(0.001)
        os._exit(0)

    with WorkerPool(thread_name_prefix="ClosePool") as pool:
        for parser in parsers:
            pool.spawn(parser.close_parser)
        for url_handle_obj in url_handles:
            pool.spawn(url_handle_obj.close_url_handle)
        pool.join(timeout=CLOSE_TIMEOUT)
        pool.spawn(exit)
        pool.join()


# @app.route('/cache/<url>', methods=['POST', 'GET'])
# def cache(url):
#     data = get_http_cache_data(url)
#     if data is not None:
#         return data
#     else:
#         abort(404)

def _handle(data):
    req_data = lib_parse(data)
    req_data = req_data.decode()
    logging.debug("input json:" + req_data)
    data = json.loads(req_data)
    req_url = data["url"]
    req_data = data["data"]
    try:
        result = ""
        if req_url == "close":
            close()
        elif req_url == "GetVersion":
            result = get_version()
        elif req_url == "Parse":
            if req_data is not None:
                j_json = req_data
                logging.debug("load json:" + str(j_json))
                result = parse(j_json["input_text"], j_json["types"], j_json["parsers_name"],
                               j_json["urlhandles_name"])
            else:
                raise Exception("can't get input json")
        elif req_url == "ParseURL":
            if req_data is not None:
                j_json = req_data
                logging.debug("load json:" + str(j_json))
                result = parse_url(j_json["input_text"], j_json["label"], j_json["min"], j_json["max"],
                                   j_json["urlhandles_name"])
            else:
                raise Exception("can't get input json")
    except Exception as e:
        info = traceback.format_exc()
        logging.error(info)
        result = {"type": "error", "error": info}
    result = {"type": "result", "url": req_url, "data": result}
    debug(result)
    j_json = json.dumps(result)
    byte_str = j_json.encode("utf-8")
    byte_str = lib_parse(byte_str)
    return byte_str


def handle(conn_list: list, conn: multiprocessing_connection.Connection, c_send: multiprocessing_connection.Connection):
    try:
        if not conn.closed:
            data = conn.recv_bytes()
            if not data:
                raise EOFError
            logging.debug("parse conn %s" % conn)
            # logging.debug(data)
            result = _handle(data)
            conn.send_bytes(result)
            conn_list.append(conn)
            c_send.send_bytes(b'ok')
    except EOFError:
        logging.debug("conn %s was eof" % conn)
        conn.close()
    except BrokenPipeError:
        logging.debug("conn %s was broken" % conn)
        conn.close()


def _process(conn_list: List[multiprocessing_connection.Connection],
             handle_pool: WorkerPool,
             c_recv: multiprocessing_connection.Connection,
             c_send: multiprocessing_connection.Connection,
             wait=multiprocessing_connection.wait):
    while True:
        try:
            for conn in wait(conn_list):
                if conn == c_recv:
                    c_recv.recv_bytes()
                    continue
                conn_list.remove(conn)
                if not conn.closed:
                    handle_pool.spawn(handle, conn_list, conn, c_send)
                else:
                    logging.debug("conn %s was closed" % conn)
        except:
            logging.exception("error")


def _run(address):
    with WorkerPool(thread_name_prefix="HandlePool") as handle_pool:
        with multiprocessing_connection.Listener(address, authkey=get_uuid()) as listener:
            c_recv, c_send = multiprocessing_connection.Pipe(False)
            conn_list = list()
            conn_list.append(c_recv)
            handle_pool.spawn(_process, conn_list, handle_pool, c_recv, c_send)
            while True:
                try:
                    conn = listener.accept()
                    logging.debug("get a new conn %s" % conn)
                    conn_list.append(conn)
                    c_send.send_bytes(b'ok')
                except:
                    logging.exception("error")


def run(pipe):
    address = r'\\.\pipe\%s@%s' % (pipe, version['version'])
    logging.info("listen address:'%s'" % address)
    _run(address)


def arg_parser():
    parser = ArgumentParser(description=version["name"])
    parser.add_argument('--pipe', type=str, default='wwqLyParse', help="set PipeName")
    # parser.add_argument('--host', type=str, default='127.0.0.1', help="set listening ip")
    # parser.add_argument('-p', '--port', type=int, default=5000, help="set listening port")
    parser.add_argument('-t', '--timeout', type=int, default=PARSE_TIMEOUT,
                        help="set parse timeout seconds, default 60s")
    parser.add_argument('--close_timeout', type=int, default=CLOSE_TIMEOUT,
                        help="set close timeout seconds, default 10s")

    parser.add_argument('-d', '--debug', type=str, default=None, help="debug a url")
    parser.add_argument('-f', '--format', type=str, default=None,
                        help="set format for Parse method")
    parser.add_argument('--parser', type=str, nargs='*', default=None,
                        help="set parser for Parse method, you should input a parser name, else will use all parsers")
    parser.add_argument('--types', type=str, nargs='*', default=None,
                        help="set types for Parse method, you should input a type name, else will use all type")
    parser.add_argument('-l', '--label', type=str, default=None,
                        help="debug a url with ParseURL method, you should input the label name")

    args = parser.parse_args()
    return args


def main(debugstr=None, parsers_name=None, types=None, label=None, pipe="wwqLyParse", timeout=PARSE_TIMEOUT,
         close_timeout=CLOSE_TIMEOUT):
    logging.debug("\n------------------------------------------------------------\n")
    global PARSE_TIMEOUT
    PARSE_TIMEOUT = timeout
    global CLOSE_TIMEOUT
    CLOSE_TIMEOUT = close_timeout
    if debugstr is not None:
        if label is None:
            debug(parse(debugstr, types=types, parsers_name=parsers_name))
        else:
            debug(parse_url(debugstr, label))
    else:
        run(pipe)


if __name__ == '__main__':
    init_version()
    args = arg_parser()
    globals()["args"] = args
    main(args.debug, args.parser, args.types, args.label, args.pipe, args.timeout, args.close_timeout)

    # main()
