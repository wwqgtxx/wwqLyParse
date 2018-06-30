#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>

CONFIG = {
    "pipe": 'wwqLyParse',
    "uuid": '{C35B9DFC-559F-49E2-B80B-79B66EC77471}',
    "version": ''
}

import json, sys, subprocess, time, logging, traceback, ctypes, sysconfig
import multiprocessing
import multiprocessing.connection

try:
    import _winapi
except:
    _winapi = None

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d]<%(funcName)s> %(threadName)s %(levelname)s : %(message)s',
                    datefmt='%H:%M:%S', stream=sys.stdout)

import os
import socket


def get_real_root_path():
    return os.path.dirname(os.path.abspath(__file__))


def get_real_path(abstract_path):
    return os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), abstract_path))


need_close = True
if __name__ == '__main__':
    pass
else:
    try:
        with open(get_real_path('../../../ver.txt')) as f:
            ver = f.readline()
            if "2016" in ver or "2015" in ver:
                MessageBox = ctypes.windll.user32.MessageBoxW
                MessageBox(None, '你的猎影版本太低，请更新你的猎影到最新版本!', '错误', 0x00000010)
                sys.exit(5)
    except SystemExit as e:
        raise e
    except:
        pass
    logging.info(get_real_path('./run.py'))
    if CONFIG["uuid"] in str(get_real_path('./run.py')).replace('_', '-'):
        need_close = False
    logging.info(need_close)

with open(get_real_path('./version.txt')) as f:
    ver = f.readline().strip()
    CONFIG['version'] = ver

address = r'\\.\pipe\%s@%s' % (CONFIG["pipe"], CONFIG["version"])


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
        args = get_real_path("./SysArch.exe")
        stdout = subprocess.check_output(args, stderr=subprocess.STDOUT)
        stdout = stdout.decode()
        global systeminfo
        systeminfo = stdout
    except:
        systeminfo = ""


get_systeminfo()


def is_64bit():
    if "64bit" in systeminfo:
        logging.info("x64")
        return True
    elif "32bit" in systeminfo:
        logging.info("x86")
        return False
    else:
        logging.info("UnKnow")
        return False


def is_xp():
    if "Windows XP" in systeminfo:
        logging.info("XP")
        return True
    else:
        return False


def is_2003():
    if "Server 2003" in systeminfo:
        logging.info("2003")
        return True
    else:
        return False


lib_wwqLyParse = None


def init_lib():
    global lib_wwqLyParse
    if sysconfig.get_platform() == "win-amd64":
        lib_wwqLyParse = ctypes.cdll.LoadLibrary(get_real_path("./wwqLyParse64.dll"))
    else:
        lib_wwqLyParse = ctypes.cdll.LoadLibrary(get_real_path("./wwqLyParse32.dll"))
    lib_wwqLyParse.parse.argtypes = [ctypes.c_char_p, ctypes.c_int,
                                     ctypes.POINTER(ctypes.POINTER(ctypes.c_char)),
                                     ctypes.POINTER(ctypes.c_int)]
    lib_wwqLyParse.get_uuid.restype = ctypes.c_char_p
    lib_wwqLyParse.get_name.restype = ctypes.c_char_p
    assert lib_wwqLyParse.get_uuid().decode() == CONFIG["uuid"]
    logging.debug("successful load lib_wwqLyParse %s" % lib_wwqLyParse)


init_lib()
get_uuid = lib_wwqLyParse.get_uuid
get_name = lib_wwqLyParse.get_name


def lib_parse(byte_str: bytes):
    length = len(byte_str)
    result_length = ctypes.c_int()
    result_p = ctypes.POINTER(ctypes.c_char)()
    # p = ctypes.create_string_buffer(byte_str, length)
    p = ctypes.c_char_p(byte_str)
    lib_wwqLyParse.parse(p, length, ctypes.byref(result_p), ctypes.byref(result_length))
    result_arr = ctypes.cast(result_p, ctypes.POINTER(ctypes.c_char * result_length.value)).contents
    result = b''.join(result_arr)
    lib_wwqLyParse.free_str(result_p)
    return result


