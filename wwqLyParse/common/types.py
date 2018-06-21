#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


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

    def close_parser(self):
        return


class UrlHandle(object):
    filters = []

    def url_handle(self, url):
        pass

    def get_filters(self):
        return self.filters

    def close_url_handle(self):
        return
