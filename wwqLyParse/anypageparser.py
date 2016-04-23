#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib.request,io,os,sys,json,re

from pyquery.pyquery import PyQuery

try:
    from . import common
except Exception as e:
    import common

class AnyPageParser(common.Parser):

	filters = ['^(http|https)\://([a-zA-Z0-9\.\-]+(\:[a-zA-Z0-9\.&amp;%\$\-]+)*@)*((25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9])\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[0-9])|localhost|([a-zA-Z0-9\-]+\.)*[a-zA-Z0-9\-]+\.(com|edu|gov|int|mil|net|org|biz|arpa|info|name|pro|aero|coop|museum|[a-zA-Z]{2}))(\:[0-9]+)*(/($|[a-zA-Z0-9\.\,\?\'\\\+&amp;%\$#\=~_\-]+))*$']
		

		
	def Parse(self,input_text):
		html = PyQuery(self.getUrl(input_text))
		items = html('a')
		title = html('title').text()
		i =0
		data = {
			"data": [],
			"more": False,
			"title": title,
			"total": i,
			"type": "list"
		}
		for item in items:
			a = PyQuery(item)
			name = a.attr('title')
			if name is None:
				name = a.text()
			no = name
			subtitle = name
			url = a.attr('href')
			if url is None:
				continue
			if not re.match('^(http|https)://.+\.html',url):
				continue
			if re.search('(list|mall|about|help|shop|map)',url):
				continue
			info = {
				"name": name,
				"no": no,
				"subtitle": subtitle,
				"url": url
			}
			data["data"].append(info)
			i = i+1
		total = i
		data["total"] = total
		return data


