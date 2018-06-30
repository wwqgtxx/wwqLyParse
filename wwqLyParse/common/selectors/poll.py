#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
try:
    import gevent.select
except:
    from select import poll, POLLIN, POLLPRI, POLLOUT, POLLERR, POLLHUP, POLLNVAL
else:
    POLLIN = 0x0001
    POLLPRI = 0x0002
    POLLOUT = 0x0004
    POLLERR = 0x0008
    POLLHUP = 0x0010
    POLLNVAL = 0x0020


    class PollResult(object):
        __slots__ = ('events', 'event')

        def __init__(self):
            self.events = set()
            self.event = gevent.select.Event()

        def add_event(self, events, fd):
            if events < 0:
                result_flags = POLLNVAL
            else:
                result_flags = 0
                if events & gevent.select._EV_READ:
                    result_flags = POLLIN
                if events & gevent.select._EV_WRITE:
                    result_flags |= POLLOUT

            self.events.add((fd, result_flags))
            self.event.set()


    class poll(object):
        """
        An implementation of :class:`select.poll` that blocks only the current greenlet.

        .. caution:: ``POLLPRI`` data is not supported.

        .. versionadded:: 1.1b1
        """

        def __init__(self):
            # {int -> flags}
            # We can't keep watcher objects in here because people commonly
            # just drop the poll object when they're done, without calling
            # unregister(). dnspython does this.
            self.fds = {}
            self.loop = gevent.select.get_hub().loop

        def register(self, fd, eventmask=gevent.select._NONE):
            if eventmask is gevent.select._NONE:
                flags = gevent.select._EV_READ | gevent.select._EV_WRITE
            else:
                flags = 0
                if eventmask & POLLIN:
                    flags = gevent.select._EV_READ
                if eventmask & POLLOUT:
                    flags |= gevent.select._EV_WRITE
                # If they ask for POLLPRI, we can't support
                # that. Should we raise an error?

            fileno = gevent.select.get_fileno(fd)
            self.fds[fileno] = flags

        def modify(self, fd, eventmask):
            self.register(fd, eventmask)

        def poll(self, timeout=None):
            """
            poll the registered fds.

            .. versionchanged:: 1.2a1
               File descriptors that are closed are reported with POLLNVAL.

            .. versionchanged:: 1.3a2
               Under libuv, interpret *timeout* values less than 0 the same as *None*,
               i.e., block. This was always the case with libev.
            """
            result = PollResult()
            watchers = []
            io = self.loop.io
            MAXPRI = self.loop.MAXPRI
            try:
                for fd, flags in gevent.select.iteritems(self.fds):
                    watcher = io(fd, flags)
                    watchers.append(watcher)
                    watcher.priority = MAXPRI
                    watcher.start(result.add_event, fd, pass_events=True)
                if timeout is not None:
                    if timeout < 0:
                        # The docs for python say that an omitted timeout,
                        # a negative timeout and a timeout of None are all
                        # supposed to block forever. Many, but not all
                        # OS's accept any negative number to mean that. Some
                        # OS's raise errors for anything negative but not -1.
                        # Python 3.7 changes to always pass exactly -1 in that
                        # case from selectors.

                        # Our Timeout class currently does not have a defined behaviour
                        # for negative values. On libuv, it uses a check watcher and effectively
                        # doesn't block. On libev, it seems to block. In either case, we
                        # *want* to block, so turn this into the sure fire block request.
                        timeout = None
                    elif timeout:
                        # The docs for poll.poll say timeout is in
                        # milliseconds. Our result objects work in
                        # seconds, so this should be *=, shouldn't it?
                        timeout /= 1000.0
                result.event.wait(timeout=timeout)
                return list(result.events)
            finally:
                for awatcher in watchers:
                    awatcher.stop()
                    awatcher.close()

        def unregister(self, fd):
            """
            Unregister the *fd*.

            .. versionchanged:: 1.2a1
               Raise a `KeyError` if *fd* was not registered, like the standard
               library. Previously gevent did nothing.
            """
            fileno = gevent.select.get_fileno(fd)
            del self.fds[fileno]