def make_python():
    global EMBED_PYTHON
    if is_64bit():
        EMBED_PYTHON = "./lib/python-3.7.0-embed-amd64/wwqLyParse64.exe"
    else:
        EMBED_PYTHON = "./lib/python-3.7.0-embed-win32/wwqLyParse32.exe"
    logging.info("set EMBED_PYTHON = " + EMBED_PYTHON)


make_python()


def check_embed_python():
    global use_embed_python
    use_embed_python = True
    if is_xp() or is_2003() or (systeminfo == ""):
        use_embed_python = False
        return
    y_bin = get_real_path('./printok.py')
    try:
        py_bin = get_real_path(EMBED_PYTHON)
    except:
        use_embed_python = False
        return
    args = [py_bin, y_bin]
    logging.info(args)
    try:
        stdout = subprocess.check_output(args, stderr=subprocess.STDOUT)
        stdout = stdout.decode()
    except:
        logging.exception("error")
        use_embed_python = False
        return
    logging.info(stdout)
    if "ok" not in stdout:
        use_embed_python = False


check_embed_python()


def is_open(addr):
    try:
        # if _winapi and getattr(_winapi, "WaitNamedPipe", None):
        #     _winapi.WaitNamedPipe(addr, 1000)
        # else:
        with multiprocessing.connection.Client(addr, authkey=get_uuid()) as conn:
            conn.send_bytes(b'')
            pass
        logging.info(get_caller_info() + "'%s' is open" % addr)
        return True
    except multiprocessing.AuthenticationError:
        pass
    except FileNotFoundError:
        pass
    except EOFError:
        pass
    logging.info(get_caller_info() + "'%s' is close" % addr)
    return False


def _run_main():
    y_bin = get_real_path('./main.py')
    if use_embed_python:
        logging.info("use Embed Python")
        py_bin = get_real_path(EMBED_PYTHON)
    else:
        logging.info("don't use Embed Python")
        py_bin = sys.executable
    if "PyRun.exe" in py_bin:
        args = [py_bin, '--normal', y_bin]
    else:
        args = [py_bin, y_bin]
    args += ['--pipe', CONFIG["pipe"]]
    logging.info(args)
    p = subprocess.Popen(args, shell=False, cwd=get_real_root_path(), close_fds=True)
    globals()["p"] = p


def init():
    for n in range(2):
        if not is_open(address):
            _run_main()
        else:
            return
        for i in range(100):
            if not is_open(address):
                time.sleep(0.1)
            else:
                return
        for i in range(10):
            if not is_open(address):
                time.sleep(1)
            else:
                return
        global use_embed_python
        use_embed_python = False
    raise Exception("can't init server")


def process(url, data, will_refused=False, need_result=True) -> dict:
    req = {"type": "get", "url": url, "data": data}
    logging.debug(req)
    req = json.dumps(req)
    req = req.encode("utf-8")
    req = lib_parse(req)
    try:
        with multiprocessing.connection.Client(address, authkey=get_uuid()) as conn:
            conn.send_bytes(req)
            if will_refused:
                return {}
            if need_result:
                results = conn.recv_bytes()
                results = lib_parse(results)
                results = results.decode('utf-8')
                results = json.loads(results)
                results = results["data"]
                return results
            else:
                return {}
    except EOFError:
        if will_refused:
            return {}
        else:
            raise


def close_server():
    try:
        p = globals()["p"]
        p.kill()
        logging.info("successfully kill %s" % (str(p)))
    except:
        pass
    for n in range(2):
        if is_open(address):
            url = 'close'
            values = {}
            process(url, values, will_refused=True)
            for n in range(100):
                if not is_open(address):
                    return
                time.sleep(0.05)
            for n in range(5):
                if not is_open(address):
                    return
                time.sleep(1)
        return
    raise Exception("can't closeServer")


version = None


def get_version():
    global version
    for n in range(3):
        try:
            init()
            url = 'GetVersion'
            values = {}
            results = process(url, values)
            assert results["uuid"] == CONFIG["uuid"]
            assert get_name().decode() in results["name"]
            version = results
            logging.info(version)
            return version
        except AssertionError:
            raise
        except:
            logging.exception("getVersion fail on '%s'" % address)
        if need_close:
            close_server()


