#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>

# modify from ykdl's jsengine.py

'''
    Usage:
        ctx = JSEngine()
        ctx.eval('1 + 1')  # => 2

        ctx2 = JSEngine("""
            function add(x, y) {
            return x + y;
        }
        """)
        ctx2.call("add", 1, 2)  # => 3
'''

import io
import json
import os
import re
import sys
import tempfile
from .for_path import get_real_path
from .subprocess import async_run_subprocess


# Exceptions
class ProgramError(Exception):
    pass


interpreter = [get_real_path('./lib/node_lib/node.exe')]

# Inject to the script to let it return jsonlized value to python
injected_script = r'''
function print(data) {
    console.log(data);
}
(function(program, execJS) { execJS(program) })(
function() {
    return eval(#{encoded_source});
},
function(program) {
    var output;
    try {
        result = program();
        print("");
        if (typeof result == 'undefined' && result !== null) {
            print('["ok"]');
        }
        else {
            try {
                print(JSON.stringify(['ok', result]));
            }
            catch (err) {
                print('["err", "Script returns a value with an unknown type"]');
            }
        }
    }
    catch (err) {
        print(JSON.stringify(['err', '' + err]));
    }
});
'''


class JSEngine:
    def __init__(self, source=''):
        self._source = source
        self._last_code = ''

    async def call(self, identifier, *args):
        args = json.dumps(args)
        code = '{identifier}.apply(this,{args})'.format(identifier=identifier, args=args)
        return await self.eval(code)

    async def eval(self, code):
        # TODO: may need a thread lock, if running multithreading
        if not code.strip():
            return None
        if self._last_code:
            self._source += '\n' + self._last_code
        self._last_code = code
        data = json.dumps(code, ensure_ascii=True)
        code = 'return eval({data});'.format(data=data)
        return await self._exec(code)

    async def _exec(self, code):
        if self._source:
            code = self._source + '\n' + code
        code = self._inject_script(code)
        output = await self._run_interpreter_with_tempfile(code)
        output = output.replace('\r\n', '\n').replace('\r', '\n')
        last_line = output.split('\n')[-2]
        ret = json.loads(last_line)
        if len(ret) == 1:
            return None
        status, value = ret
        if status == 'ok':
            return value
        else:
            raise ProgramError(value)

    async def _run_interpreter_with_tempfile(self, code):
        (fd, filename) = tempfile.mkstemp(prefix='execjs', suffix='.js')
        os.close(fd)
        try:
            with io.open(filename, 'w', encoding='utf8') as fp:
                fp.write(code)

            cmd = interpreter + [filename]
            stdout, stderr = await async_run_subprocess(cmd, need_stderr=False)
            return stdout
        finally:
            os.remove(filename)

    def _inject_script(self, source):
        encoded_source = \
            '(function(){ ' + \
            self._encode_unicode_codepoints(source) + \
            ' })()'
        return injected_script.replace('#{encoded_source}', json.dumps(encoded_source))

    def _encode_unicode_codepoints(self, str):
        codepoint_format = '\\u{0:04x}'.format

        def codepoint(m):
            return codepoint_format(ord(m.group(0)))

        return re.sub('[^\x00-\x7f]', codepoint, str)

__all__ = ["JSEngine"]