#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>

try:
    from .common import *
except Exception as e:
    from common import *
   
pool = Pool()

try:
    from .lib import bridge
except Exception as e:
    from lib import bridge

import sys
sys.path.insert(0, bridge.pn(bridge.pjoin(bridge.get_root_path(), './lib/flask_lib')))

import re,threading,queue,sys,json,os,time,logging
try:
    from flask import Flask,request
except Exception:
    from .flask import Flask,request
app = Flask(__name__)

try:
    from .parsers import listparser,indexparser,anypageparser,yougetparser,lyppvparser,mvtvparser,iqiyiparser,iqiyimparser,iqiyimtsparser,ykdlparser,pvideoparser
except Exception:
    import parsers.listparser as listparser
    import parsers.indexparser as indexparser
    import parsers.anypageparser as anypageparser
    import parsers.yougetparser as yougetparser
    import parsers.lyppvparser as lyppvparser
    import parsers.mvtvparser as mvtvparser
    import parsers.iqiyiparser as iqiyiparser
    import parsers.iqiyimparser as iqiyimparser
    import parsers.iqiyimtsparser as iqiyimtsparser
    import parsers.ykdlparser as ykdlparser
    import parsers.pvideoparser as pvideoparser
    

try:
    from .urlhandles import postfixurlhandle,jumpurlhandle
except Exception:
    import urlhandles.postfixurlhandle as postfixurlhandle
    import urlhandles.jumpurlhandle as jumpurlhandle


version = {
    'port_version' : "0.5.0", 
    'type' : 'parse', 
    'version' : '0.4.4',
    'uuid' : '{C35B9DFC-559F-49E2-B80B-79B66EC77471}',
    'filter' : [],
    'name' : 'WWQ猎影解析插件', 
    'author' : 'wwqgtxx', 
    'copyright' : 'wwqgtxx', 
    'license' : 'GPLV3', 
    'home' : '', 
    'note' : ''
}

PARSE_TIMEOUT = 60


parsers = [listparser.ListParser(), indexparser.IndexParser(), iqiyiparser.IQiYiParser(), iqiyimparser.IQiYiMParser(), iqiyimtsparser.IQiYiMTsParser(), mvtvparser.MgTVParser(), lyppvparser.LypPvParser(), yougetparser.YouGetParser(), ykdlparser.YKDLParser(), anypageparser.AnyPageParser(), pvideoparser.PVideoParser()]
#parsers = [pvideoparser.PVideoParser()]
urlhandles = [jumpurlhandle.BaiduLinkUrlHandle(),jumpurlhandle.MgtvUrlHandle(),jumpurlhandle.LetvUrlHandle(),postfixurlhandle.PostfixUrlHandle()]

def urlHandle(input_text):
    for urlhandle in urlhandles:
        for filter in urlhandle.getfilters():
            if re.match(filter,input_text):
                try:
                    logging.debug(urlhandle)
                    result = urlhandle.urlHandle(input_text)
                    if (result is not None) and (result is not ""):
                        input_text = result
                except Exception as e:
                    logging.exception()
                    #print(e)
                    #import traceback
                    #traceback.print_exc()
    return input_text


def initVersion(): 
    for parser in parsers:
        for filter in parser.getfilters():
            version['filter'].append(filter)
    for urlhandle in urlhandles:
        for filter in urlhandle.getfilters():
            version['filter'].append(filter)
    version['name'] = version['name']+version['version']+"[Include "+yougetparser.YouGetParser().getYouGetVersion()+"&"+lyppvparser.LypPvParser().getLypPvVersion()+"]"
    
def GetVersion(): 
    return version
    
