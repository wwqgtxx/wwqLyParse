import ctypes, sysconfig, logging, weakref


class LibWwqLyParseBase(object):
    def __init__(self):
        from .for_path import get_real_path
        if sysconfig.get_platform() == "win-amd64":
            self.lib_path = get_real_path("./wwqLyParse64.dll")
        else:
            self.lib_path = get_real_path("./wwqLyParse32.dll")

    def get_uuid(self) -> bytes:
        raise NotImplementedError

    def get_name(self) -> bytes:
        raise NotImplementedError

    def lib_parse(self, byte_str: bytes) -> bytes:
        raise NotImplementedError


class LibWwqParseCFFI(LibWwqLyParseBase):
    def __init__(self):
        super(LibWwqParseCFFI, self).__init__()
        from cffi import FFI
        self.ffi = FFI()
        self.lib = self.ffi.dlopen(self.lib_path)
        self.ffi.cdef("""
    char * get_uuid();
    char * get_name();
    int parse(char * c,int length,char **result,int *result_length);
    int free_str(char * c);
    void* atomic_int64_init();
    int atomic_int64_destroy(void* ptr);
    int64_t atomic_int64_get(void* ptr);
    int64_t atomic_int64_set(void* ptr, int64_t val);
    int64_t atomic_int64_add(void* ptr, int64_t val);
        """)
        self.lib.__class__.__repr__ = lambda s: "<%s object at 0x%016X>" % (s.__class__.__name__, id(s))
        logging.debug("successful load lib %s" % self.lib)
        weakref.finalize(self,
                         lambda: logging.debug("%s released" % self.lib) if self.ffi.dlclose(self.lib) or 1 else None)

    def get_uuid(self) -> bytes:
        return self.ffi.string(self.lib.get_uuid())

    def get_name(self) -> bytes:
        return self.ffi.string(self.lib.get_name())

    def lib_parse(self, byte_str: bytes) -> bytes:
        length = self.ffi.cast("int", len(byte_str))
        result_length = self.ffi.new("int *")
        result_p = self.ffi.new("char **")
        # p = self.ffi.new("char []", byte_str)
        p = self.ffi.from_buffer(byte_str)
        self.lib.parse(p, length, result_p, result_length)
        result = self.ffi.unpack(result_p[0], result_length[0])
        self.lib.free_str(result_p[0])
        return result


class LibWwqParseCtypes(LibWwqLyParseBase):
    def __init__(self):
        super(LibWwqParseCtypes, self).__init__()
        self.lib = ctypes.cdll.LoadLibrary(self.lib_path)
        self.lib.parse.argtypes = [ctypes.c_char_p, ctypes.c_int,
                                   ctypes.POINTER(ctypes.POINTER(ctypes.c_char)),
                                   ctypes.POINTER(ctypes.c_int)]
        self.lib.get_uuid.restype = ctypes.c_char_p
        self.lib.get_name.restype = ctypes.c_char_p
        self.lib.atomic_int64_init.restype = ctypes.c_void_p
        self.lib.atomic_int64_destroy.argtypes = [ctypes.c_void_p]
        self.lib.atomic_int64_get.argtypes = [ctypes.c_void_p]
        self.lib.atomic_int64_get.restype = ctypes.c_int64
        self.lib.atomic_int64_set.argtypes = [ctypes.c_void_p, ctypes.c_int64]
        self.lib.atomic_int64_set.restype = ctypes.c_int64
        self.lib.atomic_int64_add.argtypes = [ctypes.c_void_p, ctypes.c_int64]
        self.lib.atomic_int64_add.restype = ctypes.c_int64

        logging.debug("successful load lib %s" % self.lib)

    def get_uuid(self) -> bytes:
        return self.lib.get_uuid()

    def get_name(self) -> bytes:
        return self.lib.get_name()

    def lib_parse(self, byte_str: bytes) -> bytes:
        length = len(byte_str)
        result_length = ctypes.c_int()
        result_p = ctypes.POINTER(ctypes.c_char)()
        # p = ctypes.create_string_buffer(byte_str, length)
        p = ctypes.c_char_p(byte_str)
        self.lib.parse(p, length, ctypes.byref(result_p), ctypes.byref(result_length))
        result_arr = ctypes.cast(result_p, ctypes.POINTER(ctypes.c_char * result_length.value)).contents
        result = b''.join(result_arr)
        self.lib.free_str(result_p)
        return result


try:
    lib_wwqLyParse = LibWwqParseCFFI()
except:
    lib_wwqLyParse = LibWwqParseCtypes()

get_uuid = lib_wwqLyParse.get_uuid
get_name = lib_wwqLyParse.get_name
lib_parse = lib_wwqLyParse.lib_parse


class AtomicInt64(object):
    def __init__(self):
        self.lib = lib_wwqLyParse.lib
        self.handle = self.lib.atomic_int64_init()

    def __del__(self):
        self.lib.atomic_int64_destroy(self.handle)

    def get(self):
        return self.lib.atomic_int64_get(self.handle)

    def set(self, val: int):
        return self.lib.atomic_int64_set(self.handle, val)

    def __iadd__(self, other: int):
        self.lib.atomic_int64_add(self.handle, other)
        return self


async def lib_parse_async(byte_str: bytes) -> bytes:
    from . import asyncio
    return await asyncio.async_run_func_or_co(lib_parse, byte_str)

# if POOL_TYPE == "geventpool":
#     def lib_parse(byte_str: bytes):
#         return get_common_real_thread_pool().apply(lib_wwqLyParse.lib_parse, args=(byte_str,))
# else:
#     lib_parse = lib_wwqLyParse.lib_parse
