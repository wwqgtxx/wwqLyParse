#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
import urllib.request,io,os,sys,json,re

class Parser(object):
	filters = []
	def Parse(self,url):
		pass
	def ParseURL(self,url):
		pass
	def getfilters(self):
		return self.filters
	def getUrl(self,url):
		req = urllib.request.Request(url)
		f = urllib.request.urlopen(req)
		s = f.read()
		s = s.decode('utf-8','ignore')
		return s