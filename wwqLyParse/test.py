#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


from main import *

if __name__ == "__main__":
    # main("http://www.iqiyi.com/v_19rrl8pmn8.html", types="list")
    # main("http://www.iqiyi.com/v_19rrl8pmn8.html", parsers_name=["IQiYiMParser", "IQiYiParser"])
    # main("http://www.iqiyi.com/v_19rrl8pmn8.html", label="fullhd@IQiYiParser")
    # main("http://www.iqiyi.com/v_19rrl8pmn8.html", parsers_name=["ykdlparser.YKDLParser"])
    # main("http://www.iqiyi.com/v_19rrl8pmn8.html", label="1_BD_1080p_0@YKDLParser")
    # main("http://www.iqiyi.com/v_19rrl8pmn8.html", parsers_name=["yougetparser.YouGetParser"])
    # main("http://www.iqiyi.com/v_19rrl8pmn8.html", label="4_BD_1080p_0@YouGetParser")
    # main("http://www.le.com/ptv/vplay/25047584.html", parsers_name=["LypPvParser"])
    # main("http://www.le.com/ptv/vplay/25047584.html", label="4.0@LypPvParser")
    # main("http://www.le.com/ptv/vplay/25047584.html", parsers_name=["ykdlparser.YKDLParser"], types="formats")
    # main("http://www.le.com/ptv/vplay/25047584.html", label="0_TD_超清_0@YKDLParser")
    main("http://www.mgtv.com/b/308710/3917451.html", parsers_name=["YKDLParser"])
    main("http://www.mgtv.com/b/308710/3917451.html", label="1_TD_超清_0@YKDLParser")
    # main("http://v.youku.com/v_show/id_XMTYxODUxOTEyNA==.html?f=27502474", parsers_name=["YKDLParser"])
    # main("http://v.youku.com/v_show/id_XMTYxODUxOTEyNA==.html?f=27502474", label="3_BD_1080p_2.00 GB@YKDLParser")
    close()
