#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
from .utils import is_in
import re


class Parser(object):
    filters = []
    un_supports = []
    types = []

    def parse(self, url, *k, **kk):
        pass

    def parse_url(self, url, label, min=None, max=None, *k, **kk):
        pass

    def get_filters(self):
        return self.filters

    def get_un_supports(self):
        return self.un_supports

    def get_types(self):
        return self.types

    def check_support(self, url, types=None):
        if (types is None) or (not self.get_types()) or (is_in(types, self.get_types(), strict=False)):
            for un_support in self.get_un_supports():
                if re.search(un_support, url):
                    return False
            for filter_str in self.get_filters():
                if re.search(filter_str, url):
                    return True
        return False

    def close_parser(self):
        return


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

    def check_support(self, url):
        for filter_str in self.get_filters():
            if re.match(filter_str, url):
                return True
        return False

    def close_url_handle(self):
        return
