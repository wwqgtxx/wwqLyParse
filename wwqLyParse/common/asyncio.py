#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
import asyncio
import logging
import threading
from .selectors import DefaultSelector
from .concurrent_futures import ThreadPoolExecutor
from .workerpool import POOL_TYPE, GEVENT_POOL


def new_running_async_loop(name="AsyncLoopThread"):
    if POOL_TYPE == GEVENT_POOL:
        loop = asyncio.SelectorEventLoop(DefaultSelector())
    else:
        loop = asyncio.ProactorEventLoop()
    executor = ThreadPoolExecutor()
    import concurrent.futures
    assert isinstance(executor, concurrent.futures.ThreadPoolExecutor)
    loop.set_default_executor(executor)
    logging.debug("set %s for %s" % (executor, loop))

    def _run_forever():
        logging.debug("start loop %s", loop)
        asyncio.set_event_loop(loop)
        loop.run_forever()

    threading.Thread(target=_run_forever, name=name, daemon=True).start()
    return loop


_common_async_loop = None


def get_common_async_loop():
    global _common_async_loop
    if _common_async_loop is None:
        _common_async_loop = new_running_async_loop()
    return _common_async_loop
