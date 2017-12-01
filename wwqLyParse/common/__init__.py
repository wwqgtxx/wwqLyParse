#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
import logging
import sys
import os

COMMON_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../__init__.py"))


def get_real_root_path():
    return os.path.dirname(os.path.abspath(COMMON_PATH))


def get_real_path(abstract_path):
    return os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(COMMON_PATH)), abstract_path))


sys.path.insert(0, get_real_path('./lib/flask_lib'))
sys.path.insert(0, get_real_path('./lib/requests_lib'))

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s{%(name)s}%(filename)s[line:%(lineno)d]<%(funcName)s> pid:%(process)d %(threadName)s %(levelname)s : %(message)s',
                    datefmt='%H:%M:%S', stream=sys.stdout)

from .get_url import *
from .http_cache import *
from .import_class import *
from .lru_cache import *
from .parser import *
from .try_decode import *
from .urlhandle import *
from .utils import *