#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>

import re

try:
    from .parsers import listparser,indexparser,anypageparser,yougetparser,lyppvparser
except Exception:
    import parsers.listparser as listparser
    import parsers.indexparser as indexparser
    import parsers.anypageparser as anypageparser
    import parsers.yougetparser as yougetparser
    import parsers.lyppvparser as lyppvparser

version = {
    'port_version' : "0.5.0", 
    'type' : 'parse', 
    'version' : '0.1.2', 
    'uuid' : '{C35B9DFC-559F-49E2-B80B-79B66EC77471}',
    'filter' : [],
    'name' : 'WWQ猎影解析插件', 
    'author' : 'wwqgtxx', 
    'copyright' : 'wwqgtxx', 
    'license' : 'GPLV3', 
    'home' : '', 
    'note' : ''
}


parsers = [listparser.ListParser(),indexparser.IndexParser(),lyppvparser.LypPvParser(),yougetparser.YouGetParser(),anypageparser.AnyPageParser()]


for parser in parsers:
    for filter in parser.getfilters():
        version['filter'].append(filter)

def GetVersion():
    version['name'] = version['name']+version['version']+"[Include "+yougetparser.YouGetParser().getYouGetVersion()+"]"
    return version
    
def Parse(input_text,types=None):
    results = []
    for parser in parsers:
        for filter in parser.getfilters():
            if re.search(filter,input_text):
                try:
                    print(parser)
                    result = parser.Parse(input_text,types)
                    if (result is not None) and (result != []):
                        if "error" in result:
                            print(result["error"])
                            continue
                        if ("data" in result) and (result["data"] is not None) and (result["data"] != []):
                            results.append(result)
                except Exception as e:
                    #print(e)
                    import traceback  
                    traceback.print_exc()  
    return results

def ParseURL(input_text,label,min=None,max=None):
    for parser in parsers:
        for filter in parser.getfilters():
            if re.search(filter,input_text):
                try:
                    result = parser.ParseURL(input_text,label,min,max)
                    if (result is not None) and (result != []):
                        if "error" in result:
                            print(result["error"])
                            continue
                        return result
                except Exception as e:
                    #print(e)
                    import traceback  
                    traceback.print_exc()  
    return []
    
def debug(input):
    print("\n------------------------------------------------------------\n")
    print (((str(input))).encode('gbk', 'ignore').decode('gbk') )
    
def main():    
    #debug(GetVersion())
    #debug(Parse('http://www.iqiyi.com/lib/m_209445514.html?src=search'))
    #debug(Parse('http://www.iqiyi.com/a_19rrhacdwt.html#vfrm=2-4-0-1'))
    #debug(Parse('http://www.iqiyi.com/a_19rrhaare5.html'))\
    #debug(Parse('http://www.iqiyi.com/a_19rrhbhf6d.html#vfrm=2-3-0-1'))
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
    #debug(Parse('http://yyfm.xyz/video/album/1300046802.html'))
    #debug(Parse('http://list.iqiyi.com/www/2/----------------iqiyi--.html'))
    debug(Parse('http://www.iqiyi.com/v_19rrl8pmn8.html'))
    #debug(Parse('http://www.iqiyi.com/v_19rrl8pmn8.html',"formats"))
    #debug(ParseURL("http://www.iqiyi.com/v_19rrl8pmn8.html","4_fullhd_全高清_895.21 MB"))
    #debug(Parse('http://v.pptv.com/show/NWR29Yzj2hh7ibWE.html?rcc_src=S1')) #don't support
    #debug(Parse('http://www.bilibili.com/video/av2557971/')) #don't support
    
    
    
    

if __name__ == '__main__':
    main()




