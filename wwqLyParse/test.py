#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


if __name__ == "__main__":
    #import parsers.iqiyimparser
    #print(parsers.iqiyimparser.IQiYiMParser().Parse("http://www.iqiyi.com/v_19rrl8pmn8.html"))
    import parsers.ykdlparser
    #print(parsers.ykdlparser.YKDLParser().Parse("http://www.le.com/ptv/vplay/25047584.html"))
    #print(parsers.ykdlparser.YKDLParser().ParseURL("http://www.le.com/ptv/vplay/25047584.html","0_1080p_1080p_0@ykdl"))
    print(parsers.ykdlparser.YKDLParser().ParseURL("http://v.youku.com/v_show/id_XMTYxODUxOTEyNA==.html?f=27502474","3_mp4hd3_1080p_2.00 GB@ykdl"))
    #print(parsers.iqiyiparser.IQiYiParser().ParseURL("http://www.iqiyi.com/v_19rrl8pmn8.html","fullhd"))