#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
import multiprocessing.connection
from . import asyncio
import sys
import os
import pickle
import copyreg
import io
import struct
import ssl

try:
    import _winapi
    from _winapi import WAIT_OBJECT_0, WAIT_ABANDONED_0, WAIT_TIMEOUT, INFINITE
except ImportError:
    if sys.platform == 'win32':
        raise
    _winapi = None

from multiprocessing import AuthenticationError, BufferTooShort
import multiprocessing.util

BUFSIZE = 8192

MESSAGE_LENGTH = 20

CHALLENGE = b'#CHALLENGE#'
WELCOME = b'#WELCOME#'
FAILURE = b'#FAILURE#'


class _ForkingPickler(pickle.Pickler):
    '''Pickler subclass used by multiprocessing.'''
    _extra_reducers = {}
    _copyreg_dispatch_table = copyreg.dispatch_table

    def __init__(self, *args):
        super().__init__(*args)
        self.dispatch_table = self._copyreg_dispatch_table.copy()
        self.dispatch_table.update(self._extra_reducers)

    @classmethod
    def register(cls, type, reduce):
        '''Register a reduce function for a type.'''
        cls._extra_reducers[type] = reduce

    @classmethod
    def dumps(cls, obj, protocol=None):
        buf = io.BytesIO()
        cls(buf, protocol).dump(obj)
        return buf.getbuffer()

    loads = pickle.loads


