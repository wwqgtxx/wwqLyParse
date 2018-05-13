#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>

if __name__ == "__main__":
    try:
        from gevent import monkey

        monkey.patch_all()
        del monkey
    except Exception:
        gevent = None
    import os
    import sys

    _srcdir = os.path.dirname(os.path.realpath(__file__))
    _filepath = os.path.dirname(sys.argv[0])
    sys.path.insert(0, os.path.join(_filepath, _srcdir))

    print(sys.path)
    del sys
    del os

from main import *

if __name__ == "__main__":
    # main(r"file:///E:\QQDownloads\11.m3u8")
    # main(r"file:///E:\QQDownloads\a.list")
    # main(r"file:///E:\QQDownloads\url.media")
    # main("http://v.pptv.com/show/MxfOTcmjmtg7uSE.html", parsers_name=["PPTVParser"])
    # main("http://v.pptv.com/show/MxfOTcmjmtg7uSE.html", types="list")
    # main(r"https://youku.pohaier.com/yk.php?url=d1BTTTFlVnRTell1VDhtQmlLZ3lrTkZSUGtTdlhrY3JOZlJOTnZZRmE2ZDZiSVNkNU9rdVJoMlBoL1doR1FDRGVmWkJCR25rbkE=")
    # main("http://defaultts.tc.qq.com/defaultts.tc.qq.com/mcvctgljBW77YvaEtxIhsDu81rGkBDNrvJH-aOijrz6vYDOAERMwo8YjsMhsUX30gycp3l48NFvhiK0q8RrcI_piINVQwY4sfKdsmv5qi459Q7GV-rljooWl1yRZcP-f/c00248syj3f.321004.ts.m3u8?ver=4")
    # main("http://v.yinyuetai.com/video/3080638", parsers_name=["YinYueTaiParser"])
    # main("http://v.yinyuetai.com/video/2796852", parsers_name=["YinYueTaiParser"])
    # main("http://www.mgtv.com/b/316045/4096972.html", types="collection")
    # main("http://www.mgtv.com/b/316045/4096972.html", parsers_name=["MgTVParser"])
    # main("http://www.mgtv.com/b/316045/4096972.html", label="3@MgTVParser")
    # url_cache.timeout = 10
    # main("http://www.iqiyi.com/lib/m_201087714.html")
    # main("http://www.iqiyi.com/v_19rrcl8dck.html", types="list")
    # main("http://www.iqiyi.com/v_19rr8jbmeo.html", types="list")
    # main("http://www.iqiyi.com/v_19rrl8pmn8.html")
    # time.sleep(10)
    # main("http://www.iqiyi.com/v_19rrl8pmn8.html", types="list")
    # main("http://www.iqiyi.com/v_19rrl8pmn8.html", parsers_name=["IQiYiMTsParser"])
    # main("http://www.iqiyi.com/v_19rrl8pmn8.html", parsers_name=["IQiYiParser"])
    # main("http://www.iqiyi.com/v_19rrl8pmn8.html", label="1080P-H264@IQiYiParser")
    # main("http://www.le.com/ptv/vplay/25047584.html", parsers_name=["YKDLParser"], types="formats")
    # main("http://www.le.com/ptv/vplay/25047584.html", label="0_TD_超清_0@YKDLParser")
    # main("https://www.bilibili.com/video/av21877586", parsers_name=["AnnieParser"])
    # main("https://www.bilibili.com/video/av21877586", label="default@AnnieParser")
    # main("https://www.bilibili.com/video/av21877586", label="64@AnnieParser")
    # main("https://www.bilibili.com/video/av17246756/", parsers_name=["YKDLParser"])
    main("https://www.bilibili.com/video/av21877586", label="BD@YKDLParser")
    # main("https://www.bilibili.com/video/av17246756/", parsers_name=["YouGetParser"])
    # main("https://www.bilibili.com/video/av17246756/", label="flv@YouGetParser")
    # main("http://www.bilibili.com/video/av3153352/", parsers_name=["YouGetParser"])
    # main("http://www.bilibili.com/video/av3153352/", label="hdflv@YouGetParser")
    # main("http://www.le.com/ptv/vplay/27416375.html", parsers_name=["YouGetParser"])
    # main("http://www.le.com/ptv/vplay/1981824.html", types="list")
    # main("http://www.le.com/ptv/vplay/27416375.html", parsers_name=["LeParser"])
    # main("http://www.le.com/ptv/vplay/27416375.html", label="1080p@LeParser")
    # main("https://v.youku.com/v_show/id_XMzU1MjQyNzk2OA==.html", types="list")
    # main("https://v.youku.com/v_show/id_XMzU3MTI0OTgyMA==.html", types="list")
    # main("http://v.youku.com/v_show/id_XMjcxMzkwMjU3Mg==.html", types="list")
    # main("http://v.youku.com/v_show/id_XMTYxODUxOTEyNA==.html?f=27502474")
    # main("http://v.youku.com/v_show/id_XMjQ4MTc0ODMyOA==.html?spm=a2h1n.8251845.0.0", parsers_name=["AnnieParser"])
    # main("http://v.youku.com/v_show/id_XMjQ4MTc0ODMyOA==.html?spm=a2h1n.8251845.0.0", label="default@AnnieParser")
    # main("http://v.youku.com/v_show/id_XMjQ4MTc0ODMyOA==.html?spm=a2h1n.8251845.0.0", parsers_name=["YouGetParser"])
    # main("http://v.youku.com/v_show/id_XMjQ4MTc0ODMyOA==.html?spm=a2h1n.8251845.0.0", parsers_name=["YKDLParser"])
    # main("http://v.youku.com/v_show/id_XMTYxODUxOTEyNA==.html?f=27502474", label="BD@YKDLParser")
    # main("http://v.youku.com/v_show/id_XMzg1ODY1MTIw.html||123", parsers_name=["YouGetParser"])
    # main("http://list.youku.com/albumlist/show/id_2336634.html", types="collection")
    # main("https://v.youku.com/v_show/id_XMzE2MzM2NTMyNA==.html?spm=a2hww.20027244.m_250379.5~5~1~3!4~A")
    # main("http://video.tudou.com/v/XMzAxODM2MDA1Mg==.html?spm=a2h28.8313475.c1.dtitle2")
    # close()
    # init_version()
    # print(version)
    pass
