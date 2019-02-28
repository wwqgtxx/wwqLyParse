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

import sys
import os
import logging

LEVEL = logging.DEBUG
FORMAT = '%(asctime)s{%(name)s}%(filename)s[line:%(lineno)d]<%(funcName)s> pid:%(process)d %(threadName)s %(levelname)s : %(message)s'
DATA_FMT = '%H:%M:%S'
logging.basicConfig(level=LEVEL, format=FORMAT, datefmt=DATA_FMT, stream=sys.stdout)

try:
    from .common import *
except Exception as e:
    from common import *

asyncio.patch_logging()

if __name__ == "__main__":
    # get_common_real_thread_pool()
    add_remote_logging(FORMAT, DATA_FMT)

import re, threading, sys, json, os, time, logging, importlib
from argparse import ArgumentParser
from typing import Dict, Tuple, List

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
CONN_LRU_TIMEOUT = 60 * 60  # 1 hour

parser_class_map = None
urlhandle_class_map = None


async def parser_check_support(parser, url, types=None):
    if (types is None) or (not parser.get_types()) or (is_in(types, parser.get_types(), strict=False)):
        for un_support in parser.get_un_supports():
            if re.search(un_support, url):
                return False
        for filter_str in parser.get_filters():
            if re.search(filter_str, url):
                return True
    return False


async def url_handle_check_support(url_handle, url):
    for filter_str in url_handle.get_filters():
        if re.match(filter_str, url):
            return True
    return False


async def _url_handle_parse(input_text, url_handles_name=None):
    if url_handles_name is not None:
        _url_handle_class_map = import_by_class_name(class_names=url_handles_name, prefix="urlhandles.",
                                                     super_class=UrlHandle)
    else:
        _url_handle_class_map = urlhandle_class_map
    url_handles = new_objects(_url_handle_class_map)
    url_handles_dict = dict()
    for url_handle_obj in url_handles:
        url_handle_order = url_handle_obj.get_order()
        try:
            url_handle_list = url_handles_dict[url_handle_order]
        except KeyError:
            url_handle_list = list()
            url_handles_dict[url_handle_order] = url_handle_list
        url_handle_list.append(url_handle_obj)
    sorted_url_handles_dict_keys = sorted(url_handles_dict.keys())
    # logging.debug({k: url_handles_dict[k] for k in sorted_url_handles_dict_keys})
    for sorted_url_handles_dict_key in sorted_url_handles_dict_keys:
        url_handle_list = url_handles_dict[sorted_url_handles_dict_key]
        for url_handle_obj in url_handle_list:
            if await url_handle_check_support(url_handle_obj, input_text):
                try:
                    logging.debug(url_handle_obj)
                    result = await asyncio.async_run_func_or_co(url_handle_obj.url_handle, input_text)
                    if (result is not None) and (result is not "") and result != input_text:
                        logging.debug('urlHandle:"' + input_text + '"-->"' + result + '"')
                        input_text = result
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    logging.exception(str(url_handle_obj))
                    # print(e)
                    # import traceback
                    # traceback.print_exc()
    return input_text


async def _init_version():
    if version['version']:
        return
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

    name_tmp_list = [get_name().decode(), version['version'], "[Include "]
    for parser in parsers:
        try:
            version_str = await asyncio.async_run_func_or_co(parser.get_version)
            if version_str:
                name_tmp_list.append(version_str)
                name_tmp_list.append("&")
        except:
            logging.warning("%s version get error" % parser)
    name_tmp_list.append("]")
    name_tmp_list.append(" Running on Python ")
    name_tmp_list.append(sys.version)
    version['name'] = "".join(name_tmp_list)


def init_version():
    return asyncio.run_in_main_async_loop(_init_version()).result()


async def _parse_password(input_text, kk):
    if "||" in input_text:
        input_text = str(input_text).split("||")
        kk["password"] = input_text[1]
        input_text = input_text[0]
    return input_text


def get_version():
    return version


