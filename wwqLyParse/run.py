#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>

import re,threading,queue,sys

try:
    from .parsers import listparser,indexparser,anypageparser,yougetparser,lyppvparser,mvtvparser
except Exception:
    import parsers.listparser as listparser
    import parsers.indexparser as indexparser
    import parsers.anypageparser as anypageparser
    import parsers.yougetparser as yougetparser
    import parsers.lyppvparser as lyppvparser
    import parsers.mvtvparser as mvtvparser
    

try:
    from .urlhandles import postfixurlhandle,jumpurlhandle
except Exception:
    import urlhandles.postfixurlhandle as postfixurlhandle
    import urlhandles.jumpurlhandle as jumpurlhandle


version = {
    'port_version' : "0.5.0", 
    'type' : 'parse', 
    'version' : '0.1.7', 
    'uuid' : '{C35B9DFC-559F-49E2-B80B-79B66EC77471}',
    'filter' : [],
    'name' : 'WWQ猎影解析插件', 
    'author' : 'wwqgtxx', 
    'copyright' : 'wwqgtxx', 
    'license' : 'GPLV3', 
    'home' : '', 
    'note' : ''
}


parsers = [listparser.ListParser(),indexparser.IndexParser(),mvtvparser.MgTVParser(),lyppvparser.LypPvParser(),yougetparser.YouGetParser(),anypageparser.AnyPageParser()]
urlhandles = [jumpurlhandle.JumpUrlHandle(),postfixurlhandle.PostfixUrlHandle()]

def urlHandle(input_text):
    for urlhandle in urlhandles:
        for filter in urlhandle.getfilters():
            if re.match(filter,input_text):
                try:
                    print(urlhandle)
                    result = urlhandle.urlHandle(input_text)
                    if (result is not None) and (result is not ""):
                        input_text = result
                except Exception as e:
                    #print(e)
                    import traceback  
                    traceback.print_exc()  
    return input_text

def GetVersion(): 
    for parser in parsers:
        for filter in parser.getfilters():
            version['filter'].append(filter)
    for urlhandle in urlhandles:
        for filter in urlhandle.getfilters():
            version['filter'].append(filter)
    version['name'] = version['name']+version['version']+"[Include "+yougetparser.YouGetParser().getYouGetVersion()+"&"+lyppvparser.LypPvParser().getLypPvVersion()+"]"
    return version
    
def Parse(input_text,types=None):
    def run(queue,parser,input_text,types):
        try:
            print(parser)
            result = parser.Parse(input_text,types)
            if (result is not None) and (result != []):
                if "error" in result:
                    print(result["error"])
                    return
                if ("data" in result) and (result["data"] is not None) and (result["data"] != []):
                    queue.put({"result":result,"parser":parser})
        except Exception as e:
            #print(e)
            import traceback  
            traceback.print_exc() 
            
    input_text = urlHandle(input_text)
    results = []
    parser_threads = []
    t_results = []
    q_results = queue.Queue()

    for parser in parsers:
        for filter in parser.getfilters():
            if re.search(filter,input_text):
                parser_threads.append(threading.Thread(target=run, name=str(parser), args=(q_results,parser,input_text,types)))
    for parser_thread in parser_threads:
        parser_thread.start()
    for parser_thread in parser_threads:
        parser_thread.join()
    while not q_results.empty():
        t_results.append(q_results.get())
    for parser in parsers:
        for t_result in t_results:
            if t_result["parser"] is parser:
                results.append(t_result["result"])
        
    return results

def ParseURL(input_text,label,min=None,max=None):
    def run(queue,parser,input_text,label,min,max):
        try:
            print(parser)
            result = parser.ParseURL(input_text,label,min,max)
            if (result is not None) and (result != []):
                if "error" in result:
                    print(result["error"])
                    return
                queue.put({"result":result,"parser":parser})
        except Exception as e:
            #print(e)
            import traceback  
            traceback.print_exc() 
            
    input_text = urlHandle(input_text)
    results = []
    parser_threads = []
    t_results = []
    q_results = queue.Queue()

    for parser in parsers:
        for filter in parser.getfilters():
            if re.search(filter,input_text):
                parser_threads.append(threading.Thread(target=run, name=str(parser), args=(q_results,parser,input_text,label,min,max)))
    for parser_thread in parser_threads:
        parser_thread.start()
    for parser_thread in parser_threads:
        parser_thread.join()
    while not q_results.empty():
        t_results.append(q_results.get())
    for parser in parsers:
        for t_result in t_results:
            if t_result["parser"] is parser:
                results.append(t_result["result"])
        
    return results[0]
    
def debug(input):
    print("\n------------------------------------------------------------\n")
    print (((str(input))).encode('gbk', 'ignore').decode('gbk') )
    
def main(): 
    #debug(GetVersion())
    #debug(Parse('http://www.iqiyi.com/lib/m_209445514.html?src=search'))
    #debug(Parse('http://www.iqiyi.com/a_19rrhacdwt.html#vfrm=2-4-0-1'))
    #debug(Parse('http://www.iqiyi.com/a_19rrhaare5.html'))
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
    debug(Parse('http://list.iqiyi.com/www/2/----------------iqiyi--.html'))
    #debug(Parse('http://www.iqiyi.com/v_19rrl8pmn8.html#vfrm=2-3-0-1'))
    #debug(Parse('http://www.iqiyi.com/v_19rrl8pmn8.html',"formats"))
    #debug(ParseURL("http://www.iqiyi.com/v_19rrl8pmn8.html","4_fullhd_全高清_895.21 MB@youget"))
    #debug(ParseURL("http://www.iqiyi.com/v_19rrl8pmn8.html","4_1080p_1920x1080_2746.0kbps_44:30.660_7_flv_@lyppv"))
    #debug(ParseURL("http://www.iqiyi.com/v_19rrl8pmn8.html","(1)  4_1080p_1920x1080_2746.0kbps_44:30.660_7_flv_@lyppv"))
    #debug(Parse('http://v.pptv.com/show/NWR29Yzj2hh7ibWE.html?rcc_src=S1'))
    #debug(Parse('http://www.bilibili.com/video/av2557971/')) #don't support
    #debug(Parse('http://v.baidu.com/link?url=dm_10tBNoD-LLAMb79CB_p0kxozuoJcW0SiN3eycdo6CdO3GZgQm26uOzZh9fqcNSWZmz9aU9YYCCfT0NmZoGfEMoznyHhz3st-QvlOeyArYdIbhzBbdIrmntA4h1HsSampAs4Z3c17r_exztVgUuHZqChPeZZQ4tlmM5&page=tvplaydetail&vfm=bdvtx&frp=v.baidu.com%2Ftv_intro%2F&bl=jp_video',"formats"))
    #debug(Parse('http://www.mgtv.com/v/1/291976/c/3137384.html',"formats"))
    #debug(ParseURL('http://www.mgtv.com/v/1/291976/c/3137384.html',"1"))


if __name__ == '__main__':
    main()




