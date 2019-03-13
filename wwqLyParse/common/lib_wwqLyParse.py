import ctypes, sysconfig, logging, weakref


class LibWwqLyParseBase(object):
    def __init__(self):
        from .for_path import get_real_path
        if sysconfig.get_platform() == "win-amd64":
            self.lib_path = get_real_path("./wwqLyParse64.dll")
        else:
            self.lib_path = get_real_path("./wwqLyParse32.dll")
        self.ffi = None

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
    int64_t atomic_int64_sub(void* ptr, int64_t val);
    int64_t atomic_int64_and(void* ptr, int64_t val);
    int64_t atomic_int64_or(void* ptr, int64_t val);
    int64_t atomic_int64_xor(void* ptr, int64_t val);
    
    typedef union epoll_data {
      void* ptr;
      int fd;
      uint32_t u32;
      uint64_t u64;
      uintptr_t sock; /* Windows specific */
      void* hnd;  /* Windows specific */
    } epoll_data_t;
    
    typedef struct {
      uint32_t events;   /* Epoll events and flags */
      epoll_data_t data; /* User data variable */
    } epoll_event ;
    
    void* epoll_create(int size);
    void* epoll_create1(int flags);
    int epoll_close(void* ephnd);
    int epoll_ctl(void* ephnd, int op, uintptr_t sock, epoll_event* event);
    int epoll_wait(void* ephnd, epoll_event* events, int maxevents, int timeout);
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
        self.lib.atomic_int64_sub.argtypes = [ctypes.c_void_p, ctypes.c_int64]
        self.lib.atomic_int64_sub.restype = ctypes.c_int64
        self.lib.atomic_int64_and.argtypes = [ctypes.c_void_p, ctypes.c_int64]
        self.lib.atomic_int64_and.restype = ctypes.c_int64
        self.lib.atomic_int64_or.argtypes = [ctypes.c_void_p, ctypes.c_int64]
        self.lib.atomic_int64_or.restype = ctypes.c_int64
        self.lib.atomic_int64_xor.argtypes = [ctypes.c_void_p, ctypes.c_int64]
        self.lib.atomic_int64_xor.restype = ctypes.c_int64
        try:
            self.lib.epoll_create.argtypes = [ctypes.c_int]
            self.lib.epoll_create.restype = ctypes.c_void_p
            self.lib.epoll_create1.argtypes = [ctypes.c_int]
            self.lib.epoll_create1.restype = ctypes.c_void_p
            self.lib.epoll_close.argtypes = [ctypes.c_void_p]
            self.lib.epoll_close.restype = ctypes.c_int

            self.c_uint_p = ctypes.POINTER(ctypes.c_uint)

            class c_epoll_data(ctypes.Union):
                _fields_ = [
                    ("ptr", ctypes.c_void_p),
                    ("fd", ctypes.c_int),
                    ("u32", ctypes.c_uint32),
                    ("u64", ctypes.c_uint64),
                    ("sock", self.c_uint_p),
                    ("hnd", ctypes.c_void_p),
                ]

            self.c_epoll_data = c_epoll_data

            class c_epoll_event(ctypes.Structure):
                _fields_ = [
                    ("events", ctypes.c_uint32),
                    ("data", self.c_epoll_data),
                ]

            self.c_epoll_event = c_epoll_event
            self.c_epoll_event_p = ctypes.POINTER(c_epoll_event)

            self.lib.epoll_ctl.argtypes = [ctypes.c_void_p, ctypes.c_int, self.c_uint_p, self.c_epoll_event_p]
            self.lib.epoll_ctl.restype = ctypes.c_int
            self.lib.epoll_wait.argtypes = [ctypes.c_void_p, self.c_epoll_event_p, ctypes.c_int, ctypes.c_int]
            self.lib.epoll_wait.restype = ctypes.c_int
        except AttributeError:
            pass

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

