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
	
try:
    from . import anypageparser
except Exception as e:
    import anypageparser

version = {
    'port_version' : "0.4.0", 
    'type' : 'parse', 
    'version' : '0.0.8', 
    'uuid' : '{C35B9DFC-559F-49E2-B80B-79B66EC77471}',
    'filter' : [],
    'name' : 'WWQ整页列表解析插件', 
    'author' : 'wwqgtxx', 
    'copyright' : 'wwqgtxx', 
    'license' : 'GPLV3', 
    'home' : '', 
    'note' : ''
}
version['name'] = version['name']+version['version']

parsers = [listparser.ListParser(),indexparser.IndexParser(),anypageparser.AnyPageParser()]

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
	
def debug(input):
	print (((str(input))).encode('gbk', 'ignore').decode('gbk') )
	
def main():	
	#debug(GetVersion())
	#debug(Parse('http://www.iqiyi.com/lib/m_209445514.html?src=search'))
	#debug(Parse('http://www.iqiyi.com/a_19rrhacdwt.html#vfrm=2-4-0-1'))
	#debug(Parse('http://www.iqiyi.com/a_19rrhaare5.html'))\
	debug(Parse('http://www.iqiyi.com/a_19rrhbhf6d.html#vfrm=2-3-0-1'))
	#debug(Parse('http://www.le.com'))
	#debug(Parse('http://www.le.com/comic/10010294.html'))
	#debug(Parse('http://www.mgtv.com/v/1/1/'))
	#debug(Parse('http://tv.le.com/'))
	#debug(Parse('http://search.pptv.com/s_video?kw=%E5%B1%B1%E6%B5%B7%E7%BB%8F%E4%B9%8B%E8%B5%A4%E5%BD%B1%E4%BC%A0%E8%AF%B4'))
	#debug(Parse('http://www.youku.com/'))
	#debug(Parse('http://tv.sohu.com/drama/'))
	#debug(Parse('http://mv.yinyuetai.com/'))
	#debug(Parse('http://v.qq.com/tv/'))
	#debug(Parse('http://www.pptv.com/'))
	
	

if __name__ == '__main__':
    main()




