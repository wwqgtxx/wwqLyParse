#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
import selectors
from selectors import EVENT_READ, EVENT_WRITE, SelectorKey

try:
    import gevent.select
    from .select import select


    class GeventSelectSelector(selectors.SelectSelector):
        def _select(self, r, w, _, timeout=None):
            r, w, x = select(r, w, w, timeout)
            return r, w + x, []


    try:
        from .poll import *


        class GeventPollSelector(selectors.SelectSelector):
            _selector_cls = poll
            _EVENT_READ = POLLIN
            _EVENT_WRITE = POLLOUT

            def __init__(self):
                super().__init__()
                self._selector = self._selector_cls()

            def register(self, fileobj, events, data=None):
                if (not events) or (events & ~(EVENT_READ | EVENT_WRITE)):
                    raise ValueError("Invalid events: {!r}".format(events))

                key = SelectorKey(fileobj, self._fileobj_lookup(fileobj), events, data)

                if key.fd in self._fd_to_key:
                    raise KeyError("{!r} (FD {}) is already registered"
                                   .format(fileobj, key.fd))

                self._fd_to_key[key.fd] = key
                poller_events = 0
                if events & EVENT_READ:
                    poller_events |= self._EVENT_READ
                if events & EVENT_WRITE:
                    poller_events |= self._EVENT_WRITE
                try:
                    self._selector.register(key.fd, poller_events)
                except:
                    super().unregister(fileobj)
                    raise
                return key

            def unregister(self, fileobj):
                try:
                    key = self._fd_to_key.pop(self._fileobj_lookup(fileobj))
                except KeyError:
                    raise KeyError("{!r} is not registered".format(fileobj)) from None
                try:
                    self._selector.unregister(key.fd)
                except OSError:
                    # This can happen if the FD was closed since it
                    # was registered.
                    pass
                return key

            def modify(self, fileobj, events, data=None):
                try:
                    key = self._fd_to_key[self._fileobj_lookup(fileobj)]
                except KeyError:
                    raise KeyError("{!r} is not registered".format(fileobj)) from None

                changed = False
                if events != key.events:
                    selector_events = 0
                    if events & EVENT_READ:
                        selector_events |= self._EVENT_READ
                    if events & EVENT_WRITE:
                        selector_events |= self._EVENT_WRITE
                    try:
                        self._selector.modify(key.fd, selector_events)
                    except:
                        super().unregister(fileobj)
                        raise
                    changed = True
                if data != key.data:
                    changed = True

                if changed:
                    key = key._replace(events=events, data=data)
                    self._fd_to_key[key.fd] = key
                return key

            def select(self, timeout=None):
                # This is shared between poll() and epoll().
                # epoll() has a different signature and handling of timeout parameter.
                if timeout is None:
                    timeout = None
                elif timeout <= 0:
                    timeout = 0
                else:
                    # poll() has a resolution of 1 millisecond, round away from
                    # zero to wait *at least* timeout seconds.
                    timeout = math.ceil(timeout * 1e3)
                ready = []
                try:
                    fd_event_list = self._selector.poll(timeout)
                except InterruptedError:
                    return ready
                for fd, event in fd_event_list:
                    events = 0
                    if event & ~self._EVENT_READ:
                        events |= EVENT_WRITE
                    if event & ~self._EVENT_WRITE:
                        events |= EVENT_READ

                    key = self._key_from_fd(fd)
                    if key:
                        ready.append((key, events & key.events))
                return ready


        DefaultSelector = GeventPollSelector
    except:
        DefaultSelector = GeventSelectSelector
except:
    DefaultSelector = selectors.DefaultSelector

__all__ = ["DefaultSelector"]
