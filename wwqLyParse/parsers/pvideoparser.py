#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author sceext,wwqgtxx <wwqgtxx@gmail.com>
# parser for p_video

import os, sys
import re
import json
import logging
import subprocess
import time
import urllib.parse

try:
    from ..common import (
        Parser,
        IsOpen,
        getUrl,
        _second_to_time,
        byte2size,
        gen_bitrate,
    )
    # from ..p_video.bin.autoconfig import AUTO_CONFIG, RE_SUPPORT_URL, SUPPORT_URL_BLACKLIST
except Exception:
    from common import (
        Parser,
        IsOpen,
        getUrl,
        _second_to_time,
        byte2size,
        gen_bitrate,
    )
    # from p_video.bin.autoconfig import AUTO_CONFIG, RE_SUPPORT_URL, SUPPORT_URL_BLACKLIST

AUTO_CONFIG, RE_SUPPORT_URL, SUPPORT_URL_BLACKLIST = None, None, []

__MODULE_CLASS_NAMES__ = []

BIN_P_VIDEO = '../p_video/bin/p_video.py'

HANDWICH_BRIDGE_CONFIG = {
    'ip': '127.0.0.1',  # --ip IP
    'port': 48281,  # --port PORT
    # TODO use random key
    'key': None,  # --key KEY

    'core': {  # core ID to use
        'kill_271_cmd5': 'cmd5',
    },
}

BIN_ADL = '../lib/AIRSDK_Compiler/bin/adl.exe'
HANDWICH_BRIDGE_BIN = '../p_video/lib/bridge/handwich_bridge/handwich_bridge.xml'

# TODO load multi-cores support
LOAD_CORE = {
    'id': 'cmd5',
    'path': '../p_video/lib/bridge/handwich_bridge/kill_271_cmd5.swf',
}

P_VIDEO_BASE_ARGS = [
    '-s',
    'handwich_bridge_server=' + json.dumps(HANDWICH_BRIDGE_CONFIG),
    '-s',
    'http_req_default=' + json.dumps({
        'req_with': 'native',
    }),
]


def _check_support_url(raw):
    for i in SUPPORT_URL_BLACKLIST:
        if re.search(i, raw):
            return False
    for i in RE_SUPPORT_URL:
        if re.search(i, raw):
            return True
    return False


def _make_handwich_base_url():
    c = HANDWICH_BRIDGE_CONFIG
    out = 'http://' + c['ip'] + ':' + str(c['port']) + '/handwich_bridge/'
    return out


def _make_call_core_url(core, f, a=None):
    c = HANDWICH_BRIDGE_CONFIG
    out = _make_handwich_base_url() + 'call?core=' + str(core) + '&f=' + str(f)
    if c['key'] != None:
        out += '&key=' + str(c['key'])
    if a != None:
        out += '&a=' + urllib.parse.quote(json.dumps(a))
    return out


def _init_handwich_bridge():
    c = HANDWICH_BRIDGE_CONFIG
    ip = c['ip']
    port = c['port']
    key = c['key']
    # TODO start handwich_bridge
    if not IsOpen(ip, port):
        argv = [_get_rel_path(BIN_ADL), _get_rel_path(HANDWICH_BRIDGE_BIN), '--']
        argv += ['--ip', str(ip), '--port', str(port)]
        if key != None:
            argv += ['--key', str(key)]
        logging.debug(' start handwich_bridge --> ' + str(argv))
        subprocess.Popen(argv, shell=False, close_fds=True)
    # wait and check bridge started successfully
    init_ok = False
    for i in range(3):
        if not IsOpen(ip, port):
            time.sleep(i + 1)
            continue
        url = _make_handwich_base_url() + 'version'
        if key != None:
            url += '?key=' + str(key)
        try:
            info = getUrl(url, allowCache=False, usePool=False)
            logging.debug('handwich_bridge version: ' + info)
            init_ok = True
            break
        except Exception as e:
            logging.warning(e)
            time.sleep(i + 1)
    if not init_ok:
        raise Exception('start handwich_bridge failed')
    # check core loaded and load core
    l = LOAD_CORE
    c_id = l['id']
    c_path = os.path.abspath(_get_rel_path(l['path']))

    def check_core_loaded():
        core_about_url = _make_call_core_url(c_id, 'about')
        # info = json.loads(getUrl(core_about_url, allowCache=False))
        # FIXME
        text = getUrl(core_about_url, allowCache=False, usePool=False)
        logging.debug("core_about raw return:" + text)
        # print('DEBUG: core_about raw return')
        # print(text)
        info = json.loads(text)

        if info[0] != 'ret':
            logging.debug('core not loaded, ' + str(info))
            return False
        logging.debug('core ' + str(c_id) + ', ' + str(info[1]))
        return True

    if not check_core_loaded():
        load_core_url = _make_handwich_base_url() + 'load_core?id=' + str(c_id)
        if c['key'] != None:
            load_core_url += '&key=' + str(c['key'])
        load_core_url += '&path=' + urllib.parse.quote(c_path)

        info = json.loads(getUrl(load_core_url, allowCache=False, usePool=False))
        if info[0] == 'done':
            logging.debug('core loaded, ' + str(info))
        else:
            raise Exception('can not load core', info)
    if not check_core_loaded():
        raise Exception('core not loaded')


