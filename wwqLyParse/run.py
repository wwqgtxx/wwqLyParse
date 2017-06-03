#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>

CONFIG = {
    "host": "127.0.0.1",
    "port": 5000,
    "uuid": '{C35B9DFC-559F-49E2-B80B-79B66EC77471}'
}
if __name__ == '__main__':
    CONFIG["port"] = 8000

import urllib.request, json, sys, subprocess, time, logging, traceback

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d]<%(funcName)s> %(threadName)s %(levelname)s : %(message)s',
                    datefmt='%H:%M:%S', stream=sys.stdout)

import os
import socket

try:
    from .lib import bridge
except Exception as e:
    from lib import bridge


def get_caller_info():
    try:
        fn, lno, func, sinfo = traceback.extract_stack()[-3]
    except ValueError:  # pragma: no cover
        fn, lno, func = "(unknown file)", 0, "(unknown function)"
    try:
        fn = os.path.basename(fn)
    except:
        pass
    callmethod = "<%s:%d %s> " % (fn, lno, func)
    return callmethod


def get_systeminfo():
    try:
        args = "systeminfo"
        PIPE = subprocess.PIPE
        p = subprocess.Popen(args, stdout=PIPE, stderr=PIPE, shell=False)
        stdout, stderr = p.communicate()
        stdout = bridge.try_decode(stdout)
        stderr = bridge.try_decode(stderr)
        global systeminfo
        systeminfo = stdout
    except:
        systeminfo = ""


get_systeminfo()


def isX64():
    if "x64-based PC" in systeminfo:
        logging.info("x64")
        return True
    elif "x86-based PC" in systeminfo:
        logging.info("x86")
        return False
    else:
        logging.info("UnKnow")
        return False


def isXP():
    if "Windows XP" in systeminfo:
        logging.info("XP")
        return True
    else:
        return False


def is2003():
    if "Server 2003" in systeminfo:
        logging.info("2003")
        return True
    else:
        return False


def makePython():
    global EMBED_PYTHON
    if isX64():
        EMBED_PYTHON = "./lib/python-3.6.1-embed-amd64/wwqLyParse64.exe"
    else:
        EMBED_PYTHON = "./lib/python-3.6.1-embed-win32/wwqLyParse32.exe"
    logging.info("set EMBED_PYTHON = " + EMBED_PYTHON)


makePython()


def checkEmbedPython():
    global useEmbedPython
    useEmbedPython = True
    if isXP() or is2003() or (systeminfo == ""):
        useEmbedPython = False
        return
    y_bin = bridge.pn(bridge.pjoin(bridge.get_root_path(), './printok.py'))
    try:
        py_bin = bridge.pn(bridge.pjoin(bridge.get_root_path(), EMBED_PYTHON))
    except:
        useEmbedPython = False
        return
    args = [py_bin, y_bin]
    logging.info(args)
    PIPE = subprocess.PIPE
    try:
        p = subprocess.Popen(args, stdout=PIPE, stderr=None, shell=False)
    except:
        logging.exception("error")
        useEmbedPython = False
        return
    stdout, stderr = p.communicate()
    stdout = bridge.try_decode(stdout)
    # stderr = bridge.try_decode(stderr)
    logging.info(stdout)
    if "ok" not in stdout:
        useEmbedPython = False


checkEmbedPython()


def IsOpen(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, int(port)))
        s.shutdown(2)
        logging.info(get_caller_info() + '%d is open' % port)
        return True
    except:
        logging.info(get_caller_info() + '%d is down' % port)
        return False


def _run_main():
    y_bin = bridge.pn(bridge.pjoin(bridge.get_root_path(), './main.py'))
    if useEmbedPython:
        logging.info("use Embed Python")
        py_bin = bridge.pn(bridge.pjoin(bridge.get_root_path(), EMBED_PYTHON))
    else:
        logging.info("don't use Embed Python")
        py_bin = sys.executable
    if "PyRun.exe" in py_bin:
        args = [py_bin, '--normal', y_bin]
    else:
        args = [py_bin, y_bin]
    args += ['--host', CONFIG["host"]]
    args += ['--port', str(CONFIG["port"])]
    logging.info(args)
    p = subprocess.Popen(args, shell=False, cwd=bridge.get_root_path(), close_fds=True)