def Parse(input_text,types=None,parsers = parsers,urlhandles = urlhandles):
    def run(queue,parser,input_text,types):
        try:
            logging.debug(parser)
            result = parser.Parse(input_text,types)
            if (result is not None) and (result != []):
                if "error" in result:
                    logging.error(result["error"])
                    return
                if ("data" in result) and (result["data"] is not None) and (result["data"] != []):
                    for data in result['data']:
                        if ('label' in data) and (data['label'] is not None) and (data['label'] != ""):
                            data['label'] = str(data['label']) + "@" + parser.__class__.__name__
                        if ('code' in data) and (data['code'] is not None) and (data['code'] != ""):
                            data['code'] = str(data['code']) + "@" + parser.__class__.__name__
                    queue.put({"result":result,"parser":parser})
        except Exception as e:
            logging.exception(str(parser))
            #print(e)
            #import traceback
            #traceback.print_exc()
            
    input_text = urlHandle(input_text)
    results = []
    parser_threads = []
    t_results = []
    q_results = queue.Queue()

    for parser in parsers:
        for filter in parser.getfilters():
            if re.search(filter,input_text):
                parser_threads.append(pool.spawn(run,q_results,parser,input_text,types))
    for parser_thread in parser_threads:
        parser_thread.join()
    while not q_results.empty():
        t_results.append(q_results.get())
    for parser in parsers:
        for t_result in t_results:
            if t_result["parser"] is parser:
                data = t_result["result"]
                try:
                    if "sorted" not in data or data["sorted"] != 1:
                        data["data"] = sorted(data["data"], key=lambda d: d["label"], reverse=True)
                        logging.info("sorted the "+str(t_result["parser"])+"'s data['data'']")
                except:
                    pass
                results.append(data)

    return results

def ParseURL(input_text,label,min=None,max=None,parsers = parsers,urlhandles = urlhandles):
    def run(queue,parser,input_text,label,min,max):
        try:
            logging.debug(parser)
            result = parser.ParseURL(input_text,label,min,max)
            if (result is not None) and (result != []):
                if "error" in result:
                    logging.error(result["error"])
                    return
                queue.put({"result":result,"parser":parser})
        except Exception as e:
            logging.exception()
            #print(e)
            #import traceback
            #traceback.print_exc()
    
    t_label = label.split("@")
    label = t_label[0]
    parser_name = t_label[1]
    
    input_text = urlHandle(input_text)
    results = []
    parser_threads = []
    t_results = []
    q_results = queue.Queue()

    for parser in parsers:
        if (parser_name == parser.__class__.__name__):
            for filter in parser.getfilters():
                if re.search(filter,input_text):
                    parser_threads.append(pool.spawn(run,q_results,parser,input_text,label,min,max))
    if (gevent is not None):
        gevent.joinall(parser_threads,timeout=PARSE_TIMEOUT)
    else:
        for parser_thread in parser_threads:
            parser_thread.join(PARSE_TIMEOUT)
    while not q_results.empty():
        t_results.append(q_results.get())
    for parser in parsers:
        for t_result in t_results:
            if t_result["parser"] is parser:
                results.append(t_result["result"])
    if results == []:
        return []
    return results[0]
    
def debug(input):
    info = "\n------------------------------------------------------------\n"
    info += ((str(input))).encode('gbk', 'ignore').decode('gbk')
    info += "\n------------------------------------------------------------"
    logging.debug(info)
    
@app.route('/close',methods=['POST','GET'])
def Close():
    def exit():
        time.sleep(0.001)
        os._exit(0)
    for parser in parsers:
        parser.closeParser()
    for urlhandle in urlhandles:
        urlhandle.closeUrlHandle()
    threading.Thread(target=exit).start()
    return ""
    
@app.route('/GetVersion',methods=['POST','GET'])
def getVersion(): 
    result = GetVersion()
    return json.dumps(result)
    
@app.route('/Parse',methods=['POST','GET'])
def parse():
    try:
        input_text = request.values.get('input_text', '')
        types = request.values.get('types', None)
        result = Parse(input_text,types)
    except Exception as e:
        info=sys.exc_info()
        result = {"type" : "error","error" : info}
    jjson = json.dumps(result);
    debug(jjson)
    return jjson
        
    
@app.route('/ParseURL',methods=['POST','GET'])
def parseUrl():
    try:
        input_text = request.values.get('input_text', '')
        label = request.values.get('label', '')
        min = request.values.get('min', None)
        max = request.values.get('max', None)
        result = ParseURL(input_text,label,min,max)
    except Exception as e:
        info=sys.exc_info()
        result = {"type" : "error","error" : info}
    jjson = json.dumps(result);
    debug(jjson)
    return jjson
    


if __name__ == '__main__':
    initVersion()
    logging.debug("\n------------------------------------------------------------\n")
    app.run(debug=False, use_reloader=False,threaded=True)
    
    #main()




