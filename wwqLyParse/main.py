#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>

#try:
#    from .gevent import monkey
#except Exception:
#    from gevent import monkey

#monkey.patch_all()

import re,threading,queue,sys,json,os
try:
    from flask import Flask,request
except Exception:
    from .flask import Flask,request
app = Flask(__name__)

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
    'version' : '0.2.2', 
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
urlhandles = [jumpurlhandle.BaiduLinkUrlHandle(),jumpurlhandle.MgtvUrlHandle(),jumpurlhandle.LetvUrlHandle(),postfixurlhandle.PostfixUrlHandle()]

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
        parser_thread.setDaemon(True)
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

def ParseURL(input_text,label,min=None,max=None,parsers = parsers,urlhandles = urlhandles):
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
        parser_thread.setDaemon(True)
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
    
@app.route('/close',methods=['POST','GET'])
def Close(): 
    os._exit(0)
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
    app.run(debug=True, use_reloader=False,threaded=True)
    
    #main()




