import itertools
from . import asyncio


class AsyncPool(object):
    _counter = itertools.count().__next__

    def __init__(self, size=0, thread_name_prefix=None, loop=None):
        self.loop = asyncio.get_running_loop() if loop is None else loop
        self.size = size
        self.semaphore = asyncio.BoundedSemaphore(size, loop=self.loop)
        self._thread_name_prefix = (thread_name_prefix or
                                    ("AsyncPool-%d" % self._counter()))
        self._thread_name_counter = itertools.count().__next__
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

        asyncio.set_task_name(thread_name, task)
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


AsyncCancelled = asyncio.CancelledError

__all__ = ["AsyncPool", "AsyncCancelled"]
