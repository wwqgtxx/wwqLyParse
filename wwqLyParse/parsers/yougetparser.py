#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib.request, io, os, sys, json, re, math, subprocess, traceback, logging

try:
    from ..common import *
except Exception as e:
    from common import *

__MODULE_CLASS_NAMES__ = ["YouGetParser"]


class YouGetParser(Parser):
    filters = ['^(http|https)://.+']
    types = ["formats"]
    un_supports = ["www.iqiyi.com", "www.iqiyi.com/a_", 'www.iqiyi.com/lib/m', 'list.iqiyi.com', 'list.youku.com',
                   'www.le.com', 'www.mgtv.com', 'yinyuetai.com',
                   r'^(http|https)://cache.',
                   r'^(http|https)://\d+\.\d+\.\d+\.\d+']
    bin = './you-get/you-get'
    name = "you-get解析"

    # print exception function
    @staticmethod
    def _print_exception(e):
        line = traceback.format_exception(Exception, e, e.__traceback__)
        text = ''.join(line)
        return text

    # make you-get arg
    def _make_arg(self, url, _format=None, use_info=True, password=None, *k, **kk):
        # arg = self._make_proxy_arg()
        arg = []
        if password:
            arg += ['--password', password]
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

    def _get_py_bin(self):
        py_bin = sys.executable
        if "wwqLyParse64.exe" in py_bin:
            py_bin = py_bin.replace("wwqLyParse64.exe", "wwqLyParse64-youget.exe")
        elif "wwqLyParse32.exe" in py_bin:
            py_bin = py_bin.replace("wwqLyParse32.exe", "wwqLyParse32-youget.exe")
        return py_bin

    # run you-get
    def _run(self, arg, need_stderr=False):
        y_bin = get_real_path(self.bin) if self.bin else None
        py_bin = self._get_py_bin()
        if "PyRun.exe" in py_bin:
            args = [py_bin, '--normal', y_bin]
        else:
            args = [py_bin, y_bin]
        if y_bin is None:
            args.pop()
        args = args + arg
        PIPE = subprocess.PIPE
        logging.debug(args)
        p = subprocess.Popen(args, stdout=PIPE, stderr=PIPE if need_stderr else None, shell=False)
        try:
            stdout, stderr = p.communicate(timeout=get_main().PARSE_TIMEOUT - 5)
        except subprocess.TimeoutExpired:
            logging.debug("Timeout!!! %s kill %s" % (self.__class__.__name__, str(p)))
            p.kill()
            stdout, stderr = p.communicate()
        # try to decode
        stdout = try_decode(stdout)
        stderr = try_decode(stderr) if need_stderr else None
        # print(stdout)
        return stdout, stderr

    # make label
    def _make_label(self, stream):
        _format = stream['_format']
        _id = stream['_id']
        quality = stream['video_profile']
        quality = quality.replace(' ', '')
        try:
            size_str = byte2size(stream['size'], False)
            size = byte2size(stream['size'], True)
        except:
            size_str = "0"
            size = 0
        _format = str(_format).replace("_", "!")
        l = '_'.join([str(_id), _format, quality, size_str])
        ext = stream['container']
        return l, _format, size, ext

    # parse label
    @staticmethod
    def _parse_label(raw):
        if '_' in raw:
            parts = raw.split('_')
            _format = parts[1]
            _format = str(_format).replace("!", "_")
            return _format
        raw = str(raw).replace("!", "_")
        return raw

    # parse you-get output for parse
    def _parse_parse(self, raw):
        out = {'type': 'formats', 'name': raw['title'] + '_' + raw['site'], 'data': []}
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
            label, code, size, ext = self._make_label(s)
            one['label'] = label
            one['code'] = code
            one['ext'] = ext
            one['size'] = size
            try:
                download = self._parse_parse_url(raw, s['_format'])
                one['download'] = download
            except KeyError:
                pass
            out['data'].append(one)
        out["caption"] = self.name
        out['sorted'] = True
        return out

    # parse for parse_url
    def _parse_parse_url(self, raw, _format):
        stream = raw['streams'].get(_format, None)
        if stream is None:
            for item in raw['streams'].keys():
                if str(item).lower() == str(_format).lower():
                    stream = raw['streams'][item]
        if stream is None:
            stream = raw['streams']["__default__"]
        container = stream['container']
        urls = stream['src']
        referer = None
        ua = None
        if "extra" in raw:
            extra = raw["extra"]
            if isinstance(extra, dict):
                referer = extra.get("referer", None)
                ua = extra.get("ua", None)
        if 'refer' in stream:
            referer = stream['refer']
        out = []
        for u in urls:
            one = {'protocol': 'http', 'args': {}, 'urls': u}
            if container == "m3u8":
                one['protocol'] = 'm3u8'
                if not isinstance(one['urls'], list):
                    if "m3u8" in one['urls'] and ":\\Users\\" in one['urls']:
                        one['urls'] = "file:///" + one['urls']
            # check referer
            if referer or ua:
                one['args'] = {}
                if referer:
                    one['args']['Referer'] = referer
                if ua:
                    one['args']['User-Agent'] = ua
            else:
                one['args'] = {}
            out.append(one)
        return out

    # try parse json
    @staticmethod
    def _try_parse_json(raw_text):
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

    @staticmethod
    def _get_item_from_str(string, key):
        string = str(string)
        if string.startswith(key):
            string_array = string.split(key, 1)
            if len(string_array) == 2:
                return string_array[1].strip()

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
            site = self._get_item_from_str(item, "site:")
            if site:
                info["site"] = site
            title = self._get_item_from_str(item, "title:")
            if title:
                info["title"] = title
            format = self._get_item_from_str(item, "- format:")
            if format:
                last_format_dict = {
                    "container": "",
                    "video_profile": "",
                    "size": ""
                }
                info["streams"][format] = last_format_dict
            container = self._get_item_from_str(item, "container:")
            if container:
                last_format_dict["container"] = container
            video_profile = self._get_item_from_str(item, "video-profile:")
            if video_profile:
                last_format_dict["video_profile"] = video_profile
            size = self._get_item_from_str(item, "size:")
            if size:
                size_array = size.split("(", 1)
                if len(size_array) == 2:
                    size = size_array[1].strip(" bytes)")
                    try:
                        size = int(size)
                    except ValueError:
                        pass
                last_format_dict["size"] = size
            type = self._get_item_from_str(item, "type:")
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
    def _parse(self, url, *k, **kk):
        yarg = self._make_arg(url, *k, **kk)
        stdout, stderr = self._run(yarg)
        # print(stdout)
        # try to decode
        err = None
        info = None
        if stdout:
            try:
                logging.debug("%s get stdout: %s" % (self.__class__.__name__, stdout))
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

    def parse(self, url, *k, **kk):
        out = self._parse(url, *k, **kk)
        # if "bilibili" in url:
        #     for item in out['data']:
        #         if isinstance(item, dict):
        #             download = item.get("download", None)
        #             if download:
        #                 for item2 in download:
        #                     if isinstance(item2, dict):
        #                         args = item2.get("args", None)
        #                         if args and isinstance(args, dict):
        #                             referer = args.get('Referer', None)
        #                             if not referer:
        #                                 args['Referer'] = url
        #                         else:
        #                             item2["args"] = {'Referer': url}
        return out

    def _parse_url(self, url, label, min=None, max=None, *k, **kk):
        _format = self._parse_label(label)
        yarg = self._make_arg(url, _format, *k, **kk)
        stdout, stderr = self._run(yarg)
        # just load json, without ERROR check
        info = self._try_parse_json(stdout)
        logging.debug("\n" + str(info))
        out = self._parse_parse_url(info, _format)
        return out

    def parse_url(self, url, label, min=None, max=None, *k, **kk):
        out = self._parse_url(url, label, min, max, *k, **kk)
        if "iqiyi" in url:
            for item in out:
                item["unfixIp"] = True
        # if "bilibili" in url:
        #     for item in out:
        #         if isinstance(item, dict):
        #             args = item.get("args", None)
        #             if args and isinstance(args, dict):
        #                 referer = args.get('Referer', None)
        #                 if not referer:
        #                     args['Referer'] = url
        #             else:
        #                 item["args"] = {'Referer': url}
        # if "le.com" in url:
        #     for item in out:
        #         if item['protocol'] == 'm3u8':
        #             item['adjust'] = '='
        #             item['adjustData'] = item.pop('urls', None)
        #             item['decrypt'] = 'letv'

        return out

    def get_version(self):
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
