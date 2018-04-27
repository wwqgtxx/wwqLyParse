import ctypes, sysconfig, logging

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
    lib_wwqLyParse.parse.argtypes = [ctypes.c_char_p, ctypes.c_int,
                                     ctypes.POINTER(ctypes.POINTER(ctypes.c_char)),
                                     ctypes.POINTER(ctypes.c_int)]
    lib_wwqLyParse.get_uuid.restype = ctypes.c_char_p
    lib_wwqLyParse.get_name.restype = ctypes.c_char_p
    logging.debug("successful load lib_wwqLyParse %s" % lib_wwqLyParse)


init_lib()

get_uuid = lib_wwqLyParse.get_uuid
get_name = lib_wwqLyParse.get_name


def _lib_parse(byte_str: bytes):
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


if POOL_TYPE == "geventpool":
    def lib_parse(byte_str: bytes):
        return common_threadpool.apply(_lib_parse, args=(byte_str,))
else:
    lib_parse = _lib_parse
