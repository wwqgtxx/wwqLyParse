#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>

# encoding list to fix encoding BUG on windows
fix_encoding = [
    'UTF-8',
    'cp936',
    'cp950',
]


# try to decode, to fix encoding BUG on windows
def try_decode(raw, no_error=False):
    fix_list = fix_encoding
    rest = fix_list
    while len(rest) > 0:
        one = rest[0]
        rest = rest[1:]
        try:
            out = raw.decode(one)
            return out
        except Exception as e:
            if len(rest) < 1:
                if no_error:
                    out = raw.decode(one, 'ignore')
                    return out
                else:
                    raise e


def debug(text):
    print((str(text)).encode('gbk', 'ignore').decode('gbk'))
