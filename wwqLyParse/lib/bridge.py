# bridge.py, lib/, for lyp_you-get-2, sceext <sceext@foxmail.com> 
# LICENSE GNU GPLv3+ 
# version 0.0.2.0 test201509291822

import os, sys
import json
import subprocess

from . import io_one_line_only as ioo
from . import conf

# global data
etc = {}
etc['to_root_path'] = '../'
etc['root_path'] = ''	# used to cache get root_path result
etc['default_encoding'] = None	# used to cache get default encoding result

# subprocess base functions

# base path functions

def pn(raw):
    return os.path.normpath(raw)

def pjoin(*k):
    return os.path.join(*k)

def pdir(raw):
    return os.path.dirname(raw)

# get plugin root_path
def get_root_path():
    if not etc['root_path']:
        now_dir = pdir(__file__)
        root_path = pn(pjoin(now_dir, etc['to_root_path']))
        etc['root_path'] = root_path
    return etc['root_path']

# get default encoding
def get_default_encoding():
    if not etc['default_encoding']:
        bin_file = pn(pjoin(get_root_path(), conf.bin_get_encoding))
        py_bin = sys.executable
        arg = [py_bin, bin_file]
        PIPE = subprocess.PIPE
        p = subprocess.Popen(arg, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=False)
        stdout, stderr = p.communicate()
        info = json.loads(stdout.decode('utf-8', 'ignore'))
        etc['default_encoding'] = info
    return etc['default_encoding']

# try to decode, to fix encoding BUG on windows
def try_decode(raw, no_error=False):
    fix_list = [get_default_encoding()['stdout']] + conf.fix_encoding
    rest = fix_list
    while len(rest) > 0:
        one = rest[0]
        rest = rest[1:]
        try:
            out = raw.decode(one)
            break
        except Exception as e:
            if len(rest) < 1:
                if no_error:
                    out = raw.decode(one, 'ignore')
                else:
                    raise e
    return out


# get one req from sub
def _get_one_req(p):
    while True:
        raw_line = p.stdout.readline()
        raw_text = try_decode(raw_line)
        # decode by io_one_line_only
        info = ioo.decode(raw_text)
        # check type
        if info[0] == 'send':
            data = json.loads(info[1])
            # done
            return data

# send to sub
def _send_to_sub(p, fun_name='', text=''):
    # encode by io_one_line_only
    raw_text = ioo.encode(['call', fun_name, text]) + '\n'
    raw_blob = raw_text.encode(get_default_encoding()['stdin'])
    # just write it
    p.stdin.write(raw_blob)
    p.stdin.flush()

# make config file path
def _get_conf_file_path():
    p = pn(pjoin(get_root_path(), conf.proxy_config_file))
    return p

# read config file
def _read_conf_file():
    fpath = _get_conf_file_path()
    with open(fpath, 'rb') as f:
        blob = f.read()
    text = blob.decode('utf-8')
    return text

# write config file
def _write_conf_file(info):
    text = json.dumps(info, indent=4, sort_keys=True, ensure_ascii=False)
    blob = text.encode('utf-8')
    fpath = _get_conf_file_path()
    with open(fpath, 'wb') as f:
        f.write(blob)


# end bridge.py


