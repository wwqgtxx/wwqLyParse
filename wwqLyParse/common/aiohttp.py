#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
from aiohttp import *
import aiohttp as _aiohttp
import logging

_logger = logging.getLogger("aiohttp")


class TCPConnector(_aiohttp.TCPConnector):
    def _get(self, key):
        conn = super(TCPConnector, self)._get(key)
        url = "%s://%s:%d" % ("https" if key.is_ssl else "http", key.host, key.port)
        if conn is None:
            _logger.debug("create new connection for %s" % url)
        else:
            _logger.debug("reused connection for %s" % url)
        return conn


__all__ = _aiohttp.__all__
