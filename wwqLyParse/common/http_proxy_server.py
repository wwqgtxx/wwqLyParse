#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
# some code merge from GoAgent (￣▽￣)~*

from .get_url import *
from .for_path import get_real_path
from .utils import format_exception
import sys

import errno
import re
import logging
import socket
import http.server
import http.client
import urllib.parse
import time
import email
import html
import ssl
import itertools
from . import asyncio
from .async_pool import *

NetWorkIOError = (socket.error, ssl.SSLError, OSError)


class CertUtil(object):
    """CertUtil module, based on mitmproxy"""
    ca_keyfile = 'CA.crt'

    @staticmethod
    def get_cert(commonname, sans=()):
        return get_real_path(CertUtil.ca_keyfile)

    @staticmethod
    def get_context(host=''):
        certfile = CertUtil.get_cert(host)
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        # context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        context.load_cert_chain(certfile, certfile)
        return context


get_hps_loop = asyncio.get_main_async_loop


class AsyncHttpProxyServer(object):
    address_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM
    _counter = itertools.count().__next__

    def __init__(self, host="localhost", port=0):
        self.socket = socket.socket(self.address_family,
                                    self.socket_type)
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        self.socket.bind((host, port))
        self.server_address = self.socket.getsockname()
        self.server = None  # type:asyncio.AbstractServer
        self.loop = get_hps_loop()

    @property
    def port(self):
        return self.server_address[1]

    async def start_async(self):
        return await asyncio.async_run_in_loop(self._start(), loop=self.loop)

    def start(self):
        return asyncio.run_in_other_loop(self._start(), loop=self.loop)

    async def shutdown_async(self):
        return await asyncio.async_run_in_loop(self._shutdown(), loop=self.loop)

    def shutdown(self):
        return asyncio.run_in_other_loop(self._shutdown(), loop=self.loop)

    async def join_async(self):
        return await asyncio.async_run_in_loop(self._join(), loop=self.loop)

    def join(self):
        return asyncio.run_in_other_loop(self._join(), loop=self.loop)

    async def _start(self):
        loop = asyncio.get_running_loop()
        pool = AsyncPool(thread_name_prefix="HPSPool-%d" % self._counter(), loop=loop)

        def factory():
            return asyncio.AsyncTcpStreamProtocol(AsyncProxyHandler, pool, loop)

        self.server = await loop.create_server(factory, sock=self.socket, )
        logging.info("listen address:'http://%s:%s'" % self.server_address)

    async def _shutdown(self):
        if self.server:
            logging.info("begin shutdown listen address:'http://%s:%s'" % self.server_address)
            self.server.close()
            await self.server.wait_closed()
            logging.info("finish shutdown listen address:'http://%s:%s'" % self.server_address)

    async def _join(self):
        if self.server:
            await self.server.wait_closed()

    async def __aenter__(self):
        await self.start_async()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.shutdown_async()


