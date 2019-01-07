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
    get_current_task = asyncio.current_task
    get_running_loop = asyncio.get_running_loop
else:
    get_current_task = asyncio.Task.current_task
    get_running_loop = asyncio.get_event_loop

CancelledError = asyncio.CancelledError


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


_main_async_loop = None  # type: asyncio.AbstractEventLoop


def get_main_async_loop():
    assert _main_async_loop is not None
    return _main_async_loop


def start_main_async_loop_in_main_thread(callback, *args, **kwargs):
    global _main_async_loop
    assert _main_async_loop is None
    _main_async_loop = new_raw_async_loop()

    def _cb():
        try:
            callback(*args, **kwargs)
        finally:
            _main_async_loop.stop()

            async def _null():
                pass

            asyncio.run_coroutine_threadsafe(_null(), _main_async_loop)

    thread = threading.Thread(target=_cb)
    _main_async_loop.call_soon(thread.start)
    threading.current_thread().name = "MainLoop"
    _run_forever(_main_async_loop)
    threading.current_thread().name = "MainThread"


def set_task_name(name: str, task: asyncio.Task = None):
    if task is None:
        task = get_current_task()
    task.name = name


def get_task_name(task: asyncio.Task = None):
    try:
        if task is None:
            task = get_current_task()
        if task is not None:
            return getattr(task, "name")
    except AttributeError:
        pass
    except RuntimeError:
        pass
    return ""


def get_task_name_with_thread(task: asyncio.Task = None):
    task_name = get_task_name(task)
    thread_name = threading.current_thread().getName()
    if task_name:
        return thread_name + '~' + task_name
    else:
        return thread_name


def run_in_main_async_loop(coro):
    thread_name = threading.current_thread().getName()

    async def _co():
        set_task_name("For-" + thread_name)
        return await coro

    loop = get_main_async_loop()
    return asyncio.run_coroutine_threadsafe(_co(), loop)


async def async_run_func_or_co(func_or_co, *args, **kwargs):
    fn = functools.partial(func_or_co, *args, **kwargs)
    if asyncio.iscoroutinefunction(func_or_co):
        return await fn()
    else:
        return await get_running_loop().run_in_executor(None, fn)


class AsyncPool(object):
    _counter = itertools.count().__next__

    def __init__(self, size=0, thread_name_prefix=None, loop=None):
        self.size = size
        self.semaphore = asyncio.locks.BoundedSemaphore(size)
        self._thread_name_prefix = (thread_name_prefix or
                                    ("AsyncPool-%d" % self._counter()))
        self._thread_name_counter = itertools.count().__next__
        self.loop = get_running_loop() if loop is None else loop
        self.pool_tasks = []

    def _remove_from_pool_tasks(self, task):
        try:
            self.pool_tasks.remove(task)
        except ValueError:
            pass

    async def _runner(self, coco):
        async with self.semaphore:
            return await coco

    async def apply(self, coco):
        task = self.spawn(coco)
        return await task

    def spawn(self, coco):
        thread_name = '%s_%d' % (self._thread_name_prefix or self,
                                 self._thread_name_counter())
        if self.size:
            task = self.loop.create_task(self._runner(coco))
        else:
            task = self.loop.create_task(coco)

        set_task_name(thread_name, task)
        task.add_done_callback(self._remove_from_pool_tasks)
        self.pool_tasks.append(task)
        return task

    async def join(self, *k, timeout=None, **kk):
        return await self.wait(wait_list=self.pool_tasks, timeout=timeout, loop=self.loop)

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
    async def wait(wait_list, timeout=None, loop=None):
        while True:
            if len(wait_list) == 0:
                return
            try:
                return await asyncio.wait(wait_list, timeout=timeout, loop=loop)
            except ValueError:
                pass


def patch_logging():
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.threadName = get_task_name_with_thread()
        return record

    logging.setLogRecordFactory(record_factory)