def _close_handwich_bridge():
    c = HANDWICH_BRIDGE_CONFIG
    if IsOpen(c['ip'], c['port']):
        url = _make_handwich_base_url() + 'exit'
        if c['key'] != None:
            url += '?key=' + c['key']
        # just send the exit command
        try:
            getUrl(url, allowCache=False, usePool=False)
        except Exception as e:
            logging.error(e)  # ignore error


def _get_rel_path(raw):
    now_dir = os.path.dirname(__file__)
    out = os.path.abspath(os.path.normpath(os.path.join(now_dir, raw)))
    return out


def _run_p_video(argv):
    if "PyRun.exe" in sys.executable:
        args = [sys.executable, '--normal', _get_rel_path(BIN_P_VIDEO)] + argv
    else:
        args = [sys.executable, _get_rel_path(BIN_P_VIDEO)] + argv
    logging.info(' run p_video --> ' + str(args))

    PIPE = subprocess.PIPE
    result = subprocess.run(args, stdout=PIPE, check=True)

    blob = result.stdout
    return blob


def _get_auto_conf(url):
    for i in AUTO_CONFIG:
        if re.search(i, url):
            return AUTO_CONFIG[i]
    raise Exception('can not auto-config url ' + str(url))


def _call_p_video(url, hd=None):
    # make p_video args
    argv = P_VIDEO_BASE_ARGS + _get_auto_conf(url)
    if hd == None:
        set_hd = json.dumps([1, -1])
    else:
        set_hd = json.dumps([hd, hd])
    argv += ['-s', 'hd=' + set_hd, url]

    blob = _run_p_video(argv)
    text = blob.decode('utf-8')
    pvinfo = json.loads(text)
    return pvinfo


def _make_label(v):
    out = [
        'hd=' + str(v['hd']),
        'quality ' + v['quality'],
        'size_px ' + str(v['size_px'][0]) + 'x' + str(v['size_px'][1]),
        'bitrate ' + gen_bitrate(v['size_byte'], v['time_s']),
        'time ' + _second_to_time(v['time_s']),
        'format ' + v['format'],
        'size ' + byte2size(v['size_byte']),
        str(v['count']) + ' part files',
    ]
    return (', ').join(out)


def _label_to_hd(label):
    hd = label.split(',', 1)[0].rsplit('=', 1)[1]
    return float(hd)


def _pvinfo_to_parse_output(pvinfo):
    i = pvinfo['info']
    title = i['title']
    if ('title_extra' in i) and ('sub' in i['title_extra']):
        title += '_' + i['title_extra']['sub']
    title += '_' + i['site_name']
    out = {
        'type': 'formats',
        'sorted': 1,
        'data': [],
        'provider': i['site'] + '_' + i['site_name'],
        'name': title,
    }
    for v in pvinfo['video']:
        format_to_ext = {
            'm3u8/ts': 'ts',
        }
        one = {
            'label': _make_label(v),
            'ext': format_to_ext.get(v['format'], v['format']),
            'size': byte2size(v['size_byte']),
            'code': str(_label_to_hd(_make_label(v))),
        }
        out['data'].append(one)
    return out


def _pvinfo_to_parseurl_output(pvinfo, hd):
    # select hd
    v = None
    for i in pvinfo['video']:
        if i['hd'] == hd:
            v = i
            break
    if v == None:
        raise Exception('can not from pvinfo.video[] get hd ' + str(hd))
    out = []
    for f in v['file']:
        one = {
            'protocol': 'http',
            'urls': f['url'],
        }
        if ('header' in f) and (len(f['header']) > 1):
            one['args'] = f['header']
        # TODO fix m3u8 result
        out.append(one)
    return out


class PVideoParser(Parser):
    filters = RE_SUPPORT_URL
    unsupports = SUPPORT_URL_BLACKLIST + ['list.iqiyi.com']
    types = ["formats"]

    def Parse(self, url, *k, **kk):
        if not _check_support_url(url):
            logging.debug('ignore url ' + url)
            return []
        _init_handwich_bridge()

        pvinfo = _call_p_video(url, hd=None)
        out = _pvinfo_to_parse_output(pvinfo)

        out['caption'] = 'p_video(新负锐)解析'
        return out

    # TODO use the cache feature of p_video
    def ParseURL(self, url, label, *k, **kk):
        _init_handwich_bridge()

        # hd = _label_to_hd(label)
        hd = float(label)
        pvinfo = _call_p_video(url, hd=hd)
        out = _pvinfo_to_parseurl_output(pvinfo, hd)

        # add unfixIp
        if 'iqiyi' in url:
            for i in out:
                i['unfixIp'] = True
        return out

    def closeParser(self):
        _close_handwich_bridge()

    @staticmethod
    def get_p_video_version():
        blob = _run_p_video(['--version'])
        text = blob.decode('utf-8', 'ignore').replace('\r\n', '\n').replace('\r', '\n')
        return text.split('\n', 1)[0]
