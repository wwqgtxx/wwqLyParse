#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
import sys
import os

COMMON_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../__init__.py"))


def get_real_root_path():
    return os.path.dirname(os.path.abspath(COMMON_PATH))


def get_real_path(abstract_path):
    return os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(COMMON_PATH)), abstract_path))


PY35 = 0x03050000 <= sys.hexversion < 0x03060000
PY36 = 0x03060000 <= sys.hexversion < 0x03070000
PY37 = 0x03070000 <= sys.hexversion < 0x03080000

# sys.path.insert(0, get_real_path('./lib/flask_lib'))
if not PY35:
    sys.path.insert(0, get_real_path('./lib/aiohttp_lib'))
else:
    sys.path.insert(0, get_real_path('./lib/fallback_lib_py352'))
    sys.path.insert(0, get_real_path('./lib/aiohttp_lib_py352'))
sys.path.insert(0, get_real_path('./lib/requests_lib'))
# sys.path.insert(0, get_real_path('./lib/dns_lib'))

print(sys.path)

import mimetypes

# for 'http.server' import speed
mimetypes._winreg = None
mimetypes.init()