def init():
    for n in range(2):
        if not IsOpen(CONFIG["host"], CONFIG["port"]):
            _run_main()
        else:
            return
        for i in range(100):
            if not IsOpen(CONFIG["host"], CONFIG["port"]):
                time.sleep(0.05)
            else:
                return
        for i in range(10):
            if not IsOpen(CONFIG["host"], CONFIG["port"]):
                time.sleep(1)
            else:
                return
        global useEmbedPython
        useEmbedPython = False
    raise Exception("can't init server")


def process(url, values, willRefused=False, needresult=True, needjson=True):
    data = urllib.parse.urlencode(values).encode(encoding='UTF8')
    logging.info(data)
    req = urllib.request.Request(url, data)
    # req.add_header('Referer', 'http://www.python.org/')
    for n in range(3):
        try:
            if willRefused:
                try:
                    urllib.request.urlopen(req)
                    return
                except:
                    return
            for i in range(10):
                try:
                    response = urllib.request.urlopen(req)
                    break
                except socket.timeout:
                    logging.info('request attempt %s timeout' % str(i + 1))
            if needresult:
                the_page = response.read()
                if needjson:
                    results = json.loads(the_page.decode('UTF8'))
                else:
                    the_page.decode('UTF8')
                return results
            else:
                return
        except Exception as e:
            # logging.info(e)
            import traceback
            traceback.print_exc()
    raise Exception("can't process " + str(url) + str(values))


def closeServer():
    for n in range(2):
        if IsOpen(CONFIG["host"], CONFIG["port"]):
            url = 'http://%s:%d/close' % (CONFIG["host"], CONFIG["port"])
            values = {"uuid": CONFIG["uuid"]}
            process(url, values, willRefused=True)
            for n in range(100):
                if not IsOpen(CONFIG["host"], CONFIG["port"]):
                    return
                time.sleep(0.05)
            for n in range(5):
                if not IsOpen(CONFIG["host"], CONFIG["port"]):
                    return
                time.sleep(1)
        return
    raise Exception("can't closeServer")


def getVersion(needclose=True):
    for n in range(3):
        try:
            if needclose:
                closeServer()
            init()
            url = 'http://%s:%d/GetVersion' % (CONFIG["host"], CONFIG["port"])
            # user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
            values = {"uuid": CONFIG["uuid"]}
            results = process(url, values)
            assert results["uuid"] == CONFIG["uuid"]
            global version
            version = results
            logging.info(version)
            return
        except:
            logging.exception("getVersion fail on %s:%d" % (CONFIG["host"], CONFIG["port"]))
        CONFIG["port"] += 1


getVersion()


def Cleanup():
    closeServer()


def GetVersion(debug=False):
    if (not debug):
        closeServer()
    return version


def Parse(input_text, types=None, parsers_name=None, urlhandles_name=None):
    for n in range(3):
        try:
            init()
            url = 'http://%s:%d/Parse' % (CONFIG["host"], CONFIG["port"])
            # user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
            values = {}
            values["input_text"] = input_text
            values["types"] = types
            values["parsers_name"] = parsers_name
            values["urlhandles_name"] = urlhandles_name
            jjson = json.dumps(values)
            values = {"json": jjson, "uuid": CONFIG["uuid"]}
            results = process(url, values)
            return results
        except Exception as e:
            # logging.info(e)
            import traceback
            traceback.print_exc()
            error = e
    raise error


def ParseURL(input_text, label, min=None, max=None, urlhandles_name=None):
    for n in range(3):
        try:
            init()
            url = 'http://%s:%d/ParseURL' % (CONFIG["host"], CONFIG["port"])
            # user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
            values = {}
            values["input_text"] = input_text
            values["label"] = label
            values["min"] = min
            values["max"] = max
            values["urlhandles_name"] = urlhandles_name
            jjson = json.dumps(values)
            values = {"json": jjson, "uuid": CONFIG["uuid"]}
            results = process(url, values)
            return results
        except Exception as e:
            # logging.info(e)
            import traceback
            traceback.print_exc()
            error = e
    raise error


