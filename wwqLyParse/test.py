#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


if __name__ == "__main__":
    import parsers.iqiyiparser
    #print(parsers.iqiyiparser.IQiYiParser().Parse("http://www.iqiyi.com/v_19rrl8pmn8.html"))
    print(parsers.iqiyiparser.IQiYiParser().ParseURL("http://www.iqiyi.com/v_19rrl8pmn8.html","fullhd"))