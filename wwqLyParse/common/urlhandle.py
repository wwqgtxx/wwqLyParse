#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


class UrlHandle(object):
    filters = []

    def url_handle(self, url):
        pass

    def get_filters(self):
        return self.filters

    def close_url_handle(self):
        return