if hasattr(lib_wwqLyParse.lib, "epoll_create1"):
    class WEPoll(object):
        EPOLLIN = (1 << 0)
        EPOLLPRI = (1 << 1)
        EPOLLOUT = (1 << 2)
        EPOLLERR = (1 << 3)
        EPOLLHUP = (1 << 4)
        EPOLLRDNORM = (1 << 6)
        EPOLLRDBAND = (1 << 7)
        EPOLLWRNORM = (1 << 8)
        EPOLLWRBAND = (1 << 9)
        EPOLLMSG = (1 << 10)  # /* Never reported. */
        EPOLLRDHUP = (1 << 13)
        EPOLLONESHOT = (1 << 31)

        EPOLL_CTL_ADD = 1
        EPOLL_CTL_MOD = 2
        EPOLL_CTL_DEL = 3

        EPOLL_CLOEXEC = 0
        INT_MAX = 2147483647
        FD_SETSIZE = 512
        EBADF = 6

        def __init__(self):
            self.handle = lib_wwqLyParse.lib.epoll_create1(WEPoll.EPOLL_CLOEXEC)
            self.finalize = weakref.finalize(self, lib_wwqLyParse.lib.epoll_close, self.handle).detach()

        def close(self):
            self.finalize()
            self.handle = None

        @property
        def closed(self):
            return self.handle is None

        @property
        def fileno(self):
            return self.handle

        if lib_wwqLyParse.ffi is None:
            def _new_ev(self):
                ev = lib_wwqLyParse.c_epoll_event()
                evp = ctypes.pointer(ev)
                return ev, evp

            def _ignore_closed(self, result):
                if ctypes.get_errno() == WEPoll.EBADF:
                    # /* fd already closed */
                    ctypes.set_errno(0)
                    result = 0
                return result

            def _new_evs(self, maxevents):
                return (lib_wwqLyParse.c_epoll_event * maxevents)()

            def _raise_error(self):
                raise ctypes.WinError()
        else:
            def _new_ev(self):
                evp = lib_wwqLyParse.ffi.new("epoll_event*")
                ev = evp[0]
                return ev, evp

            def _ignore_closed(self, result):
                if lib_wwqLyParse.ffi.errno == WEPoll.EBADF:
                    # /* fd already closed */
                    lib_wwqLyParse.ffi.errno = 0
                    result = 0
                return result

            def _new_evs(self, maxevents):
                return lib_wwqLyParse.ffi.new("epoll_event[]", maxevents)

            def _raise_error(self):
                raise WindowsError(*lib_wwqLyParse.ffi.getwinerror())

        def ctl(self, op, fd, events):
            ev, evp = self._new_ev()
            ev.events = events
            ev.data.fd = fd
            fd = ev.data.sock
            result = lib_wwqLyParse.lib.epoll_ctl(self.handle, op, fd, evp)
            if op == WEPoll.EPOLL_CTL_DEL:
                result = self._ignore_closed(result)
            if result < 0:
                self._raise_error()
            _ = (ev, evp)  # ensure not gc before here!!!
            return result

        def register(self, fd, eventmask=EPOLLIN | EPOLLPRI | EPOLLOUT):
            return self.ctl(WEPoll.EPOLL_CTL_ADD, fd, eventmask)

        def modify(self, fd, eventmask):
            return self.ctl(WEPoll.EPOLL_CTL_MOD, fd, eventmask)

        def unregister(self, fd):
            return self.ctl(WEPoll.EPOLL_CTL_DEL, fd, 0)

        def poll(self, timeout=-1, maxevents=-1):
            if timeout > 0:
                timeout = round(timeout * 1000)
            if timeout > WEPoll.INT_MAX:
                raise OverflowError("timeout is too large")
            if timeout < 0:
                timeout = -1
            if maxevents == -1:
                maxevents = WEPoll.FD_SETSIZE - 1
            elif maxevents < 1:
                raise ValueError("maxevents must be greater than 0, got %d" % maxevents)
            evs = self._new_evs(maxevents)
            nfds = lib_wwqLyParse.lib.epoll_wait(self.handle, evs, maxevents, timeout)
            if nfds < 0:
                self._raise_error()
            elist = list()
            for i in range(nfds):
                etuple = evs[i].data.fd, evs[i].events
                elist.append(etuple)
            _ = evs  # ensure not gc before here!!!
            return elist


    import selectors
    import math


    class WEPollSelector(selectors._PollLikeSelector):
        """Epoll-based selector."""
        _selector_cls = WEPoll
        _EVENT_READ = WEPoll.EPOLLIN
        _EVENT_WRITE = WEPoll.EPOLLOUT

        def fileno(self):
            return self._selector.fileno()

        def select(self, timeout=None):
            if timeout is None:
                timeout = -1
            elif timeout <= 0:
                timeout = 0
            else:
                # epoll_wait() has a resolution of 1 millisecond, round away
                # from zero to wait *at least* timeout seconds.
                timeout = math.ceil(timeout * 1e3) * 1e-3

            # epoll_wait() expects `maxevents` to be greater than zero;
            # we want to make sure that `select()` can be called when no
            # FD is registered.
            max_ev = max(len(self._fd_to_key), 1)

            ready = []
            try:
                fd_event_list = self._selector.poll(timeout, max_ev)
            except InterruptedError:
                return ready
            for fd, event in fd_event_list:
                events = 0
                if event & ~WEPoll.EPOLLIN:
                    events |= selectors.EVENT_WRITE
                if event & ~WEPoll.EPOLLOUT:
                    events |= selectors.EVENT_READ

                key = self._key_from_fd(fd)
                if key:
                    ready.append((key, events & key.events))
            return ready

        def close(self):
            self._selector.close()
            super().close()


    selectors.DefaultSelector = WEPollSelector


class AtomicInt64(object):
    __slots__ = ["handle", "__weakref__"]

    def __init__(self):
        self.handle = lib_wwqLyParse.lib.atomic_int64_init()
        weakref.finalize(self, lib_wwqLyParse.lib.atomic_int64_destroy, self.handle)

    def get(self) -> int:
        return lib_wwqLyParse.lib.atomic_int64_get(self.handle)

    def set(self, val: int) -> int:
        return lib_wwqLyParse.lib.atomic_int64_set(self.handle, val)

    def __iadd__(self, other: int):
        lib_wwqLyParse.lib.atomic_int64_add(self.handle, other)
        return self

    def __isub__(self, other: int):
        lib_wwqLyParse.lib.atomic_int64_sub(self.handle, other)
        return self

    def __iand__(self, other: int):
        lib_wwqLyParse.lib.atomic_int64_and(self.handle, other)
        return self

    def __ior__(self, other: int):
        lib_wwqLyParse.lib.atomic_int64_or(self.handle, other)
        return self

    def __ixor__(self, other: int):
        lib_wwqLyParse.lib.atomic_int64_xor(self.handle, other)
        return self


async def lib_parse_async(byte_str: bytes) -> bytes:
    from . import asyncio
    return await asyncio.async_run_func_or_co(lib_parse, byte_str)

# if POOL_TYPE == "geventpool":
#     def lib_parse(byte_str: bytes):
#         return get_common_real_thread_pool().apply(lib_wwqLyParse.lib_parse, args=(byte_str,))
# else:
#     lib_parse = lib_wwqLyParse.lib_parse
