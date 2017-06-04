#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
if __name__ == "__main__":
    import os
    import sys

    _srcdir = os.path.dirname(os.path.realpath(__file__))
    _filepath = os.path.dirname(sys.argv[0])
    sys.path.insert(0, os.path.join(_filepath, _srcdir))

    print(sys.path)
    del sys
    del os

try:
    from .common import *
except Exception as e:
    from common import *

pool = Pool()

import re, threading, sys, json, os, time, logging, importlib
from argparse import ArgumentParser

try:
    from flask import Flask, request, abort
except Exception:
    from .flask import Flask, request, abort
app = Flask(__name__)

version = {
    'port_version': "0.5.0",
    'type': 'parse',
    'version': '0.7.9',
    'uuid': '{C35B9DFC-559F-49E2-B80B-79B66EC77471}',
    'filter': [],
    'name': 'WWQ猎影解析插件',
    'author': 'wwqgtxx',
    'copyright': 'wwqgtxx',
    'license': 'GPLV3',
    'home': '',
    'note': ''
}

PARSE_TIMEOUT = 60
CLOSE_TIMEOUT = 10

parser_class_map = import_by_name(module_names=get_all_filename_by_dir('./parsers'), prefix="parsers.",
                                  super_class=Parser)
urlhandle_class_map = import_by_name(module_names=get_all_filename_by_dir('./urlhandles'), prefix="urlhandles.",
                                     super_class=UrlHandle)


def urlHandle(input_text, urlhandles_name=None):
    if urlhandles_name is not None:
        _urlhandle_class_map = import_by_name(class_names=urlhandles_name, prefix="urlhandles.", super_class=UrlHandle)
    else:
        _urlhandle_class_map = urlhandle_class_map
    urlhandles = new_objects(_urlhandle_class_map)
    for urlhandle in urlhandles:
        for filter in urlhandle.getfilters():
            if re.match(filter, input_text):
                try:
                    logging.debug(urlhandle)
                    result = urlhandle.urlHandle(input_text)
                    if (result is not None) and (result is not ""):
                        input_text = result
                except Exception as e:
                    logging.exception(str(urlhandle))
                    # print(e)
                    # import traceback
                    # traceback.print_exc()
    return input_text


def initVersion():
    parsers = new_objects(parser_class_map)
    urlhandles = new_objects(urlhandle_class_map)
    for parser in parsers:
        for filter in parser.getfilters():
            version['filter'].append(filter)
    for urlhandle in urlhandles:
        for filter in urlhandle.getfilters():
            version['filter'].append(filter)

    version['name'] = version['name'] + version['version'] + "[Include "
    try:
        version['name'] = version['name'] + parser_class_map["YouGetParser"]().getYouGetVersion() + "&"
    except:
        logging.warning("YouGetParser version get error")
    version['name'] = version['name'] + "]" + " Running on Python %s" % sys.version


def GetVersion():
    return version


def Parse(input_text, types=None, parsers_name=None, urlhandles_name=None, *k, **kk):
    if parsers_name is not None:
        _parser_class_map = import_by_name(class_names=parsers_name, prefix="parsers.", super_class=Parser)
    else:
        _parser_class_map = parser_class_map
    parsers = new_objects(_parser_class_map)

    def run(queue, parser, input_text, *k, **kk):
        try:
            logging.debug(parser)
            result = parser.Parse(input_text, *k, **kk)
            if (result is not None) and (result != []):
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
        except Exception as e:
            logging.exception(str(parser))
            # print(e)
            # import traceback
            # traceback.print_exc()

    input_text = urlHandle(input_text, urlhandles_name)
    results = []
    parser_threads = []
    t_results = []
    q_results = Queue()
    for parser in parsers:
        for filter in parser.getfilters():
            if (types is None) or (not parser.gettypes()) or (isin(types, parser.gettypes(), strict=False)):
                if re.search(filter, input_text):
                    support = True
                    for unsupport in parser.getunsupports():
                        if re.search(unsupport, input_text):
                            support = False
                            break
                    if support:
                        parser_threads.append(pool.spawn(run, q_results, parser, input_text, *k, **kk))
    joinall(parser_threads, timeout=PARSE_TIMEOUT)
    while not q_results.empty():
        t_results.append(q_results.get())
    for parser in parsers:
        for t_result in t_results:
            if t_result["parser"] is parser:
                data = t_result["result"]
                try:
                    if "sorted" not in data or data["sorted"] != 1:
                        data["data"] = sorted(data["data"], key=lambda d: d["label"], reverse=True)
                        logging.info("sorted the " + str(t_result["parser"]) + "'s data['data'']")
                except:
                    pass
                results.append(data)
    return results


