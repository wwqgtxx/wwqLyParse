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


# sys.path.insert(0, get_real_path('./lib/flask_lib'))
sys.path.insert(0, get_real_path('./lib/aiohttp_lib'))
sys.path.insert(0, get_real_path('./lib/requests_lib'))
sys.path.insert(0, get_real_path('./lib/dns_lib'))

import mimetypes

# for 'http.server' import speed
mimetypes._winreg = None
mimetypes.init()
