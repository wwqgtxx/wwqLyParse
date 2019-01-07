#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
import uuid

http_cache_data = dict()


def put_new_http_cache_data(data, suffix="None"):
    name = str(uuid.uuid4()) + suffix
    http_cache_data[name] = data
    return name


def get_http_cache_data(name, need_delete=True):
    if need_delete:
        return http_cache_data.pop(name, None)
    else:
        return http_cache_data.get(name, None)


def get_http_cache_data_url(name):
    if "args" in globals():
        args = globals()["args"]
        host = args.host
        port = args.port
    else:
        host = "127.0.0.1"
        port = "5000"
    return "http://%s:%s/cache/%s" % (host, port, name)