class _AsyncConnectionBase:
    _handle = None

    def __init__(self, handle, readable=True, writable=True, server_side=False):
        handle = handle.__index__()
        if handle < 0:
            raise ValueError("invalid handle")
        if not readable and not writable:
            raise ValueError(
                "at least one of `readable` and `writable` must be True")
        self._handle = handle
        self._readable = readable
        self._writable = writable
        self._server_side = server_side

    # XXX should we use util.Finalize instead of a __del__?

    def __del__(self):
        if self._handle is not None:
            self._close()

    def _check_closed(self):
        if self._handle is None:
            raise OSError("handle is closed")

    def _check_readable(self):
        if not self._readable:
            raise OSError("connection is write-only")

    def _check_writable(self):
        if not self._writable:
            raise OSError("connection is read-only")

    def _bad_message_length(self):
        if self._writable:
            self._readable = False
        else:
            self.close()
        raise OSError("bad message length")

    @property
    def closed(self):
        """True if the connection is closed"""
        return self._handle is None

    @property
    def readable(self):
        """True if the connection is readable"""
        return self._readable

    @property
    def writable(self):
        """True if the connection is writable"""
        return self._writable

    def fileno(self):
        """File descriptor or handle of the connection"""
        self._check_closed()
        return self._handle

    def close(self):
        """Close the connection"""
        if self._handle is not None:
            try:
                self._close()
            finally:
                self._handle = None

    async def send_bytes(self, buf, offset=0, size=None):
        """Send the bytes data from a bytes-like object"""
        self._check_closed()
        self._check_writable()
        m = memoryview(buf)
        # HACK for byte-indexing of non-bytewise buffers (e.g. array.array)
        if m.itemsize > 1:
            m = memoryview(bytes(m))
        n = len(m)
        if offset < 0:
            raise ValueError("offset is negative")
        if n < offset:
            raise ValueError("buffer length < offset")
        if size is None:
            size = n - offset
        elif size < 0:
            raise ValueError("size is negative")
        elif offset + size > n:
            raise ValueError("buffer length < offset + size")
        await self._send_bytes(m[offset:offset + size])

    async def send(self, obj):
        """Send a (picklable) object"""
        self._check_closed()
        self._check_writable()
        await self._send_bytes(_ForkingPickler.dumps(obj))

    async def recv_bytes(self, maxlength=None):
        """
        Receive bytes data as a bytes object.
        """
        self._check_closed()
        self._check_readable()
        if maxlength is not None and maxlength < 0:
            raise ValueError("negative maxlength")
        buf = await self._recv_bytes(maxlength)
        if buf is None:
            self._bad_message_length()
        return buf.getvalue()

    async def recv_bytes_into(self, buf, offset=0):
        """
        Receive bytes data into a writeable bytes-like object.
        Return the number of bytes read.
        """
        self._check_closed()
        self._check_readable()
        with memoryview(buf) as m:
            # Get bytesize of arbitrary buffer
            itemsize = m.itemsize
            bytesize = itemsize * len(m)
            if offset < 0:
                raise ValueError("negative offset")
            elif offset > bytesize:
                raise ValueError("offset too large")
            result = await self._recv_bytes()
            size = result.tell()
            if bytesize < offset + size:
                raise BufferTooShort(result.getvalue())
            # Message can fit in dest
            result.seek(0)
            result.readinto(m[offset // itemsize:
                              (offset + size) // itemsize])
            return size

    async def recv(self):
        """Receive a (picklable) object"""
        self._check_closed()
        self._check_readable()
        buf = await self._recv_bytes()
        return _ForkingPickler.loads(buf.getbuffer())

    async def poll(self):
        """Whether there is any input available to be read"""
        self._check_closed()
        self._check_readable()
        return await self._poll()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        self.close()

    async def deliver_challenge(self, authkey: bytes):
        import hmac
        if not isinstance(authkey, bytes):
            raise ValueError(
                "Authkey must be bytes, not {0!s}".format(type(authkey)))
        message = os.urandom(MESSAGE_LENGTH)
        await self.send_bytes(CHALLENGE + message)
        digest = hmac.new(authkey, message, 'md5').digest()
        response = await self.recv_bytes(256)  # reject large message
        if response == digest:
            await self.send_bytes(WELCOME)
        else:
            await self.send_bytes(FAILURE)
            raise AuthenticationError('digest received was wrong')

    async def answer_challenge(self, authkey: bytes):
        import hmac
        if not isinstance(authkey, bytes):
            raise ValueError(
                "Authkey must be bytes, not {0!s}".format(type(authkey)))
        try:
            message = await self.recv_bytes(256)  # reject large message
            assert message[:len(CHALLENGE)] == CHALLENGE, 'message = %r' % message
            message = message[len(CHALLENGE):]
            digest = hmac.new(authkey, message, 'md5').digest()
            await self.send_bytes(digest)
            response = await self.recv_bytes(256)  # reject large message
            if response != WELCOME:
                raise AuthenticationError('digest sent was rejected')
        except asyncio.LimitOverrunError as e:
            raise AuthenticationError(e)

    async def do_auth(self, authkey: bytes):
        if self._server_side:
            await self.deliver_challenge(authkey)
            await self.answer_challenge(authkey)
        else:
            await self.answer_challenge(authkey)
            await self.deliver_challenge(authkey)

    async def _send_bytes(self, buf):
        raise NotImplemented

    async def _recv_bytes(self, maxsize=None):
        raise NotImplemented

    async def _poll(self):
        raise NotImplemented

    def _close(self):
        raise NotImplemented


def _get_proactor():
    loop = asyncio.get_running_loop()
    assert isinstance(loop, asyncio.ProactorEventLoop)
    proactor = loop._proactor
    return proactor


async def _wait_for_ov(ov):
    proactor = _get_proactor()
    return await proactor.wait_for_handle(ov.event)


_ready_errors = {_winapi.ERROR_BROKEN_PIPE, _winapi.ERROR_NETNAME_DELETED}


class AsyncPipeConnection(_AsyncConnectionBase):
    """
    Connection class based on a Windows named pipe.
    Overlapped I/O is used, so the handles must have been created
    with FILE_FLAG_OVERLAPPED.
    """
    _got_empty_message = False

    def _close(self, _CloseHandle=_winapi.CloseHandle):
        _CloseHandle(self._handle)

    async def _send_bytes(self, buf):
        ov, err = _winapi.WriteFile(self._handle, buf, overlapped=True)
        try:
            if err == _winapi.ERROR_IO_PENDING:
                # waitres = _winapi.WaitForMultipleObjects(
                #                 # [ov.event], False, INFINITE)
                # assert waitres == WAIT_OBJECT_0
                await _wait_for_ov(ov)
        except:
            ov.cancel()
            raise
        finally:
            nwritten, err = ov.GetOverlappedResult(True)
        assert err == 0
        assert nwritten == len(buf)

    async def _recv_bytes(self, maxsize=None):
        if self._got_empty_message:
            self._got_empty_message = False
            return io.BytesIO()
        else:
            bsize = 128 if maxsize is None else min(maxsize, 128)
            try:
                ov, err = _winapi.ReadFile(self._handle, bsize,
                                           overlapped=True)
                try:
                    if err == _winapi.ERROR_IO_PENDING:
                        # waitres = _winapi.WaitForMultipleObjects(
                        #     [ov.event], False, INFINITE)
                        # assert waitres == WAIT_OBJECT_0
                        await _wait_for_ov(ov)
                except:
                    ov.cancel()
                    raise
                finally:
                    nread, err = ov.GetOverlappedResult(True)
                    if err == 0:
                        f = io.BytesIO()
                        f.write(ov.getbuffer())
                        return f
                    elif err == _winapi.ERROR_MORE_DATA:
                        return self._get_more_data(ov, maxsize)
            except OSError as e:
                if e.winerror == _winapi.ERROR_BROKEN_PIPE:
                    raise EOFError
                else:
                    raise
        raise RuntimeError("shouldn't get here; expected KeyboardInterrupt")

    async def _poll(self):
        if (self._got_empty_message or
                _winapi.PeekNamedPipe(self._handle)[0] != 0):
            return True
        ov = None
        try:
            try:
                ov, err = _winapi.ReadFile(self._handle, 0, True)
            except OSError as e:
                ov, err = None, e.winerror
                if err not in _ready_errors:
                    raise
            if err == _winapi.ERROR_IO_PENDING:
                # ov_list.append(ov)
                # waithandle_to_obj[ov.event] = o
                await _wait_for_ov(ov)
            else:
                # If o.fileno() is an overlapped pipe handle and
                # err == 0 then there is a zero length message
                # in the pipe, but it HAS NOT been consumed...
                if ov and sys.getwindowsversion()[:2] >= (6, 2):
                    # ... except on Windows 8 and later, where
                    # the message HAS been consumed.
                    try:
                        _, err = ov.GetOverlappedResult(False)
                    except OSError as e:
                        err = e.winerror
                    if not err:
                        self._got_empty_message = True
        finally:
            if ov is not None:
                ov.cancel()
                try:
                    _, err = ov.GetOverlappedResult(True)
                except OSError as e:
                    err = e.winerror
                    if err not in _ready_errors:
                        raise
                if err != _winapi.ERROR_OPERATION_ABORTED:
                    # o = waithandle_to_obj[ov.event]
                    # ready_objects.add(o)
                    if err == 0:
                        # If o.fileno() is an overlapped pipe handle then
                        # a zero length message HAS been consumed.
                        self._got_empty_message = True
        return True

    def _get_more_data(self, ov, maxsize):
        buf = ov.getbuffer()
        f = io.BytesIO()
        f.write(buf)
        left = _winapi.PeekNamedPipe(self._handle)[1]
        assert left > 0
        if maxsize is not None and len(buf) + left > maxsize:
            self._bad_message_length()
        ov, err = _winapi.ReadFile(self._handle, left, overlapped=True)
        rbytes, err = ov.GetOverlappedResult(True)
        assert err == 0
        assert rbytes == left
        f.write(ov.getbuffer())
        return f


class AsyncSslPipeConnection(AsyncPipeConnection):
    max_size = 256 * 1024  # Buffer size passed to read()
    head_type = '<Q'
    head_length = 8

    class _MustDo(object):
        def __init__(self, co_func):
            self._co_func = co_func

        async def __aenter__(self):
            await self._co_func()
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            await self._co_func()

    def __init__(self, handle, readable=True, writable=True, server_side=False):
        super().__init__(handle, readable=readable, writable=writable, server_side=server_side)
        self.finish_handshake = False
        from .http_proxy_server import CertUtil
        self._context = CertUtil.get_context()
        self._incoming = ssl.MemoryBIO()
        self._outgoing = ssl.MemoryBIO()
        self._handshake_lock = asyncio.Lock()
        self._ssl_obj = self._context.wrap_bio(self._incoming, self._outgoing, self._server_side)
        self.__must_write = lambda: self._MustDo(self.__write_to_pipe())
        # print(self._ssl_obj)
        # print(self._ssl_obj.server_side)

    async def do_handshake(self):
        async with self._handshake_lock:
            if self.finish_handshake:
                return
            while True:
                try:
                    # print("do_handshake")
                    async with self.__must_write():
                        self._ssl_obj.do_handshake()
                    # print("finish_handshake")
                    break
                except ssl.SSLWantReadError as e:
                    # print(e)
                    await self.__read_from_pipe()
            self.finish_handshake = True

    async def __write_to_pipe(self):
        data = self._outgoing.read()
        if data:
            await super()._send_bytes(data)

    async def __read_from_pipe(self):
        data = await super()._recv_bytes()
        buf = data.getvalue()
        self._incoming.write(buf)

    async def _send_bytes(self, buf):
        if not self.finish_handshake:
            await self.do_handshake()
        offset = 0
        head = struct.pack(self.head_type, len(buf))
        buf = head + buf
        view = memoryview(buf)
        while offset < len(view):
            try:
                async with self.__must_write():
                    offset += self._ssl_obj.write(view[offset:])
            except ssl.SSLWantReadError as e:
                # print(e)
                await self.__read_from_pipe()

    async def _recv_bytes(self, maxsize=None):
        if not self.finish_handshake:
            await self.do_handshake()
        length = self.head_length
        bio = io.BytesIO()
        while length > 0:
            data = await self.__recv_bytes(length)
            if not data:
                break
            bio.write(data)
            length -= len(data)
        length = struct.unpack_from(self.head_type, bio.getbuffer())[0]
        if maxsize < length:
            return None
        bio = io.BytesIO()
        while length > 0:
            data = await self.__recv_bytes(length)
            if not data:
                break
            bio.write(data)
            length -= len(data)
        return bio

    async def __recv_bytes(self, maxsize=None):
        maxsize = min(self.max_size, maxsize)
        while True:
            try:
                async with self.__must_write():
                    return self._ssl_obj.read(maxsize)
            except ssl.SSLWantReadError as e:
                # print(e)
                await self.__read_from_pipe()


class AsyncPipeListener(object):
    '''
    Representation of a named pipe
    '''

    def __init__(self, address, backlog=None, wrap_ssl=False):
        self._address = address
        self._wrap_ssl = wrap_ssl
        self._handle_queue = [self._new_handle(first=True)]

        self._last_accepted = None
        self.close = multiprocessing.util.Finalize(
            self, AsyncPipeListener._finalize_pipe_listener,
            args=(self._handle_queue, self._address), exitpriority=0
        )

    def _new_handle(self, first=False):
        flags = _winapi.PIPE_ACCESS_DUPLEX | _winapi.FILE_FLAG_OVERLAPPED
        if first:
            flags |= _winapi.FILE_FLAG_FIRST_PIPE_INSTANCE
        return _winapi.CreateNamedPipe(
            self._address, flags,
            _winapi.PIPE_TYPE_MESSAGE | _winapi.PIPE_READMODE_MESSAGE |
            _winapi.PIPE_WAIT,
            _winapi.PIPE_UNLIMITED_INSTANCES, BUFSIZE, BUFSIZE,
            _winapi.NMPWAIT_WAIT_FOREVER, _winapi.NULL
        )

    async def accept(self):
        self._handle_queue.append(self._new_handle())
        handle = self._handle_queue.pop(0)
        try:
            ov = _winapi.ConnectNamedPipe(handle, overlapped=True)
        except OSError as e:
            if e.winerror != _winapi.ERROR_NO_DATA:
                raise
            # ERROR_NO_DATA can occur if a client has already connected,
            # written data and then disconnected -- see Issue 14725.
        else:
            try:
                # res = _winapi.WaitForMultipleObjects(
                #     [ov.event], False, INFINITE)
                await _wait_for_ov(ov)
            except:
                ov.cancel()
                _winapi.CloseHandle(handle)
                raise
            finally:
                _, err = ov.GetOverlappedResult(True)
                assert err == 0
        if self._wrap_ssl:
            return AsyncSslPipeConnection(handle, server_side=True)
        else:
            return AsyncPipeConnection(handle, server_side=True)

    @staticmethod
    def _finalize_pipe_listener(queue, address):
        for handle in queue:
            _winapi.CloseHandle(handle)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        self.close()


# Initial delay in seconds for connect_pipe() before retrying to connect
CONNECT_PIPE_INIT_DELAY = 0.001

# Maximum delay in seconds for connect_pipe() before retrying to connect
CONNECT_PIPE_MAX_DELAY = 0.100


class AsyncPipeClient(object):
    def __init__(self, address, wrap_ssl=False):
        self._address = address
        self._wrap_ssl = wrap_ssl
        self._conn = None  # type:AsyncPipeConnection

    async def connect(self):
        '''
        Return a connection object connected to the pipe given by `address`
        '''
        if self._conn is None:
            delay = CONNECT_PIPE_INIT_DELAY
            while True:
                # Unfortunately there is no way to do an overlapped connect to
                # a pipe.  Call CreateFile() in a loop until it doesn't fail with
                # ERROR_PIPE_BUSY.
                try:
                    h = _winapi.CreateFile(
                        self._address, _winapi.GENERIC_READ | _winapi.GENERIC_WRITE,
                        0, _winapi.NULL, _winapi.OPEN_EXISTING,
                        _winapi.FILE_FLAG_OVERLAPPED, _winapi.NULL
                    )
                    break
                except OSError as e:
                    if e.winerror not in (_winapi.ERROR_SEM_TIMEOUT,
                                          _winapi.ERROR_PIPE_BUSY):
                        raise

                # ConnectPipe() failed with ERROR_PIPE_BUSY: retry later
                delay = min(delay * 2, CONNECT_PIPE_MAX_DELAY)
                await asyncio.sleep(delay)
            _winapi.SetNamedPipeHandleState(
                h, _winapi.PIPE_READMODE_MESSAGE, None, None
            )
            if self._wrap_ssl:
                self._conn = AsyncSslPipeConnection(h)
            else:
                self._conn = AsyncPipeConnection(h)
        return self._conn

    async def close(self):
        if self._conn is not None:
            self._conn.close()

    def __await__(self):
        return self.connect().__await__()

    async def __aenter__(self):
        return await self.connect()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


__all__ = ["AsyncPipeConnection", "AsyncPipeListener", "AsyncPipeClient"]
