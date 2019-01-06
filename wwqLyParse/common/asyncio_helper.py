#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
import asyncio
import sys
import logging
import threading
import functools
import itertools
from .selectors import DefaultSelector
from .concurrent_futures import ThreadPoolExecutor
from .workerpool import POOL_TYPE, GEVENT_POOL

if sys.version_info >= (3, 7):
    async_current_task = asyncio.current_task
    async_create_task = asyncio.create_task
else:
    async_current_task = asyncio.Task.current_task
    async_create_task = asyncio.ensure_future


def new_raw_async_loop():
    if POOL_TYPE == GEVENT_POOL:
        loop = asyncio.SelectorEventLoop(DefaultSelector())
    else:
        loop = asyncio.ProactorEventLoop()
    executor = ThreadPoolExecutor()
    import concurrent.futures
    assert isinstance(executor, concurrent.futures.ThreadPoolExecutor)
    loop.set_default_executor(executor)
    logging.debug("set %s for %s" % (executor, loop))
    return loop


def _run_forever(loop):
    logging.debug("start loop %s", loop)
    asyncio.set_event_loop(loop)
    loop.run_forever()


def new_running_async_loop(name="AsyncLoopThread"):
    loop = new_raw_async_loop()

    threading.Thread(target=_run_forever, args=(loop,), name=name, daemon=True).start()
    return loop


_common_async_loop = None


def get_common_async_loop():
    global _common_async_loop
    if _common_async_loop is None:
        _common_async_loop = new_running_async_loop()
    return _common_async_loop


def start_common_async_loop_in_main_thread(callback, *args, **kwargs):
    global _common_async_loop
    assert _common_async_loop is None
    _common_async_loop = new_raw_async_loop()

    def _cb():
        callback(*args, **kwargs)
        _common_async_loop.stop()

    thread = threading.Thread(target=_cb)
    _common_async_loop.call_soon(thread.start)
    _run_forever(_common_async_loop)


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
    _counter = itertools.count().__next__

    def __init__(self, size=0, thread_name_prefix=None):
        self.queue = asyncio.Queue(maxsize=size)
        self._thread_name_prefix = (thread_name_prefix or
                                    ("AsyncPool-%d" % self._counter()))
        self._thread_name_counter = itertools.count().__next__
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
        thread_name = '%s_%d' % (self._thread_name_prefix or self,
                                 self._thread_name_counter())
        task = async_create_task(coco)
        task.name = thread_name
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


def async_patch_logging():
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        try:
            task = async_current_task()
            if task is not None:
                record.threadName = record.threadName + '~' + getattr(task, "name")
        except AttributeError:
            pass
        except RuntimeError:
            pass
        return record

    logging.setLogRecordFactory(record_factory)
