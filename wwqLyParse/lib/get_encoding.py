#!/usr/bin/env python
# -*- coding: utf-8 -*-
# get_encoding.py for lyp_bridge
# version 0.0.1.0 test201509210037

import sys, json

def main():
    out = {}
    out['stdout'] = sys.stdout.encoding
    out['stderr'] = sys.stderr.encoding
    out['stdin'] = sys.stdin.encoding
    
    text = json.dumps(out)
    print(text)

if __name__ == '__main__':
    main()

# end get_encoding.py


