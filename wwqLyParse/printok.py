#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>

import pyquery

if __name__ == "__main__":
    import os
    import sys

    _srcdir = os.path.dirname(os.path.realpath(__file__))
    _filepath = os.path.dirname(sys.argv[0])
    sys.path.insert(0, os.path.join(_filepath, _srcdir))

    os.environ["NOT_LOGGING"] = "1"
    del sys
    del os

try:
    from .common import *
except Exception as e:
    from common import *

try:
    from flask import Flask,request
except Exception:
    from .flask import Flask,request

if __name__ == "__main__":
    print("ok")