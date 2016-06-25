#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>

import urllib.request,json,sys,subprocess,time

import os
import socket

try:
    from .lib import bridge
except Exception as e:
    from lib import bridge
    
def IsOpen(ip,port):
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    try:
        s.connect((ip,int(port)))
        s.shutdown(2)
        print('%d is open' % port)
        return True
    except:
        print('%d is down' % port)
        return False
        
def _run_main():
    y_bin = bridge.pn(bridge.pjoin(bridge.get_root_path(), './main.py'))
    py_bin = sys.executable
    args = [py_bin,'--normal', y_bin]
    print(args)
    p = subprocess.Popen(args, shell=False,cwd=bridge.get_root_path(),close_fds=True)

def init():
    for n in range(3):
        if not IsOpen("127.0.0.1",5000):
            _run_main()
        else:
            return
        for i in range(5):
            if not IsOpen("127.0.0.1",5000):
                time.sleep(1+i)
            else:
                return
    raise Exception("can't init server")
        
def closeServer():
    if IsOpen("127.0.0.1",5000):
        url = 'http://localhost:5000/close'
        values = {}
        data = urllib.parse.urlencode(values).encode(encoding='UTF8')
        req = urllib.request.Request(url, data)
        try:
            response = urllib.request.urlopen(req)
        except:
            response = None;
            
def Cleanup():
    closeServer()

def GetVersion(debug=False): 
    if (not debug):
        closeServer()
    init()
    url = 'http://localhost:5000/GetVersion'
    #user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
    values = {}
    data = urllib.parse.urlencode(values).encode(encoding='UTF8')
    req = urllib.request.Request(url, data)
    #req.add_header('Referer', 'http://www.python.org/')
    response = urllib.request.urlopen(req)
    the_page = response.read()
    results = json.loads(the_page.decode('UTF8'))
    if (not debug):
        closeServer()
    return results
    
def Parse(input_text,types=None):
    init()
    url = 'http://localhost:5000/Parse'
    #user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
    values = {}
    values["input_text"] = input_text
    if types is not None:
        values["types"] = types
    data = urllib.parse.urlencode(values).encode(encoding='UTF8')
    req = urllib.request.Request(url, data)
    print(data)
    response = urllib.request.urlopen(req)
    the_page = response.read()
    results = json.loads(the_page.decode('UTF8'))
    return results

def ParseURL(input_text,label,min=None,max=None):
    init()
    url = 'http://localhost:5000/ParseURL'
    #user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
    values = {}
    values["input_text"] = input_text
    values["label"] = label
    if min is not None:
        values["min"] = min
    if max is not None:
        values["max"] = max
    data = urllib.parse.urlencode(values).encode(encoding='UTF8')
    req = urllib.request.Request(url, data)
    #req.add_header('Referer', 'http://www.python.org/')
    response = urllib.request.urlopen(req)
    the_page = response.read()
    results = json.loads(the_page.decode('UTF8'))
    return results
    

    
def debug(input):
    print("\n------------------------------------------------------------\n")
    print (((str(input))).encode('gbk', 'ignore').decode('gbk') )
    
def main(): 
    #debug(GetVersion(debug=True))
    Cleanup()
    #debug(Parse('http://www.iqiyi.com/lib/m_209445514.html?src=search'))
    #debug(Parse('http://www.iqiyi.com/a_19rrhacdwt.html#vfrm=2-4-0-1'))
    #debug(Parse('http://www.iqiyi.com/a_19rrhaare5.html'))
    #debug(Parse('http://www.iqiyi.com/a_19rrhbhf6d.html#vfrm=2-3-0-1'))
    #debug(Parse('http://www.le.com'))
    #debug(Parse('http://www.letv.com/comic/10010294.html'))
    #debug(Parse('http://www.mgtv.com/v/1/1/'))
    #debug(Parse('http://tv.le.com/'))
    #debug(Parse('http://search.pptv.com/s_video?kw=%E5%B1%B1%E6%B5%B7%E7%BB%8F%E4%B9%8B%E8%B5%A4%E5%BD%B1%E4%BC%A0%E8%AF%B4'))
    #debug(Parse('http://www.youku.com/'))
    #debug(Parse('http://tv.sohu.com/drama/'))
    #debug(Parse('http://mv.yinyuetai.com/'))
    #debug(Parse('http://v.qq.com/tv/'))
    #debug(Parse('http://www.pptv.com/'))
    #debug(Parse('http://yyfm.xyz/video/album/1300046802.html'))
    #debug(Parse('http://www.iqiyi.com/playlist392712002.html',"collection"))
    #debug(Parse('http://list.iqiyi.com/www/2/----------------iqiyi--.html'))
    #debug(Parse('http://www.iqiyi.com/a_19rrhb8fjp.html',"list"))
    #debug(Parse('http://www.iqiyi.com/v_19rrl8pmn8.html#vfrm=2-3-0-1'))
    #debug(Parse('http://www.iqiyi.com/v_19rrl8pmn8.html',"formats"))
    #debug(Parse('http://www.iqiyi.com/v_19rrl8pmn8.html'))
    #debug(ParseURL("http://www.iqiyi.com/v_19rrl8pmn8.html","4_fullhd_全高清_895.21 MB@youget"))
    #debug(ParseURL("http://www.iqiyi.com/v_19rrl8pmn8.html","4_1080p_1920x1080_2746.0kbps_44:30.660_7_flv_@lyppv"))
    #debug(ParseURL("http://www.iqiyi.com/v_19rrl8pmn8.html","(1)  4_1080p_1920x1080_2746.0kbps_44:30.660_7_flv_@lyppv"))
    #debug(Parse('http://v.pptv.com/show/NWR29Yzj2hh7ibWE.html?rcc_src=S1'))
    #debug(Parse('http://www.bilibili.com/video/av2557971/')) #don't support
    #debug(Parse('http://v.baidu.com/link?url=dm_10tBNoD-LLAMb79CB_p0kxozuoJcW0SiN3eycdo6CdO3GZgQm26uOzZh9fqcNSWZmz9aU9YYCCfT0NmZoGfEMoznyHhz3st-QvlOeyArYdIbhzBbdIrmntA4h1HsSampAs4Z3c17r_exztVgUuHZqChPeZZQ4tlmM5&page=tvplaydetail&vfm=bdvtx&frp=v.baidu.com%2Ftv_intro%2F&bl=jp_video',"formats"))
    #debug(Parse('http://www.hunantv.com/v/1/291976/c/3137384.html'))
    #debug(ParseURL('http://www.mgtv.com/v/1/291976/c/3137384.html',"1"))
    debug(Parse('http://v.youku.com/v_show/id_XMTYxODUxOTEyNA==.html?f=27502474'))
    Cleanup()


if __name__ == '__main__':
    #app.run()
    main()