def debug(input):
    info = "\n------------------------------------------------------------\n"
    info += ((str(input))).encode('gbk', 'ignore').decode('gbk')
    info += "\n------------------------------------------------------------"
    logging.debug(info)


def main():
    # debug(GetVersion())
    # Cleanup()
    # debug(Parse('http://www.iqiyi.com/lib/m_209445514.html?src=search'))
    # debug(Parse('http://www.iqiyi.com/a_19rrhacdwt.html#vfrm=2-4-0-1'))
    # debug(Parse('http://www.iqiyi.com/a_19rrhaare5.html'))
    # debug(Parse('http://www.iqiyi.com/a_19rrhbhf6d.html#vfrm=2-3-0-1'))
    # debug(Parse('http://www.le.com'))
    # debug(Parse('http://www.letv.com/comic/10010294.html'))
    # debug(Parse('http://www.mgtv.com/v/1/1/'))
    # debug(Parse('http://tv.le.com/'))
    # debug(Parse('http://search.pptv.com/s_video?kw=%E5%B1%B1%E6%B5%B7%E7%BB%8F%E4%B9%8B%E8%B5%A4%E5%BD%B1%E4%BC%A0%E8%AF%B4'))
    # debug(Parse('http://www.youku.com/'))
    # debug(Parse('http://tv.sohu.com/drama/'))
    # debug(Parse('http://mv.yinyuetai.com/'))
    # debug(Parse('http://v.qq.com/tv/'))
    # debug(Parse('http://www.pptv.com/'))
    # debug(Parse('http://yyfm.xyz/video/album/1300046802.html'))
    # debug(Parse('http://www.iqiyi.com/playlist392712002.html',"collection"))
    # debug(Parse('http://list.iqiyi.com/www/2/----------------iqiyi--.html'))
    # debug(Parse('http://www.iqiyi.com/a_19rrhb8fjp.html',"list"))
    debug(Parse('http://www.iqiyi.com/v_19rrl8pmn8.html#vfrm=2-3-0-1'))
    # debug(Parse('http://www.iqiyi.com/v_19rrl8pmn8.html',"formats",parsers_name=["IQiYiParser"]))
    # debug(Parse('http://www.iqiyi.com/v_19rrl8pmn8.html',"formats",parsers_name=["PVideoParser"]))
    # debug(Parse('http://www.iqiyi.com/v_19rrl8pmn8.html'))
    # debug(ParseURL("http://www.iqiyi.com/v_19rrl8pmn8.html","2.0@PVideoParser"))
    # #debug(ParseURL("http://www.iqiyi.com/v_19rrl8pmn8.html","fullhd@IQiYiParser"))
    # debug(Parse('http://v.pptv.com/show/NWR29Yzj2hh7ibWE.html?rcc_src=S1'))
    # debug(Parse('http://www.bilibili.com/video/av2557971/')) #don't support
    # debug(Parse('http://v.baidu.com/link?url=dm_10tBNoD-LLAMb79CB_p0kxozuoJcW0SiN3eycdo6CdO3GZgQm26uOzZh9fqcNSWZmz9aU9YYCCfT0NmZoGfEMoznyHhz3st-QvlOeyArYdIbhzBbdIrmntA4h1HsSampAs4Z3c17r_exztVgUuHZqChPeZZQ4tlmM5&page=tvplaydetail&vfm=bdvtx&frp=v.baidu.com%2Ftv_intro%2F&bl=jp_video',"formats"))
    # debug(Parse('http://www.hunantv.com/v/1/291976/c/3137384.html',parsers_name=["IMgTVParser"]))
    # debug(ParseURL('http://www.mgtv.com/v/1/291976/c/3137384.html',"3@MgTVParser"))
    # debug(Parse('http://v.youku.com/v_show/id_XMTYxODUxOTEyNA==.html?f=27502474'))
    # debug(Parse('http://v.qq.com/cover/y/yxpn9yol52go2i6.html?vid=f0141icyptp'))
    # debug(ParseURL('http://v.qq.com/cover/y/yxpn9yol52go2i6.html?vid=f0141icyptp','4_1080p____-1x-1_2521.9kbps_09:35.240_1_mp4_@LypPvParser'))
    Cleanup()


if __name__ == '__main__':
    # app.run()
    try:
        main()
    finally:
        Cleanup()
