#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>

from main import *

if __name__ == "__main__":
    #debug(Parse("http://www.iqiyi.com/v_19rrl8pmn8.html", parsers_name=["IQiYiMParser","IQiYiParser"]))
    debug(ParseURL("http://www.iqiyi.com/v_19rrl8pmn8.html","fullhd@IQiYiParser"))
    #debug(Parse("http://www.le.com/ptv/vplay/25047584.html",parsers_name=["YKDLParser"]))
    #debug(ParseURL("http://www.le.com/ptv/vplay/25047584.html","0_TD_超清_0@YKDLParser"))
    #debug(Parse("http://v.youku.com/v_show/id_XMTYxODUxOTEyNA==.html?f=27502474", parsers_name=["YKDLParser"]))
    #debug(ParseURL("http://v.youku.com/v_show/id_XMTYxODUxOTEyNA==.html?f=27502474","3_BD_1080p_2.00 GB@YKDLParser"))