async def _parse(input_text, types=None, parsers_name=None, url_handles_name=None,
                 _use_inside=False, _inside_pool=None, _inside_queue=None,
                 *k, **kk):
    if parsers_name is not None:
        _parser_class_map = import_by_class_name(class_names=parsers_name, prefix="parsers.", super_class=Parser)
    else:
        _parser_class_map = parser_class_map
    parsers = new_objects(_parser_class_map)

    async def run(queue, parser, input_text, pool: AsyncPool, *k, **kk):
        try:
            assert isinstance(queue, asyncio.Queue)
            logging.debug(parser)
            result = await asyncio.async_run_func_or_co(parser.parse, input_text, *k, **kk)
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
                    await queue.put(q_result)
            elif type(result) == list:
                await queue.put(result)
            elif type(result) == ReCallMainParseFunc:
                wait_list = await _parse(*result.k, _use_inside=True, _inside_pool=pool, _inside_queue=queue,
                                         **result.kk)
                await pool.wait(wait_list)
        except asyncio.CancelledError:
            logging.warning("%s timeout exit" % parser)
        except Exception as e:
            logging.exception(str(parser))
            # print(e)
            # import traceback
            # traceback.print_exc()

    if not _use_inside:
        asyncio.set_timeout(asyncio.current_task(), PARSE_TIMEOUT + 1)

    input_text = await _parse_password(input_text, kk)

    input_text = await _url_handle_parse(input_text, url_handles_name)
    if not input_text:
        return None

    results = []
    if _use_inside:
        for parser in parsers:
            if await parser_check_support(parser, input_text, types):
                task = _inside_pool.spawn(run(_inside_queue, parser, input_text, _inside_pool, *k, **kk))
                asyncio.set_timeout(task, asyncio.get_left_time() - 1)
                results.append(task)
        return results
    t_results = []
    q_results = asyncio.Queue()
    async with AsyncPool() as pool:
        for parser in parsers:
            if await parser_check_support(parser, input_text, types):
                task = pool.spawn(run(q_results, parser, input_text, pool, *k, **kk))
                asyncio.set_timeout(task, asyncio.get_left_time() - 1)
        await pool.join()
    while not q_results.empty():
        result = await q_results.get()
        if type(result) == dict:
            t_results.append(result)
        if type(result) == list:
            t_results.extend(result)
    replace_if_exists_list = list()
    for t_result in t_results:
        parser = t_result["parser"]
        replace_if_exists_list.extend(parser.get_replace_if_exists())
    for t_result in t_results:
        parser = t_result["parser"]
        if parser.__class__.__name__ in replace_if_exists_list:
            logging.info("drop " + str(t_result["parser"]) + "'s result because of replace_if_exists_list")
            continue
        data = t_result["result"]
        try:
            if "sorted" not in data or data["sorted"] != True:
                data["data"] = sorted(data["data"], key=lambda d: d["label"], reverse=True)
                data["sorted"] = True
                logging.info("sorted the " + str(t_result["parser"]) + "'s data['data']")
        except:
            pass
        results.append(data)
    return results


async def parse_async(input_text, types=None, parsers_name=None, url_handles_name=None):
    try:
        return await asyncio.async_run_in_loop(
            _parse(input_text, types=types, parsers_name=parsers_name, url_handles_name=url_handles_name),
            loop=asyncio.get_main_async_loop())
    except asyncio.CancelledError:
        return []


def parse(input_text, types=None, parsers_name=None, url_handles_name=None):
    try:
        return asyncio.run_in_main_async_loop(
            _parse(input_text, types=types, parsers_name=parsers_name, url_handles_name=url_handles_name)).result()
    except asyncio.CancelledError:
        return []


async def _parse_url(input_text, label, min=None, max=None, url_handles_name=None, *k, **kk):
    async def run(queue, parser, input_text, label, min, max, *k, **kk):
        try:
            assert isinstance(queue, asyncio.Queue)
            logging.debug(parser)
            result = await asyncio.async_run_func_or_co(parser.parse_url, input_text, label, min, max, *k, **kk)
            if (result is not None) and (result != []):
                if "error" in result:
                    logging.error(result["error"])
                    return
                await queue.put(result)
        except asyncio.CancelledError:
            logging.warning("%s timeout exit" % parser)
        except Exception as e:
            logging.exception(str(parser))

    t_label = label.split("@")
    label = t_label[0]
    parser_name = t_label[1]
    _parser_class_map = import_by_class_name(class_names=[parser_name], prefix="parsers.", super_class=Parser)
    parsers = new_objects(_parser_class_map)
    if not parsers:
        return None

    asyncio.set_timeout(asyncio.current_task(), PARSE_TIMEOUT + 1)

    input_text = await _parse_password(input_text, kk)

    input_text = await _url_handle_parse(input_text, url_handles_name)
    if not input_text:
        return None
    parser = parsers[0]
    q_results = asyncio.Queue()
    async with AsyncPool() as pool:
        task = pool.spawn(run(q_results, parser, input_text, label, min, max, *k, **kk))
        asyncio.set_timeout(task, asyncio.get_left_time() - 1)
        await pool.join()
    if not q_results.empty():
        result = await q_results.get()
    else:
        result = []
    return result


async def parse_url_async(input_text, label, min=None, max=None, url_handles_name=None, *k, **kk):
    try:
        return await asyncio.async_run_in_loop(
            _parse_url(input_text, label, min=min, max=max, url_handles_name=url_handles_name),
            loop=asyncio.get_main_async_loop())
    except asyncio.CancelledError:
        return []


