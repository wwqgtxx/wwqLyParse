#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>

if __name__ == "__main__":
    # import sys
    #
    # sys.modules["gevent"] = None
    # try:
    #     from gevent import monkey
    #
    #     monkey.patch_all()
    #     del monkey
    # except Exception:
    #     gevent = None
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


async def test():
    async with AsyncHttpProxyServer(host='localhost', port=1082) as hps:
        await hps.join_async()


def server():
    asyncio.run_in_main_async_loop(test()).result()


if __name__ == "__main__":
    # with HttpProxyServer(host='localhost', port=1082) as hps:
    #     hps.join()
    asyncio.start_main_async_loop_in_other_thread()
    server()
