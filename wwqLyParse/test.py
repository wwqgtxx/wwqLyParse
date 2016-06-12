#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>

from flask import Flask
app = Flask(__name__)

@app.route('/hello/<meid>/<metype>',methods=['POST','GET'])
def hello(meid,metype):
    return meid+"Hello World!"+metype

if __name__ == "__main__":
    app.run()