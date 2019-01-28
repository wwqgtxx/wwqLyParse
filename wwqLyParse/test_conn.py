#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>

import json, sys, subprocess, time, logging, traceback, ctypes, sysconfig
import multiprocessing
import multiprocessing.connection

import main


def test():
    main.init()
    address = r'\\.\pipe\%s@%s' % ('wwqLyParse', main.version["version"])
    with multiprocessing.connection.Client(address, authkey=main.get_uuid()) as conn:
        time.sleep(main.CONN_LRU_TIMEOUT)
        logging.debug(main.CONN_LRU_TIMEOUT)
        time.sleep(1)
        with multiprocessing.connection.Client(address, authkey=main.get_uuid()) as conn2:
            pass
        time.sleep(1)
        try:
            conn.recv_bytes()
        except EOFError:
            logging.debug("EOF")


if __name__ == '__main__':
    main.asyncio.start_main_async_loop_in_main_thread(test)
