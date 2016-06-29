#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
try:
    from gevent import monkey
    monkey.patch_all()
    print("gevent.monkey.patch_all()")
    from gevent.pool import Pool
    from gevent.queue import Queue
    print("use gevent.pool")
except Exception:
    gevent = None
    from simplepool import Pool
    from queue import Queue
    print("use simple pool")
    
import urllib.request,io,os,sys,json,re,gzip,time,socket,math,urllib.error,http.client,gc,threading,urllib

urlcache = {}
URLCACHE_MAX = 1000
URLCACHE_POOL = 20
    
pool_getUrl = Pool(URLCACHE_POOL)
pool_cleanUrlcache = Pool(1)
    

def getUrl(oUrl, encoding = 'utf-8' , headers = {}, data = None, method = None,allowCache = True,usePool = True,pool = pool_getUrl) :
    def cleanUrlcache():
        global urlcache
        if (len(urlcache)<=URLCACHE_MAX):
            return
        sortedDict = sorted(urlcache.items(), key=lambda d: d[1]["lasttimestap"], reverse=True)
        newDict = {}
        for (k, v) in sortedDict[:int(URLCACHE_MAX - URLCACHE_MAX/10)]:# 从数组中取索引start开始到end-1的记录
            newDict[k] = v
        del sortedDict
        del urlcache
        urlcache = newDict
        gc.collect()
        print("urlcache has been cleaned")
    def _getUrl(result_queue,oUrl, encoding, headers, data, method,allowCache):
        url_json = {"oUrl":oUrl,"encoding":encoding,"headers":headers,"data":data,"method":method}
        url_json = json.dumps(url_json,sort_keys=True, ensure_ascii=False)
        if allowCache:
            global urlcache
            global URLCACHE_MAX
            urlcache_temp =  urlcache
            if url_json in urlcache_temp:
                item = urlcache_temp[url_json]
                html_text = item["html_text"]
                item["lasttimestap"] = int(time.time())
                print("cache get:"+url_json)
                if (len(urlcache_temp)>URLCACHE_MAX):
                    pool_cleanUrlcache.spawn(cleanUrlcache)
                del urlcache_temp
                result_queue.put(html_text)
                return
            print("normal get:"+url_json)
        else:
            print("nocache get:"+url_json)
        # url 包含中文时 parse.quote_from_bytes(oUrl.encode('utf-8'), ':/&%?=+')
        req = urllib.request.Request( oUrl, headers= headers, data = data, method = method )
        for i in range(10):
            try:
                with urllib.request.urlopen(req ) as  response:
                    headers = response.info()
                    cType = headers.get('Content-Type','')
                    match = re.search('charset\s*=\s*(\w+)', cType)
                    if match:
                        encoding = match.group(1)
                    blob = response.read()
                    if headers.get('Content-Encoding','') == 'gzip':
                        data=gzip.decompress(blob)
                        html_text = data.decode(encoding,'ignore')
                    else:
                        html_text = blob.decode(encoding,'ignore')
                    if allowCache:
                        urlcache[url_json] = {"html_text":html_text,"lasttimestap":int(time.time())}
                    result_queue.put(html_text)
                    return
            except socket.timeout:
                print('request attempt %s timeout' % str(i + 1))
            except urllib.error.URLError:
                print('request attempt %s URLError' % str(i + 1))
            except http.client.RemoteDisconnected:
                print('request attempt %s RemoteDisconnected' % str(i + 1))
            except http.client.IncompleteRead:
                print('request attempt %s IncompleteRead' % str(i + 1))
            except:
                #print(e)
                import traceback  
                traceback.print_exc()
    
    queue = Queue(1)
    pool.spawn(_getUrl,queue,oUrl, encoding, headers, data, method,allowCache)
    return queue.get()
        
def url_size(url, headers = {}):
    if headers:
        response = urllib.request.urlopen(urllib.request.Request(url, headers = headers), None)
    else:
        response = urllib.request.urlopen(url)

    size = response.headers['content-length']
    return int(size) if size!=None else float('inf')

    
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
        
def gen_bitrate(size_byte, time_s, unit_k=1024):
    if (size_byte <= 0) or (time_s <= 0):
        return '-1'	# can not gen bitrate
    raw_rate = size_byte * 8 / time_s	# bps
    kbps = raw_rate / unit_k
    bitrate = str(round(kbps, 1)) + 'kbps'
    return bitrate
   
# make a 2.3 number, with given length after .
def num_len(n, l=3):
    t = str(float(n))
    p = t.split('.')
    if l < 1:
        return p[0]
    if len(p[1]) > l:
        p[1] = p[1][:l]
    while len(p[1]) < l:
        p[1] += '0'
    t = ('.').join(p)
    # done
    return t

# byte to size
def byte2size(size_byte, flag_add_byte=False):
    
    unit_list = [
        'Byte', 
        'KB', 
        'MB', 
        'GB', 
        'TB', 
        'PB', 
        'EB', 
    ]
    
    # check size_byte
    size_byte = int(size_byte)
    if size_byte < 1024:
        return size_byte + unit_list[0]
    
    # get unit
    unit_i = math.floor(math.log(size_byte, 1024))
    unit = unit_list[unit_i]
    size_n = size_byte / pow(1024, unit_i)
    
    size_t = num_len(size_n, 2)
    
    # make final size_str
    size_str = size_t + ' ' + unit
    
    # check flag
    if flag_add_byte:
        size_str += ' (' + str(size_byte) + ' Byte)'
    # done
    return size_str
    
# DEPRECATED in favor of match1()
def r1(pattern, text):
    m = re.search(pattern, text)
    if m:
        return m.group(1)
        
def debug(input):
    print (((str(input))).encode('gbk', 'ignore').decode('gbk') )
        
class Parser(object):
    filters = []
    def Parse(self,url,types=None):
        pass
    def ParseURL(self,url,label,min=None,max=None):
        pass
    def getfilters(self):
        return self.filters
    def closeParser(self):
        return
        
class UrlHandle():
    filters = []
    def urlHandle(url):
        pass
    def getfilters(self):
        return self.filters
    def closeUrlHandle(self):
        return