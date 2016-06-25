#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib.request,io,os,sys,json,re,math,subprocess,traceback

try:
    from ..lib import conf,bridge
except Exception as e:
    from lib import conf,bridge

try:
    from ..common import *
except Exception as e:
    from common import *
    


class YouGetParser(Parser):

    filters = ['^(http|https)://.+']
    bin = './you-get/you-get'
        
    # print exception function
    def _print_exception(self,e):
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
            return []	# use system default proxy

    # make you-get arg
    def _make_arg(self,url, _format=None):
        arg = self._make_proxy_arg()
        # NOTE ignore __default__ format
        if _format and (_format != '__default__'):
            arg += ['--format', _format]
        arg += ['--json', url]
        return arg

    # run you-get
    def _run(self,arg):
        y_bin = bridge.pn(bridge.pjoin(bridge.get_root_path(),self.bin))
        py_bin = sys.executable
        args = [py_bin, y_bin] + arg
        PIPE = subprocess.PIPE
        print(args)
        p = subprocess.Popen(args, stdout=PIPE, stderr=PIPE, shell=False)
        stdout, stderr = p.communicate()
        # try to decode
        stdout = bridge.try_decode(stdout)
        stderr = bridge.try_decode(stderr)
        #print(stdout)
        return stdout, stderr

    # make label
    def _make_label(self,stream):
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
    def _parse_label(self,raw):
        parts = raw.split('_')
        _format = parts[1]
        return _format

    # parse you-get output for parse
    def _parse_parse(self,raw):
        out = {}
        out['type'] = 'formats'
        out['name'] = raw['title'] + '_' + raw['site']
        out['data'] = []
        stream = []
        for _format, s in raw['streams'].items():
            s['_format'] = _format
            stream.append(s)
        # sort stream by size
        stream.sort(key=lambda x:x['size'], reverse=False)
        for i in range(len(stream)):
            stream[i]['_id'] = i
        stream.sort(key=lambda x:x['size'], reverse=True)
        # process each stream
        for s in stream:
            one = {}
            label, size, ext = self._make_label(s)
            one['label'] = label
            one['ext'] = ext
            one['size'] = size
            out['data'].append(one)
        return out

    # parse for parse_url
    def _parse_parse_url(self,raw, _format):
        stream = raw['streams'][_format]
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
            # check referer
            if referer:
                one['args'] = {
                    'Referer' : referer, 
                }
            out.append(one)
        return out

    # try parse json
    def _try_parse_json(self,raw_text):
        while True:
            try:
                info = json.loads(raw_text)
                return info
            except Exception as e:
                rest = '{' + raw_text.split('{', 1)[1]
                if rest == raw_text:
                    raise
                raw_text = rest

    # parse functions
    def _Parse(self,url,types=None):
        yarg = self._make_arg(url)
        stdout, stderr = self._run(yarg)
        #print(stdout)
        # try to decode
        try:
            info = self._try_parse_json(stdout)
        except Exception as e:
            # NOTE make custom Error info
            e_text = str(self)+'return [[stderr]] \n' + stderr
            e_text += '\n [[stdout]] \n' + stdout
            e_text += '\n ERROR info \n' + self._print_exception(e)
            return {
                'error' : e_text, 
            }
        # parse it
        out = self._parse_parse(info)
        return out
    
    def Parse(self,url,types=None):
        if (types is not None) and ("formats" not in types):
            return
        if ('www.iqiyi.com' in url):
            return []
        if re.search('www.iqiyi.com/(lib/m|a_)',url):
            return []
        out =  self._Parse(url,types)
        if "data" in out:
            for data in out['data']:
                data['label'] = data['label'] + ("@youget")
            out["caption"]= "you-get解析"
            out['sorted']= True
        return out

    def _ParseURL(self,url,label,min=None,max=None):
        _format = self._parse_label(label)
        yarg = self._make_arg(url, _format)
        stdout, stderr = self._run(yarg)
        # just load json, without ERROR check
        info = self._try_parse_json(stdout)
        out = self._parse_parse_url(info, _format)
        return out
        
    def ParseURL(self,url,label,min=None,max=None):
        assert "@youget" in label
        out = self._ParseURL(url,label,min,max)
        if "iqiyi" in url:
            for item in out:
                item["unfixIp"] = True
        return out
        
    def getYouGetVersion(self):
        try:
            stdout, stderr = self._run(['--version'])
            if "Errno" in stderr:
                return ""
            return stderr.split(',')[0]
        except Exception as e:
            #print(e)
            import traceback  
            traceback.print_exc()  
        return ""


