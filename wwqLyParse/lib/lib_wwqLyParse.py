import subprocess, ctypes, sysconfig

try:
    from ..common import *
except Exception as e:
    from common import *

lib_wwqLyParse = None


def init_lib():
    global lib_wwqLyParse
    if sysconfig.get_platform() == "win-amd64":
        lib_wwqLyParse = ctypes.cdll.LoadLibrary(get_real_path("./wwqLyParse64.dll"))
    else:
        lib_wwqLyParse = ctypes.cdll.LoadLibrary(get_real_path("./wwqLyParse32.dll"))


init_lib()


def lib_parse(byte_str):
    p = ctypes.c_char_p(byte_str)
    lib_wwqLyParse.parse(p, len(byte_str))
    return byte_str
