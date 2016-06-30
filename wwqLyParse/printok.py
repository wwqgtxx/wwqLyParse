#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>

import pyquery

try:
    from .lib import bridge
except Exception as e:
    from lib import bridge
import sys
sys.path.insert(0, bridge.pn(bridge.pjoin(bridge.get_root_path(), './lib/flask_lib')))
try:
    from flask import Flask,request
except Exception:
    from .flask import Flask,request

if __name__ == "__main__":
    print("ok")