def parse_url(input_text, label, min=None, max=None, url_handles_name=None, *k, **kk):
    try:
        return asyncio.run_in_main_async_loop(
            _parse_url(input_text, label, min=min, max=max, url_handles_name=url_handles_name)).result()
    except asyncio.CancelledError:
        return []


def debug(text):
    try:
        text = json.dumps({"output": text}, ensure_ascii=False)
    except:
        pass
    info = "\n------------------------------------------------------------\n"
    info += (str(text)).encode('gbk', 'ignore').decode('gbk')
    info += "\n------------------------------------------------------------"
    logging.debug(info)


_close_lock = threading.Lock()


def close():
    if _close_lock.acquire(blocking=False):
        logging.debug("Oh!Oh!Oh! I'm closing!")
        parsers = new_objects(parser_class_map)
        url_handles = new_objects(urlhandle_class_map)

        def exit():
            # asyncio_helper.get_main_async_loop().stop()
            # time.sleep(0.001)
            os._exit(0)

        with ThreadPool(thread_name_prefix="ClosePool") as pool:
            for parser in parsers:
                pool.spawn(parser.close_parser)
            for url_handle_obj in url_handles:
                pool.spawn(url_handle_obj.close_url_handle)
            pool.join(timeout=CLOSE_TIMEOUT)
            pool.spawn(exit)
            pool.join()


async def _handle(data):
    req_data = await lib_parse_async(data)
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
                result = await parse_async(j_json["input_text"], j_json["types"], j_json["parsers_name"],
                                           j_json["urlhandles_name"])
            else:
                raise Exception("can't get input json")
        elif req_url == "ParseURL":
            if req_data is not None:
                j_json = req_data
                logging.debug("load json:" + str(j_json))
                result = await parse_url_async(j_json["input_text"], j_json["label"], j_json["min"], j_json["max"],
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
    byte_str = await lib_parse_async(byte_str)
    return byte_str


async def _run(pipe, force_start=False):
    address = r'\\.\pipe\%s@%s' % (pipe, version['version'])
    logging.info("listen address:'%s'" % address)
    for _ in range(3 if force_start else 1):
        try:
            return await ConnectionServer(address, _handle, get_uuid()).run()
        except PermissionError:
            if force_start:
                try:
                    for _ in range(3):
                        async with AsyncPipeClient(address) as conn:
                            await conn.do_auth(get_uuid())
                            req = {"type": "get", "url": 'close', "data": {}}
                            req = json.dumps(req)
                            req = req.encode("utf-8")
                            req = lib_parse(req)
                            await conn.send_bytes(req)
                            await asyncio.sleep(0.1)
                            time.sleep(0.1)
                except FileNotFoundError:
                    pass
                except EOFError:
                    pass
                time.sleep(0.1)
            else:
                raise


def run(pipe, force_start=False):
    asyncio.run_in_main_async_loop(_run(pipe, force_start)).result()


def arg_parser():
    parser = ArgumentParser(description=version["name"])
    parser.add_argument('--pipe', type=str, default='wwqLyParse', help="set PipeName")
    # parser.add_argument('--host', type=str, default='127.0.0.1', help="set listening ip")
    # parser.add_argument('-p', '--port', type=int, default=5000, help="set listening port")
    parser.add_argument('-t', '--timeout', type=int, default=PARSE_TIMEOUT,
                        help="set parse timeout seconds, default %ds" % PARSE_TIMEOUT)
    parser.add_argument('--close_timeout', type=int, default=CLOSE_TIMEOUT,
                        help="set close timeout seconds, default %ds" % CLOSE_TIMEOUT)
    parser.add_argument('--force_start', type=bool, default=False,
                        help="force start server")

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


def init():
    global parser_class_map
    if parser_class_map is None:
        parser_class_map = import_by_module_name(module_names=get_all_filename_by_dir('./parsers'), prefix="parsers.",
                                                 super_class=Parser)
    global urlhandle_class_map
    if urlhandle_class_map is None:
        urlhandle_class_map = import_by_module_name(module_names=get_all_filename_by_dir('./urlhandles'),
                                                    prefix="urlhandles.",
                                                    super_class=UrlHandle)
    init_version()
    get_url_service.init()
    logging.debug("\n------------------------------------------------------------\n")


def main(debugstr=None, parsers_name=None, types=None, label=None, pipe=None, force_start=False
         , timeout=PARSE_TIMEOUT, close_timeout=CLOSE_TIMEOUT):
    init()
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
        try:
            run(pipe, force_start)
        except:
            logging.exception("run error")


if __name__ == '__main__':
    args = arg_parser()
    asyncio.start_main_async_loop_in_other_thread()
    main(args.debug, args.parser, args.types,
         args.label, args.pipe, args.force_start,
         args.timeout, args.close_timeout)