class AsyncBaseHttpRequestHandler(asyncio.AsyncTcpStreamRequestHandler):
    protocol_version = "HTTP/0.9"
    default_request_version = "HTTP/0.9"
    error_message_format = http.server.DEFAULT_ERROR_MESSAGE
    error_content_type = http.server.DEFAULT_ERROR_CONTENT_TYPE

    async def parse_request(self):
        """Parse a request (internal).

        The request should be stored in self.raw_requestline; the results
        are in self.command, self.path, self.request_version and
        self.headers.

        Return True for success, False for failure; on failure, any relevant
        error response has already been sent back.

        """
        self.command = None  # set in case of error on the first line
        self.request_version = version = self.default_request_version
        self.close_connection = True
        requestline = str(self.raw_requestline, 'iso-8859-1')
        requestline = requestline.rstrip('\r\n')
        self.requestline = requestline
        words = requestline.split()
        if len(words) == 0:
            return False

        if len(words) >= 3:  # Enough to determine protocol version
            version = words[-1]
            try:
                if not version.startswith('HTTP/'):
                    raise ValueError
                base_version_number = version.split('/', 1)[1]
                version_number = base_version_number.split(".")
                # RFC 2145 section 3.1 says there can be only one "." and
                #   - major and minor numbers MUST be treated as
                #      separate integers;
                #   - HTTP/2.4 is a lower version than HTTP/2.13, which in
                #      turn is lower than HTTP/12.3;
                #   - Leading zeros MUST be ignored by recipients.
                if len(version_number) != 2:
                    raise ValueError
                version_number = int(version_number[0]), int(version_number[1])
            except (ValueError, IndexError):
                await self.send_error(
                    http.HTTPStatus.BAD_REQUEST,
                    "Bad request version (%r)" % version)
                return False
            if version_number >= (1, 1) and self.protocol_version >= "HTTP/1.1":
                self.close_connection = False
            if version_number >= (2, 0):
                await self.send_error(
                    http.HTTPStatus.HTTP_VERSION_NOT_SUPPORTED,
                    "Invalid HTTP version (%s)" % base_version_number)
                return False
            self.request_version = version

        if not 2 <= len(words) <= 3:
            await self.send_error(
                http.HTTPStatus.BAD_REQUEST,
                "Bad request syntax (%r)" % requestline)
            return False
        command, path = words[:2]
        if len(words) == 2:
            self.close_connection = True
            if command != 'GET':
                await self.send_error(
                    http.HTTPStatus.BAD_REQUEST,
                    "Bad HTTP/0.9 request type (%r)" % command)
                return False
        self.command, self.path = command, path

        # Examine the headers and look for a Connection directive.
        headers = []
        while True:
            line = await self.rfile.readline()
            if len(line) > 65536:
                await self.send_error(http.HTTPStatus.REQUEST_HEADER_FIELDS_TOO_LARGE, "Line too long", "")
                return False
            headers.append(line)
            if len(headers) > 100:
                await self.send_error(http.HTTPStatus.REQUEST_HEADER_FIELDS_TOO_LARGE, "Too many headers", "")
                return False
            if line in (b'\r\n', b'\n', b''):
                break
        hstring = b''.join(headers).decode('iso-8859-1')
        self.headers = email.parser.Parser(_class=http.client.HTTPMessage).parsestr(hstring)

        conntype = self.headers.get('Connection', "")
        if conntype.lower() == 'close':
            self.close_connection = True
        elif (conntype.lower() == 'keep-alive' and
              self.protocol_version >= "HTTP/1.1"):
            self.close_connection = False
        # Examine the headers and look for an Expect directive
        expect = self.headers.get('Expect', "")
        if (expect.lower() == "100-continue" and
                self.protocol_version >= "HTTP/1.1" and
                self.request_version >= "HTTP/1.1"):
            if not self.handle_expect_100():
                return False
        return True

    async def handle_expect_100(self):
        """Decide what to do with an "Expect: 100-continue" header.

        If the client is expecting a 100 Continue response, we must
        respond with either a 100 Continue or a final response before
        waiting for the request body. The default is to always respond
        with a 100 Continue. You can behave differently (for example,
        reject unauthorized requests) by overriding this method.

        This method should either return True (possibly after sending
        a 100 Continue response) or send an error response and return
        False.

        """
        await self.send_response_only(http.HTTPStatus.CONTINUE)
        await self.end_headers()
        return True

    async def handle_one_request(self):
        """Handle a single HTTP request.

        You normally don't need to override this method; see the class
        __doc__ string for information on how to handle specific HTTP
        commands such as GET and POST.

        """
        try:
            self.raw_requestline = await self.rfile.readline()
            if len(self.raw_requestline) > 65536:
                self.requestline = ''
                self.request_version = ''
                self.command = ''
                await self.send_error(http.HTTPStatus.REQUEST_URI_TOO_LONG)
                return
            if not self.raw_requestline:
                self.close_connection = True
                return
            if not await self.parse_request():
                # An error code has been sent, just exit
                return
            mname = 'do_' + self.command
            if not hasattr(self, mname):
                await self.send_error(
                    http.HTTPStatus.NOT_IMPLEMENTED,
                    "Unsupported method (%r)" % self.command)
                return
            method = getattr(self, mname)
            await method()
            await self.wfile.drain()
        except socket.timeout as e:
            # a read or a write timed out.  Discard this connection
            self.log_error("Request timed out: %r", e)
            self.close_connection = True
            return

    async def handle(self):
        """Handle multiple requests if necessary."""
        self.close_connection = True

        await self.handle_one_request()
        while not self.close_connection:
            await self.handle_one_request()

    async def send_error(self, code, message=None, explain=None):
        """Send and log an error reply.

        Arguments are
        * code:    an HTTP error code
                   3 digits
        * message: a simple optional 1 line reason phrase.
                   *( HTAB / SP / VCHAR / %x80-FF )
                   defaults to short entry matching the response code
        * explain: a detailed message defaults to the long entry
                   matching the response code.

        This sends an error response (so it must be called before any
        output has been generated), logs the error, and finally sends
        a piece of HTML explaining the error to the user.

        """

        try:
            shortmsg, longmsg = self.responses[code]
        except KeyError:
            shortmsg, longmsg = '???', '???'
        if message is None:
            message = shortmsg
        if explain is None:
            explain = longmsg
        self.log_error("code %d, message %s", code, message)
        await self.send_response(code, message)
        await self.send_header('Connection', 'close')

        # Message body is omitted for cases described in:
        #  - RFC7230: 3.3. 1xx, 204(No Content), 304(Not Modified)
        #  - RFC7231: 6.3.6. 205(Reset Content)
        body = None
        if (code >= 200 and
                code not in (http.HTTPStatus.NO_CONTENT,
                             http.HTTPStatus.RESET_CONTENT,
                             http.HTTPStatus.NOT_MODIFIED)):
            # HTML encode to prevent Cross Site Scripting attacks
            # (see bug #1100201)
            content = (self.error_message_format % {
                'code': code,
                'message': html.escape(message, quote=False),
                'explain': html.escape(explain, quote=False)
            })
            body = content.encode('UTF-8', 'replace')
            await self.send_header("Content-Type", self.error_content_type)
            await self.send_header('Content-Length', str(len(body)))
        await self.end_headers()

        if self.command != 'HEAD' and body:
            self.wfile.write(body)

    async def send_response(self, code, message=None):
        """Add the response header to the headers buffer and log the
        response code.

        Also send two standard headers with the server software
        version and the current date.

        """
        self.log_request(code)
        await self.send_response_only(code, message)
        await self.send_header('Server', self.version_string())
        await self.send_header('Date', self.date_time_string())

    async def send_response_only(self, code, message=None):
        """Send the response header only."""
        if self.request_version != 'HTTP/0.9':
            if message is None:
                if code in self.responses:
                    message = self.responses[code][0]
                else:
                    message = ''
            if not hasattr(self, '_headers_buffer'):
                self._headers_buffer = []
            self._headers_buffer.append(("%s %d %s\r\n" %
                                         (self.protocol_version, code, message)).encode(
                'latin-1', 'strict'))

    async def send_header(self, keyword, value):
        """Send a MIME header to the headers buffer."""
        if self.request_version != 'HTTP/0.9':
            if not hasattr(self, '_headers_buffer'):
                self._headers_buffer = []
            self._headers_buffer.append(
                ("%s: %s\r\n" % (keyword, value)).encode('latin-1', 'strict'))

        if keyword.lower() == 'connection':
            if value.lower() == 'close':
                self.close_connection = True
            elif value.lower() == 'keep-alive':
                self.close_connection = False

    async def end_headers(self):
        """Send the blank line ending the MIME headers."""
        if self.request_version != 'HTTP/0.9':
            self._headers_buffer.append(b"\r\n")
            await self.flush_headers()

    async def flush_headers(self):
        if hasattr(self, '_headers_buffer'):
            self.wfile.write(b"".join(self._headers_buffer))
            self._headers_buffer = []

    def log_request(self, code='-', size='-'):
        """Log an accepted request.

        This is called by send_response().

        """
        if isinstance(code, http.HTTPStatus):
            code = code.value
        self.log_message('"%s" %s %s',
                         self.requestline, str(code), str(size))

    def log_error(self, format, *args):
        """Log an error.

        This is called when a request cannot be fulfilled.  By
        default it passes the message on to log_message().

        Arguments are the same as for log_message().

        XXX This should go to the separate error log.

        """

        self.log_message(format, *args)

    def log_message(self, format, *args):
        """Log an arbitrary message.

        This is used by all other logging functions.  Override
        it if you have specific logging wishes.

        The first argument, FORMAT, is a format string for the
        message to be logged.  If the format string contains
        any % escapes requiring parameters, they should be
        specified as subsequent arguments (it's just like
        printf!).

        The client ip and current date/time are prefixed to
        every message.

        """

        sys.stderr.write("%s - - [%s] %s\n" %
                         (self.address_string(),
                          self.log_date_time_string(),
                          format % args))

    def version_string(self):
        """Return the server software version string."""
        return 'hps/1.0'

    def date_time_string(self, timestamp=None):
        """Return the current date and time formatted for a message header."""
        if timestamp is None:
            timestamp = time.time()
        return email.utils.formatdate(timestamp, usegmt=True)

    def log_date_time_string(self):
        """Return the current time formatted for logging."""
        now = time.time()
        year, month, day, hh, mm, ss, x, y, z = time.localtime(now)
        s = "%02d/%3s/%04d %02d:%02d:%02d" % (
            day, self.monthname[month], year, hh, mm, ss)
        return s

    weekdayname = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    monthname = [None,
                 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    def address_string(self):
        """Return the client address."""

        return self.client_address[0]

    # hack to maintain backwards compatibility
    responses = {
        v: (v.phrase, v.description)
        for v in http.HTTPStatus.__members__.values()
    }


class AsyncProxyHandler(AsyncBaseHttpRequestHandler):
    protocol_version = 'HTTP/1.1'
    buf_size = 256 * 1024

    def __init__(self, *k, **kk):
        super().__init__(*k, **kk)
        self.scheme = "http"

    def log_message(self, format, *args):
        pass
        # logging.debug(format % args)

    async def parse_header(self):
        if self.command == 'CONNECT':
            netloc = self.path
        elif self.path[0] == '/':
            netloc = self.headers.get('Host', 'localhost')
            self.path = '%s://%s%s' % (self.scheme, netloc, self.path)
        else:
            netloc = urllib.parse.urlsplit(self.path).netloc
        m = re.match(r'^(.+):(\d+)$', netloc)
        if m:
            self.host = m.group(1).strip('[]')
            self.port = int(m.group(2))
        else:
            self.host = netloc
            self.port = 443 if self.scheme == 'https' else 80

    async def do_mock(self, status, headers, content):
        """mock response"""
        logging.info('%s "MOCK %s %s %s" %d %d', self.address_string(), self.command, self.path, self.protocol_version,
                     status, len(content))
        headers = dict((k.title(), v) for k, v in headers.items())
        if 'Transfer-Encoding' in headers:
            del headers['Transfer-Encoding']
        if 'Content-Length' not in headers:
            headers['Content-Length'] = len(content)
        if 'Connection' not in headers:
            headers['Connection'] = 'close'
        await self.send_response(status)
        for key, value in headers.items():
            await self.send_header(key, value)
            await self.end_headers()
        self.wfile.write(content)

    async def do_strip(self, do_ssl_handshake=True):
        """strip connect"""
        logging.info('%s "STRIP %s %s:%d %s" - -', self.address_string(), self.command, self.host, self.port,
                     self.protocol_version)

        await self.send_response(200)
        await self.end_headers()
        if do_ssl_handshake:
            try:
                context = CertUtil.get_context(self.host)
                transport = await asyncio.start_tls(self.protocol.loop, self.protocol.transport, self.protocol,
                                                    sslcontext=context, server_side=True)
                self.protocol.transport = transport
                self.protocol.rebuild()
                await self.setup()
                # logging.debug(self.protocol.transport)
            except ConnectionResetError:
                raise
            except Exception as e:
                logging.exception('start_tls(self.connection=%r) failed: %s', self.connection, e)
                return
            self.scheme = 'https'
        try:
            self.raw_requestline = await self.rfile.readline()
            if len(self.raw_requestline) > 65536:
                self.requestline = ''
                self.request_version = ''
                self.command = ''
                await self.send_error(414)
                return
            if not self.raw_requestline:
                self.close_connection = 1
                return
            if not await self.parse_request():
                return
        except NetWorkIOError as e:
            if e.args[0] not in (errno.ECONNABORTED, errno.ECONNRESET, errno.EPIPE):
                raise
        try:
            await self.do_method()
        except NetWorkIOError as e:
            if e.args[0] not in (errno.ECONNABORTED, errno.ETIMEDOUT, errno.EPIPE):
                raise

    async def do_url_fetch(self):
        method = self.command
        if self.path[0] == '/':
            url = '%s://%s%s' % (self.scheme, self.headers['Host'], self.path)
        elif self.path.lower().startswith(('http://', 'https://', 'ftp://')):
            url = self.path
        else:
            raise ValueError('URL_FETCH %r is not a valid url' % self.path)
        logging.debug('%s "URL_FETCH %s %s" - -', self.address_string(), self.command, url)
        headers = dict((k.title(), v) for k, v in self.headers.items())
        body = self.body

        try:
            resp = await get_url_service.get_url_async(url,
                                                       method=method,
                                                       headers=headers,
                                                       data=body,
                                                       cookies=EMPTY_COOKIES,
                                                       stream=True,
                                                       allow_cache=False)  # type:GetUrlResponse
            status = resp.status_code
            content = resp.content
            headers = resp.headers
            # logging.debug(data)
            # logging.debug(headers)
        except Exception as e:
            status = 502
            headers = {'Content-Type': 'text/plain'}
            content = format_exception(e).encode()
            return await self.do_mock(status, headers, content)

        # self.close_connection = not headers.get('Content-Length')
        await self.send_response_only(status)
        pop_headers = ['Transfer-Encoding', 'Connection']

        if isinstance(content, GetUrlStreamReader):
            if headers.get('Content-Encoding') in content.decoded_encoding:
                pop_headers.append('Content-Length')
                pop_headers.append('Content-Encoding')
        else:
            pop_headers.append('Content-Length')
            pop_headers.append('Content-Encoding')
            await self.send_header('Content-Length', len(content))
        await self.send_header('Connection', 'close')
        pop_headers = [k.lower() for k in pop_headers]
        for key, value in headers.items():
            if key.lower() in pop_headers:
                continue
            await self.send_header(key, value)
        await self.end_headers()

        try:
            if isinstance(content, GetUrlStreamReader):
                async with content:
                    while True:
                        data = await content.read_async()
                        if not data:
                            break
                        self.wfile.write(data)
            elif isinstance(content, bytes):
                self.wfile.write(content)
                del content
        except GetUrlStreamReadError:
            return
        except NetWorkIOError as e:
            if e.args[0] in (errno.ECONNABORTED, errno.EPIPE) or 'bad write retry' in repr(e):
                return

    def __getattr__(self, item):
        if str(item).startswith("do_"):
            return self.do_method
        raise AttributeError

    async def do_method(self):
        await self.parse_header()
        self.body = await self.rfile.read(
            int(self.headers['Content-Length'])) if 'Content-Length' in self.headers else ''
        if self.command == 'CONNECT':
            do_ssl_handshake = 440 <= self.port <= 450 or 1024 <= self.port <= 65535
            return await self.do_strip(do_ssl_handshake)
        elif self.command in ('GET', 'POST', 'HEAD', 'PUT', 'DELETE', 'PATCH'):
            return await self.do_url_fetch()


HttpProxyServer = AsyncHttpProxyServer

__all__ = ["HttpProxyServer", "AsyncHttpProxyServer"]
