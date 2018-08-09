#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>

if __name__ == "__main__":
    # import sys
    #
    # sys.modules["gevent"] = None
    try:
        from gevent import monkey

        monkey.patch_all()
        del monkey
    except Exception:
        gevent = None
    import os
    import sys

    _srcdir = os.path.dirname(os.path.realpath(__file__))
    _filepath = os.path.dirname(sys.argv[0])
    sys.path.insert(0, os.path.join(_filepath, _srcdir))

    print(sys.path)
    del sys
    del os

from main import *

get_url_service.init()

if __name__ == "__main__":
    with HttpProxyServer(port=1082) as hps:
        hps.join()