def Cleanup():
    close_server()


def GetVersion(debug=False):
    if not version:
        if need_close:
            close_server()
        get_version()
    if not debug:
        close_server()
    return version


def Parse(input_text, types=None, parsers_name=None, urlhandles_name=None):
    error = None
    for n in range(3):
        try:
            init()
            url = 'Parse'
            values = {"input_text": input_text,
                      "types": types,
                      "parsers_name": parsers_name,
                      "urlhandles_name": urlhandles_name
                      }
            results = process(url, values)
            return results
        except Exception as e:
            # logging.info(e)
            import traceback
            traceback.print_exc()
            error = e
    raise error


def ParseURL(input_text, label, min=None, max=None, urlhandles_name=None):
    error = None
    for n in range(3):
        try:
            init()
            url = 'ParseURL'
            values = {"input_text": input_text,
                      "label": label,
                      "min": min,
                      "max": max,
                      "urlhandles_name": urlhandles_name
                      }
            results = process(url, values)
            return results
        except Exception as e:
            # logging.info(e)
            import traceback
            traceback.print_exc()
            error = e
    raise error


def debug(input_str):
    try:
        input_str = json.dumps({"output": input_str}, ensure_ascii=False)
    except:
        pass
    info = "\n------------------------------------------------------------\n"
    info += (str(input_str)).encode('gbk', 'ignore').decode('gbk')
    info += "\n------------------------------------------------------------"
    logging.debug(info)


def main():
    debug(GetVersion())
    # Cleanup()
    # debug(Parse('http://www.iqiyi.com/lib/m_209445514.html?src=search'))
    # debug(Parse('http://www.iqiyi.com/a_19rrhacdwt.html#vfrm=2-4-0-1'))
    # debug(Parse('http://www.iqiyi.com/v_19rrl8pmn8.html'))
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
    # debug(Parse('http://www.iqiyi.com/v_19rrl8pmn8.html#vfrm=2-3-0-1'))
    # debug(Parse('http://www.iqiyi.com/v_19rrl8pmn8.html',"formats",parsers_name=["IQiYiParser"]))
    # debug(Parse('http://www.iqiyi.com/v_19rrl8pmn8.html',"formats",parsers_name=["PVideoParser"]))
    # debug(Parse('http://www.iqiyi.com/v_19rrl8pmn8.html'))
    # debug(ParseURL("http://www.iqiyi.com/v_19rrl8pmn8.html", "1080P-H264@IQiYiParser"))
    # debug(Parse('http://v.pptv.com/show/NWR29Yzj2hh7ibWE.html?rcc_src=S1'))
    # debug(Parse('http://www.bilibili.com/video/av2557971/')) #don't support
    # debug(Parse('http://v.baidu.com/link?url=dm_10tBNoD-LLAMb79CB_p0kxozuoJcW0SiN3eycdo6CdO3GZgQm26uOzZh9fqcNSWZmz9aU9YYCCfT0NmZoGfEMoznyHhz3st-QvlOeyArYdIbhzBbdIrmntA4h1HsSampAs4Z3c17r_exztVgUuHZqChPeZZQ4tlmM5&page=tvplaydetail&vfm=bdvtx&frp=v.baidu.com%2Ftv_intro%2F&bl=jp_video',"formats"))
    # debug(Parse('https://www.mgtv.com/b/318221/4222532.html',parsers_name=["MgTVParser"]))
    # debug(ParseURL('https://www.mgtv.com/b/318221/4222532.html', "3@MgTVParser"))
    # debug(Parse('http://v.youku.com/v_show/id_XMTYxODUxOTEyNA==.html?f=27502474'))
    # debug(Parse('http://v.qq.com/cover/y/yxpn9yol52go2i6.html?vid=f0141icyptp'))
    # debug(ParseURL('http://v.qq.com/cover/y/yxpn9yol52go2i6.html?vid=f0141icyptp','4_1080p____-1x-1_2521.9kbps_09:35.240_1_mp4_@LypPvParser'))
    # Cleanup()


if __name__ == '__main__':
    # app.run()
    try:
        main()
    finally:
        # pass
        Cleanup()