def ParseURL(input_text, label, min=None, max=None, urlhandles_name=None, *k, **kk):
    def run(queue, parser, input_text, label, min, max, *k, **kk):
        try:
            logging.debug(parser)
            result = parser.ParseURL(input_text, label, min, max, *k, **kk)
            if (result is not None) and (result != []):
                if "error" in result:
                    logging.error(result["error"])
                    return
                queue.put(result)
        except Exception as e:
            logging.exception(str(parser))

    t_label = label.split("@")
    label = t_label[0]
    parser_name = t_label[1]
    parser_class_map = import_by_name(class_names=[parser_name], prefix="parsers.", super_class=Parser)
    parsers = new_objects(parser_class_map)

    input_text = urlHandle(input_text, urlhandles_name)
    parser = parsers[0]
    q_results = Queue(1)
    parser_thread = pool.spawn(run, q_results, parser, input_text, label, min, max, *k, **kk)
    joinall([parser_thread], timeout=PARSE_TIMEOUT)
    if not q_results.empty():
        result = q_results.get()
    else:
        result = []
    return result


def debug(input):
    info = "\n------------------------------------------------------------\n"
    info += ((str(input))).encode('gbk', 'ignore').decode('gbk')
    info += "\n------------------------------------------------------------"
    logging.debug(info)


def close():
    parsers = new_objects(parser_class_map)
    urlhandles = new_objects(urlhandle_class_map)

    def exit():
        time.sleep(0.001)
        os._exit(0)

    close_threads = []
    for parser in parsers:
        close_threads.append(pool.spawn(parser.closeParser))
    for urlhandle in urlhandles:
        close_threads.append(pool.spawn(urlhandle.closeUrlHandle))
    joinall(close_threads, timeout=CLOSE_TIMEOUT)
    pool.spawn(exit)


@app.route('/close', methods=['POST', 'GET'])
def Close():
    try:
        '''
        uuid = request.values.get('uuid', None)
        if uuid is None or uuid != version["uuid"]:
            raise Exception("get the error uuid:" + str(uuid))
        '''
        close()
        return ""
    except Exception as e:
        info = traceback.format_exc()
        logging.error(info)
        result = {"type": "error", "error": info}
        jjson = json.dumps(result)
        logging.debug(jjson)
        return jjson


@app.route('/GetVersion', methods=['POST', 'GET'])
def getVersion():
    try:
        '''
        uuid = request.values.get('uuid', None)
        if uuid is None or uuid != version["uuid"]:
            raise Exception("get the error uuid:" + str(uuid))
        '''
        result = GetVersion()
    except Exception as e:
        info = traceback.format_exc()
        logging.error(info)
        result = {"type": "error", "error": info}
    jjson = json.dumps(result)
    logging.debug(jjson)
    return jjson


@app.route('/Parse', methods=['POST', 'GET'])
def parse():
    try:
        uuid = request.values.get('uuid', None)
        if uuid is None or uuid != version["uuid"]:
            raise Exception("get the error uuid:" + str(uuid))
        s_json = request.values.get('json', None)
        if s_json is not None:
            logging.debug("input json:" + s_json)
            jjson = json.loads(s_json)
            logging.debug("load json:" + str(jjson))
            result = Parse(jjson["input_text"], jjson["types"], jjson["parsers_name"], jjson["urlhandles_name"])
        else:
            raise Exception("can't get input json")
    except Exception as e:
        info = traceback.format_exc()
        logging.error(info)
        result = {"type": "error", "error": info}
    jjson = json.dumps(result)
    logging.debug(jjson)
    return jjson


@app.route('/ParseURL', methods=['POST', 'GET'])
def parseUrl():
    try:
        uuid = request.values.get('uuid', None)
        if uuid is None or uuid != version["uuid"]:
            raise Exception("get the error uuid:" + str(uuid))
        s_json = request.values.get('json', None)
        if s_json is not None:
            logging.debug("input json:" + s_json)
            jjson = json.loads(s_json)
            logging.debug("load json:" + str(jjson))
            result = ParseURL(jjson["input_text"], jjson["label"], jjson["min"], jjson["max"], jjson["urlhandles_name"])
        else:
            raise Exception("can't get input json")
    except Exception as e:
        info = traceback.format_exc()
        result = {"type": "error", "error": info}
    jjson = json.dumps(result)
    logging.debug(jjson)
    return jjson


@app.route('/cache/<url>', methods=['POST', 'GET'])
def cache(url):
    data = get_http_cache_data(url)
    if data is not None:
        return data
    else:
        abort(404)


def arg_parser():
    parser = ArgumentParser(description=version["name"])
    parser.add_argument('--host', type=str, default='127.0.0.1', help="set listening ip")
    parser.add_argument('-p', '--port', type=int, default=5000, help="set listening port")
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


def main(debugstr=None, parsers_name=None, types=None, label=None, host="127.0.0.1", port="5000", timeout=PARSE_TIMEOUT,
         close_timeout=CLOSE_TIMEOUT):
    logging.debug("\n------------------------------------------------------------\n")
    global PARSE_TIMEOUT
    PARSE_TIMEOUT = timeout
    global CLOSE_TIMEOUT
    CLOSE_TIMEOUT = close_timeout
    if debugstr is not None:
        if label is None:
            debug(Parse(debugstr, types=types, parsers_name=parsers_name))
        else:
            debug(ParseURL(debugstr, label))
    else:
        app.run(host=host, port=port, debug=False, use_reloader=False, threaded=True)


if __name__ == '__main__':
    initVersion()
    args = arg_parser()
    globals()["args"] = args
    main(args.debug, args.parser, args.types, args.label, args.host, args.port, args.timeout, args.close_timeout)


    # main()
