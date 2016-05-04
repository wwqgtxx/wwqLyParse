#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib.request,io,os,sys,json,re,math,subprocess,traceback

try:
    from ..lib import conf,bridge
except Exception as e:
    from lib import conf,bridge

try:
    from .. import common
except Exception as e:
    import common
    


class YouGetParser(common.Parser):

    filters = ['^(http|https)://.+']
        
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
    def _make_you_get_arg(self,url, _format=None):
        arg = self._make_proxy_arg()
        # NOTE ignore __default__ format
        if _format and (_format != '__default__'):
            arg += ['--format', _format]
        arg += ['--json', url]
        return arg

    # run you-get
    def _run_you(self,arg):
        y_bin = bridge.pn(bridge.pjoin(bridge.get_root_path(), conf.bin_you_get))
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

    # make a 2.3 number, with given length after .
    def num_len(self,n, l=3):
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
    def byte2size(self,size_byte, flag_add_byte=False):
        
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
        
        size_t = self.num_len(size_n, 2)
        
        # make final size_str
        size_str = size_t + ' ' + unit
        
        # check flag
        if flag_add_byte:
            size_str += ' (' + str(size_byte) + ' Byte)'
        # done
        return size_str

    # make label
    def _make_label(self,stream):
        _format = stream['_format']
        _id = stream['_id']
        quality = stream['video_profile']
        l = ('_').join([str(_id), _format, quality, self.byte2size(stream['size'], False)])
        size = self.byte2size(stream['size'], True)
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
            one['label'] = one['label'] + ("@youget")
            one['ext'] = ext
            one['size'] = size
            out['data'].append(one)
        out["caption"]= "you-get解析"
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
            one['value'] = u
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
    def Parse(self,url,types=None):
        if (types is not None) and ("formats" not in types):
            return
        yarg = self._make_you_get_arg(url)
        stdout, stderr = self._run_you(yarg)
        #print(stdout)
        # try to decode
        try:
            info = self._try_parse_json(stdout)
        except Exception as e:
            # NOTE make custom Error info
            e_text = 'you-get return [[stderr]] \n' + stderr
            e_text += '\n [[stdout]] \n' + stdout
            e_text += '\n ERROR info \n' + self._print_exception(e)
            return {
                'error' : e_text, 
            }
        # parse it
        out = self._parse_parse(info)
        return out

    def ParseURL(self,url,label,min=None,max=None):
        assert "@youget" in label
        _format = self._parse_label(label)
        yarg = self._make_you_get_arg(url, _format)
        stdout, stderr = self._run_you(yarg)
        # just load json, without ERROR check
        info = self._try_parse_json(stdout)
        out = self._parse_parse_url(info, _format)
        return out
        
    def getYouGetVersion(self):
        try:
            stdout, stderr = self._run_you(['--version'])
            if "Errno" in stderr:
                return ""
            return stderr.split(',')[0]
        except Exception as e:
            #print(e)
            import traceback  
            traceback.print_exc()  
        return ""


