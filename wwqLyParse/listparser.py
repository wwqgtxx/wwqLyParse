#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib.request,io,os,sys,json,re

from pyquery.pyquery import PyQuery

try:
    from . import common
except Exception as e:
    import common

class ListParser(common.Parser):

	filters = ['www.iqiyi.com/lib/m','www.iqiyi.com/a_']
		
	def Parse(self,input_text):
		if re.search('www.iqiyi.com/lib/m',input_text):
			return self.Parse_lib_m(input_text)
		if re.search('www.iqiyi.com/a_',input_text):
			return self.Parse_a(input_text)
		
	def Parse_a(self,input_text):
		html = PyQuery(self.getUrl(input_text))
		album_items = html('ul.site-piclist').children('li')
		title = html('h1.main_title').children('a').text()
		i =0
		data = {
			"data": [],
			"more": False,
			"title": title,
			"total": i,
			"type": "list"
		}
		for album_item in album_items:
			album_item = PyQuery(album_item)
			site_piclist_info = PyQuery(album_item.children('div.site-piclist_info'))
			site_piclist_info_title = PyQuery(site_piclist_info.children('p.site-piclist_info_title'))
			site_piclist_info_title_a = PyQuery(site_piclist_info_title.children('a'))
			site_piclist_info_title_fs12 = PyQuery(site_piclist_info.children('p.fs12'))
			site_piclist_info_title_fs12_a = PyQuery(site_piclist_info_title_fs12.children('a'))
			no = site_piclist_info_title_a.text()
			#if re.search("预告",no):
				#continue
			name = site_piclist_info_title_fs12_a.text()
			url = site_piclist_info_title_fs12_a.attr('href')
			if url is None:
				continue
			subtitle = site_piclist_info_title_fs12_a.text()
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

	def Parse_lib_m(self,input_text):
		html = PyQuery(self.getUrl(input_text))
		
		"""
		album_items = html('div.clearfix').children('li.album_item')
		title = html('h1.main_title').children('a').text()
		i =0
		data = {
			"data": [],
			"more": False,
			"title": title,
			"total": i,
			"type": "list"
		}
		for album_item in album_items:
			no = '第'+str(i+1)+'集'
			name = title+'('+no+')'
			url = PyQuery(album_item).children('a').attr('href')
			subtitle = ''
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
		"""
		data = {
			"data": [],
			"more": False,
			"title": '',
			"total": 0,
			"type": "list"
		}
		
		data_doc_id = html('span.play_source').attr('data-doc-id')
		ejson_url = 'http://rq.video.iqiyi.com/aries/e.json?site=iqiyi&docId='+data_doc_id+'&count=100000'
		ejson = json.loads(self.getUrl(ejson_url))
		ejson_datas = ejson["data"]["objs"]
		data["total"] = ejson_datas["info"]["total_video_number"]
		data["title"] = ejson_datas["info"]["album_title"]
		album_items = ejson_datas["episode"]["data"]
		for album_item in album_items:
			no = '第'+str(album_item["play_order"])+'集'
			name = album_item["title"]
			url = album_item["play_url"]
			subtitle = album_item["desciption"]
			info = {
				"name": name,
				"no": no,
				"subtitle": subtitle,
				"url": url
			}
			data["data"].append(info)
		#print(ejson)
		return data

