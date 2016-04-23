#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>

import re

try:
    from . import listparser
except Exception as e:
    import listparser

try:
    from . import indexparser
except Exception as e:
    import indexparser

version = {
    'port_version' : "0.4.0", 
    'type' : 'parse', 
    'version' : '0.0.2', 
    'uuid' : '{C35B9DFC-559F-49E2-B80B-79B66EC77471}',
    'filter' : [],
    'name' : 'WWQ列表解析插件', 
    'author' : 'wwqgtxx', 
    'copyright' : 'wwqgtxx', 
    'license' : 'GPLV3', 
    'home' : '', 
    'note' : ''
}

parsers = [listparser.ListParser(),indexparser.IndexParser()]

for parser in parsers:
	for filter in parser.getfilters():
		version['filter'].append(filter)

def GetVersion():
    return version
    
def Parse(input_text):
	for parser in parsers:
		for filter in parser.getfilters():
			if re.search(filter,input_text):
				try:
					result = parser.Parse(input_text)
					if result is not (None or []):
						return result
				except Exception as e:
					print(e)
	return []


#print (GetVersion())
#print (Parse('http://www.iqiyi.com/lib/m_209445514.html?src=search'))
#print (Parse('http://www.iqiyi.com/a_19rrhacdwt.html'))
#print (Parse('http://www.le.com'))


