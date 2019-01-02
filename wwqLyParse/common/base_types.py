#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


class Parser(object):
    filters = []
    un_supports = []
    types = []
    replace_if_exists = []

    def parse(self, url, *k, **kk):
        pass

    def parse_url(self, url, label, min=None, max=None, *k, **kk):
        pass

    def get_version(self):
        pass

    def get_filters(self):
        return self.filters

    def get_un_supports(self):
        return self.un_supports

    def get_types(self):
        return self.types

    def get_replace_if_exists(self):
        return self.replace_if_exists

    def close_parser(self):
        pass


class ReCallMainParseFunc(object):
    def __init__(self, *k, **kk):
        self.k = k
        self.kk = kk


class UrlHandle(object):
    filters = []
    order = 100

    def url_handle(self, url):
        pass

    def get_filters(self):
        return self.filters

    def get_order(self):
        return self.order

    def close_url_handle(self):
        pass
