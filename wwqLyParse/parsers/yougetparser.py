#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib.request, io, os, sys, json, re, math, subprocess, traceback, logging

try:
    from ..lib import conf, bridge
except Exception as e:
    from lib import conf, bridge

try:
    from ..common import *
except Exception as e:
    from common import *

__MODULE_CLASS_NAMES__ = ["YouGetParser"]


class YouGetParser(Parser):
    filters = ['^(http|https)://.+']
    types = ["formats"]
    unsupports = ['list.iqiyi.com', 'www.le.com']
    bin = './you-get/you-get'

    # print exception function
    def _print_exception(self, e):
        line = traceback.format_exception(Exception, e, e.__traceback__)
        text = ('').join(line)
        return text

    # load config file
    def _load_config_file(self):
        fpath = bridge.pn(bridge.pjoin(bridge.get_root_path(), conf.proxy_config_file))
        with open(fpath, 'rb') as f:
            blob = f.read()
        text = blob.decode('utf-8')
        info = json.loads(text)
        return info

    # make proxy arg
    def _make_proxy_arg(self):
        try:
            info = self._load_config_file()
            ptype = info['proxy_type']
            if ptype == 'no_proxy':
                return ['--no-proxy']
            elif ptype == 'user_proxy':
                return ['--extractor-proxy', info['proxy_server']]
            return []
        except Exception as e:
            return []  # use system default proxy

    # make you-get arg
    def _make_arg(self, url, _format=None, use_info=True):
        arg = self._make_proxy_arg()
        # NOTE ignore __default__ format
        if _format and (_format != '__default__'):
            arg += ['--format', _format]
            arg += ['--json', url]
        else:
            if use_info:
                arg += ['--info', url]
            else:
                arg += ['--json', url]
        return arg

    # run you-get
    def _run(self, arg, need_stderr=False):
        y_bin = bridge.pn(bridge.pjoin(bridge.get_root_path(), self.bin))
        py_bin = sys.executable
        if "PyRun.exe" in py_bin:
            args = [py_bin, '--normal', y_bin]
        else:
            args = [py_bin, y_bin]
        args = args + arg
        PIPE = subprocess.PIPE
        logging.debug(args)
        p = subprocess.Popen(args, stdout=PIPE, stderr=PIPE if need_stderr else None, shell=False)
        stdout, stderr = p.communicate()
        # try to decode
        stdout = bridge.try_decode(stdout)
        stderr = bridge.try_decode(stderr) if need_stderr else None
        # print(stdout)
        return stdout, stderr

    # make label
    def _make_label(self, stream):
        _format = stream['_format']
        _id = stream['_id']
        quality = stream['video_profile']
        try:
            size_str = byte2size(stream['size'], False)
            size = byte2size(stream['size'], True)
        except:
            size_str = "0"
            size = 0
        l = ('_').join([str(_id), _format, quality, size_str])
        ext = stream['container']
        return l, size, ext

    # parse label
    def _parse_label(self, raw):
        parts = raw.split('_')
        _format = parts[1]
        return _format

    # parse you-get output for parse
    def _parse_parse(self, raw):
        out = {}
        out['type'] = 'formats'
        out['name'] = raw['title'] + '_' + raw['site']
        out['data'] = []
        stream = []
        for _format, s in raw['streams'].items():
            s['_format'] = _format
            stream.append(s)
        # sort stream by size
        try:
            stream.sort(key=lambda x: x['size'], reverse=False)
        except KeyError:
            pass
        for i in range(len(stream)):
            stream[i]['_id'] = i
        try:
            stream.sort(key=lambda x: x['size'], reverse=True)
        except KeyError:
            pass
        # process each stream
        for s in stream:
            one = {}
            label, size, ext = self._make_label(s)
            one['label'] = label
            one['ext'] = ext
            one['size'] = size
            try:
                download = self._parse_parse_url(raw, s['_format'])
                one['download'] = download
            except KeyError:
                pass
            out['data'].append(one)
        return out

    # parse for parse_url
    def _parse_parse_url(self, raw, _format):
        stream = raw['streams'].get(_format, None)
        if stream is None:
            stream = raw['streams']["__default__"]
        container = stream['container']
        urls = stream['src']
        referer = None
        if 'refer' in stream:
            referer = stream['refer']
        out = []
        for u in urls:
            one = {}
            one['protocol'] = 'http'
            one['args'] = {}
            one['urls'] = u
            if container == "m3u8":
                one['protocol'] = 'm3u8'
                if not isinstance(one['urls'], list):
                    if "m3u8" in one['urls'] and ":\\Users\\" in one['urls']:
                        one['urls'] = "file:///" + one['urls']
            # check referer
            if referer:
                one['args'] = {
                    'Referer': referer,
                }
            out.append(one)
        return out

    # try parse json
    def _try_parse_json(self, raw_text):
        while True:
            try:
                info = json.loads(raw_text)
                return info
            except Exception as e:
                try:
                    rest = '{' + raw_text.split('{', 1)[1]
                except IndexError:
                    raise e
                if rest == raw_text:
                    raise
                raw_text = rest

    def _try_parse_info(self, raw_text):
        """
type1:
```
Site:       bilibili.com
Title:      【手书】藤子·F·不二雄漫画×女子高生ED
Type:       MPEG-4 video (video/mp4)
Size:       2.8 MiB (2940054 Bytes)
```

type2:
```
site:                芒果 (MGTV)
title:               快乐大本营20170527期：杨紫秦俊杰合体撒狗粮 任嘉伦变“小伦女”表白 遭秒拒
streams:             # Available quality and codecs
    [ DEFAULT ] _________________________________
    - format:        hd
      container:     ts
      video-profile: 超清
      size:          1005.5 MiB (1054394240 bytes)
    # download-with: you-get --format=hd [URL]

    - format:        sd
      container:     ts
      video-profile: 高清
      size:          568.8 MiB (596470420 bytes)
    # download-with: you-get --format=sd [URL]

    - format:        ld
      container:     ts
      video-profile: 标清
      size:          322.6 MiB (338284192 bytes)
    # download-with: you-get --format=ld [URL]
```
        :param raw_text: 
        :return: 
        """

        def get_item_from_str(string, key):
            string = str(string)
            if string.startswith(key):
                string_array = string.split(key, 1)
                if len(string_array) == 2:
                    return string_array[1].strip()

        def mime_to_container(mime):
            mapping = {
                'video/3gpp': '3gp',
                'video/mp4': 'mp4',
                'video/webm': 'webm',
                'video/x-flv': 'flv',
            }
            if mime in mapping:
                return mapping[mime]
            else:
                return mime.split('/')[1]

        data_array = raw_text.splitlines()
        info = {"site": "", "title": "", "streams": {}}
        last_format_dict = None
        for item in data_array:
            item = str(item.strip()).lower()
            if not item:
                continue
            site = get_item_from_str(item, "site:")
            if site:
                info["site"] = site
            title = get_item_from_str(item, "title:")
            if title:
                info["title"] = title
            format = get_item_from_str(item, "- format:")
            if format:
                last_format_dict = {
                    "container": "",
                    "video_profile": "",
                    "size": ""
                }
                info["streams"][format] = last_format_dict
            container = get_item_from_str(item, "container:")
            if container:
                last_format_dict["container"] = container
            video_profile = get_item_from_str(item, "video-profile:")
            if video_profile:
                last_format_dict["video_profile"] = video_profile
            size = get_item_from_str(item, "size:")
            if size:
                size_array = size.split("(", 1)
                if len(size_array) == 2:
                    size = size_array[1].strip(" bytes)")
                    try:
                        size = int(size)
                    except ValueError:
                        pass
                last_format_dict["size"] = size
            type = get_item_from_str(item, "type:")
            if type:
                last_format_dict = {
                    "container": "",
                    "video_profile": "",
                    "size": ""
                }
                info["streams"]["default"] = last_format_dict
                type_array = type.split("(", 1)
                if len(type_array) == 2:
                    container = type_array[1].strip(")")
                    last_format_dict["container"] = container
        logging.info(info)
        return info

    # parse functions
    def _Parse(self, url):
        yarg = self._make_arg(url)
        stdout, stderr = self._run(yarg)
        # print(stdout)
        # try to decode
        err = None
        info = None
        if stdout:
            try:
                logging.debug(stdout)
                try:
                    info = self._try_parse_json(stdout)
                except json.decoder.JSONDecodeError:
                    info = self._try_parse_info(stdout)
            except Exception as e:
                err = e
        if not info:
            # NOTE make custom Error info
            e_text = str(self) + 'return \n'
            if stderr:
                e_text += '[[stderr]] \n' + stderr
            e_text += '\n [[stdout]] \n' + stdout
            if err:
                e_text += '\n ERROR info \n' + self._print_exception(err)
            return {
                'error': e_text,
            }
        # parse it
        out = self._parse_parse(info)
        return out

    def Parse(self, url):
        out = self._Parse(url)
        if "data" in out:
            out["caption"] = "you-get解析"
            out['sorted'] = True
        return out

    def _ParseURL(self, url, label, min=None, max=None):
        _format = self._parse_label(label)
        yarg = self._make_arg(url, _format)
        stdout, stderr = self._run(yarg)
        # just load json, without ERROR check
        info = self._try_parse_json(stdout)
        out = self._parse_parse_url(info, _format)
        return out

    def ParseURL(self, url, label, min=None, max=None):
        out = self._ParseURL(url, label, min, max)
        if "iqiyi" in url:
            for item in out:
                item["unfixIp"] = True
        # if "le.com" in url:
        #     for item in out:
        #         if item['protocol'] == 'm3u8':
        #             item['adjust'] = '='
        #             item['adjustData'] = item.pop('urls', None)
        #             item['decrypt'] = 'letv'

        return out

    def getYouGetVersion(self):
        try:
            stdout, stderr = self._run(['--version'], True)
            if "Errno" in stderr:
                return ""
            return stderr.split(',')[0]
        except Exception as e:
            logging.exception("get version error")
            # print(e)
            # import traceback
            # traceback.print_exc()
        return ""
