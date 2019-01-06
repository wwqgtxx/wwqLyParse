#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
import asyncio
import logging
import threading
import functools
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


def get_running_async_loop():
    return asyncio.get_event_loop()


def run_in_common_async_loop(coro):
    loop = get_common_async_loop()
    return asyncio.run_coroutine_threadsafe(coro, loop)


async def async_run_func(func, *args, **kwargs):
    fn = functools.partial(func, *args, **kwargs)
    if asyncio.iscoroutinefunction(func):
        return await fn()
    else:
        return await get_running_async_loop().run_in_executor(None, fn)


class AsyncPool(object):
    def __init__(self, size=0, thread_name_prefix=None):
        self.queue = asyncio.Queue(maxsize=size)
        self.pool_tasks = []

    def _remove_from_pool_tasks(self, task):
        try:
            self.pool_tasks.remove(task)
        except ValueError:
            pass

    async def apply(self, coco):
        task = self.spawn(coco)
        return await task.result()

    def spawn(self, coco):
        task = asyncio.ensure_future(coco)
        task.add_done_callback(self._remove_from_pool_tasks)
        self.pool_tasks.append(task)
        return task

    async def join(self, *k, timeout=None, **kk):
        return await self.wait(wait_list=self.pool_tasks)

    async def kill(self, *k, block=False, **kk):
        for task in self.pool_tasks:
            assert isinstance(task, asyncio.Task)
            task.cancel()
        if block:
            return await self.join()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.kill(block=False)

    @staticmethod
    async def wait(wait_list, timeout=None):
        while True:
            if len(wait_list) == 0:
                return
            try:
                return await asyncio.wait(wait_list, timeout=timeout)
            except ValueError:
                pass
