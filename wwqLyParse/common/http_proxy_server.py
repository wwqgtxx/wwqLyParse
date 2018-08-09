#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
# some code merge from GoAgent (￣▽￣)~*

from .get_url import *
from .for_path import get_real_path
from .selectors import DefaultSelector
from .workerpool import WorkerPool
from .utils import format_exception
import sys

import errno
import struct
import re
import io
import logging
import socket
import ssl
import socketserver
import threading
import http.server
import http.client
import urllib.parse

NetWorkIOError = (socket.error, ssl.SSLError, OSError)
socketserver._ServerSelector = DefaultSelector


class CertUtil(object):
    """CertUtil module, based on mitmproxy"""
    ca_keyfile = 'CA.crt'

    @staticmethod
    def get_cert(commonname, sans=()):
        return get_real_path(CertUtil.ca_keyfile)


def is_clienthello(data):
    if len(data) < 20:
        return False
    if data.startswith(b'\x16\x03'):
        # TLSv12/TLSv11/TLSv1/SSLv3
        length, = struct.unpack('>h', data[3:5])
        return len(data) == 5 + length
    elif data[0] == b'\x80' and data[2:4] == b'\x01\x03':
        # SSLv23
        return len(data) == 2 + ord(data[1])
    else:
        return False


def extract_sni_name(packet):
    if packet.startswith(b'\x16\x03'):
        stream = io.BytesIO(packet)
        stream.read(0x2b)
        session_id_length = ord(stream.read(1))
        stream.read(session_id_length)
        cipher_suites_length, = struct.unpack('>h', stream.read(2))
        stream.read(cipher_suites_length + 2)
        extensions_length, = struct.unpack('>h', stream.read(2))
        # extensions = {}
        while True:
            data = stream.read(2)
            if not data:
                break
            etype, = struct.unpack('>h', data)
            elen, = struct.unpack('>h', stream.read(2))
            edata = stream.read(elen)
            if etype == 0:
                server_name = edata[5:]
                return server_name


class ProxyHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    buf_size = 256 * 1024

    def __init__(self, request, client_address, server):
        self.scheme = 'http'
        super().__init__(request, client_address, server)

    def log_message(self, format, *args):
        pass
        # logging.debug(format % args)

    def handle_one_request(self):
        if self.scheme == 'http':
            leadbyte = self.connection.recv(1, socket.MSG_PEEK)
            if leadbyte in (b'\x80', b'\x16'):
                server_name = ''
                if leadbyte == b'\x16':
                    for _ in range(2):
                        leaddata = self.connection.recv(1024, socket.MSG_PEEK)
                        if is_clienthello(leaddata):
                            try:
                                server_name = extract_sni_name(leaddata)
                            finally:
                                break
                try:
                    certfile = CertUtil.get_cert(server_name or 'www.google.com')
                    ssl_sock = ssl.wrap_socket(self.connection, keyfile=certfile,
                                               certfile=certfile, server_side=True)
                except Exception as e:
                    if e.args[0] not in (errno.ECONNABORTED, errno.ECONNRESET):
                        logging.exception('ssl.wrap_socket(self.connection=%r) failed: %s', self.connection, e)
                    return
                self.connection = ssl_sock
                self.rfile = self.connection.makefile('rb', self.buf_size)
                self.wfile = self.connection.makefile('wb', 0)
                self.scheme = 'https'
        return http.server.BaseHTTPRequestHandler.handle_one_request(self)

    def parse_header(self):
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

    def do_mock(self, status, headers, content):
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
        self.send_response(status)
        for key, value in headers.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(content)

    def do_strip(self, do_ssl_handshake=True):
        """strip connect"""
        certfile = CertUtil.get_cert(self.host)
        logging.info('%s "STRIP %s %s:%d %s" - -', self.address_string(), self.command, self.host, self.port,
                     self.protocol_version)

        self.send_response(200)
        self.end_headers()
        if do_ssl_handshake:
            try:
                ssl_sock = ssl.wrap_socket(self.connection, keyfile=certfile, certfile=certfile, server_side=True)
            except Exception as e:
                if e.args[0] not in (errno.ECONNABORTED, errno.ECONNRESET):
                    logging.exception('ssl.wrap_socket(self.connection=%r) failed: %s', self.connection, e)
                return
            self.connection = ssl_sock
            self.rfile = self.connection.makefile('rb', self.buf_size)
            self.wfile = self.connection.makefile('wb', 0)
            self.scheme = 'https'
        try:
            self.raw_requestline = self.rfile.readline(65537)
            if len(self.raw_requestline) > 65536:
                self.requestline = ''
                self.request_version = ''
                self.command = ''
                self.send_error(414)
                return
            if not self.raw_requestline:
                self.close_connection = 1
                return
            if not self.parse_request():
                return
        except NetWorkIOError as e:
            if e.args[0] not in (errno.ECONNABORTED, errno.ECONNRESET, errno.EPIPE):
                raise
        try:
            self.do_method()
        except NetWorkIOError as e:
            if e.args[0] not in (errno.ECONNABORTED, errno.ETIMEDOUT, errno.EPIPE):
                raise

    def do_url_fetch(self):
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
            resp = get_url(url,
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
            return self.do_mock(status, headers, content)

        # self.close_connection = not headers.get('Content-Length')
        self.send_response_only(status)
        pop_headers = ['Transfer-Encoding', 'Connection']
        if isinstance(content, GetUrlStreamReader):
            if headers.get('Content-Encoding') in content.decoded_encoding:
                pop_headers.append('Content-Length')
                pop_headers.append('Content-Encoding')
        else:
            pop_headers.append('Content-Length')
            pop_headers.append('Content-Encoding')
            self.send_header('Content-Length', len(content))
        self.send_header('Connection', 'close')
        pop_headers = [k.lower() for k in pop_headers]
        for key, value in headers.items():
            if key.lower() in pop_headers:
                continue
            self.send_header(key, value)
        self.end_headers()

        try:
            if isinstance(content, GetUrlStreamReader):
                with content:
                    while True:
                        data = content.read()
                        if not data:
                            break
                        self.wfile.write(data)
            elif content:
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

    def do_method(self):
        self.parse_header()
        self.body = self.rfile.read(int(self.headers['Content-Length'])) if 'Content-Length' in self.headers else ''
        if self.command == 'CONNECT':
            do_ssl_handshake = 440 <= self.port <= 450 or 1024 <= self.port <= 65535
            return self.do_strip(do_ssl_handshake)
        elif self.command in ('GET', 'POST', 'HEAD', 'PUT', 'DELETE', 'PATCH'):
            return self.do_url_fetch()


class HttpProxyServer(socketserver.TCPServer):
    """Local Proxy Server"""
    allow_reuse_address = False
    daemon_threads = True
    common_worker_pool = WorkerPool(thread_name_prefix="HPSPool")

    def __init__(self, host="localhost", port=0):
        super().__init__((host, port), ProxyHandler)
        self.is_start = False
        self._threads = []
        self._serve_thread = None

    def process_request_thread(self, request, client_address):
        try:
            self.finish_request(request, client_address)
        except Exception:
            self.handle_error(request, client_address)
        finally:
            self.shutdown_request(request)

    def process_request(self, request, client_address):
        self._threads.append(self.common_worker_pool.spawn(self.process_request_thread, request, client_address))

    def server_close(self):
        super().server_close()
        threads = self._threads
        self._threads = []
        self.common_worker_pool.wait(threads)

    def close_request(self, request):
        try:
            request.close()
        except Exception:
            pass

    def finish_request(self, request, client_address):
        try:
            self.RequestHandlerClass(request, client_address, self)
        except NetWorkIOError as e:
            if e.args[0] not in (errno.ECONNABORTED, errno.ECONNRESET, errno.EPIPE):
                raise

    def handle_error(self, *args):
        """make ThreadingTCPServer happy"""
        exc_info = sys.exc_info()
        error = exc_info and len(exc_info) and exc_info[1]
        if isinstance(error, NetWorkIOError) and len(error.args) > 1 and 'bad write retry' in error.args[1]:
            exc_info = error = None
        else:
            del exc_info, error
            socketserver.ThreadingTCPServer.handle_error(self, *args)

    def serve_forever(self, poll_interval=0.5):
        logging.info("listen address:'http://%s:%s'" % self.server_address)
        super().serve_forever(poll_interval=poll_interval)

    def _shutdown(self):
        logging.info("begin shutdown listen address:'http://%s:%s'" % self.server_address)
        self.socket.close()
        super().shutdown()
        logging.info("finish shutdown listen address:'http://%s:%s'" % self.server_address)

    @property
    def port(self):
        return self.server_address[1]

    def start(self):
        self.is_start = True
        self._serve_thread = self.common_worker_pool.spawn(self.serve_forever)

    def join(self, timeout=None):
        if self.is_start:
            self.common_worker_pool.wait([self._serve_thread], timeout=timeout)

    def shutdown(self):
        if self.is_start:
            self.is_start = False
            self.common_worker_pool.spawn(self._shutdown)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()


__all__ = ["HttpProxyServer"]
