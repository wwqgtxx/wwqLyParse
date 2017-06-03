#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>

from common import *
from pyquery.pyquery import PyQuery

if __name__ == "__main__":
    from main import *

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
    # main("http://www.mgtv.com/b/308710/3917451.html", parsers_name=["YouGetParser"])
    # main("http://www.mgtv.com/b/308710/3917451.html", label="2_hd_超清_982.06 MB@YouGetParser")
    # main("http://www.mgtv.com/b/308710/3917451.html", parsers_name=["YKDLParser"])
    # main("http://www.mgtv.com/b/308710/3917451.html", label="1_TD_超清_0@YKDLParser")
    # main("http://www.bilibili.com/video/av3153352/", parsers_name=["YouGetParser"])
    # main("http://www.bilibili.com/video/av3153352/", label="0_default__2.80 MB@YouGetParser")
    # main("http://www.le.com/ptv/vplay/27416375.html", parsers_name=["YouGetParser"])
    main("http://www.le.com/ptv/vplay/1981824.html", types="list")
    # main("http://v.youku.com/v_show/id_XMjcxMzkwMjU3Mg==.html", types="list")
    # main("http://v.youku.com/v_show/id_XMTYxODUxOTEyNA==.html?f=27502474", parsers_name=["YouGetParser"])
    # main("http://v.youku.com/v_show/id_XMTYxODUxOTEyNA==.html?f=27502474", parsers_name=["YKDLParser"])
    # main("http://v.youku.com/v_show/id_XMTYxODUxOTEyNA==.html?f=27502474", label="3_BD_1080p_2.00 GB@YKDLParser")
    # close()
    # print(getUrl("http://183.131.245.38/218/40/46/letv-uts/14/ver_00_22-1095122980-avc-420009-aac-48000-3529600-211910027-3382c87ddc75c42783b74ea9e3092f47-1491593062870.m3u8?crypt=90aa7f2e180&b=480&nlh=4096&nlt=60&bf=30&p2p=1&video_type=mp4&termid=1&tss=ios&platid=1&splatid=101&its=0&qos=3&fcheck=0&amltag=100&mltag=100&proxy=1945012610,3079193363,611247581&uid=3069515166.rp&keyitem=GOw_33YJAAbXYE-cnQwpfLlv_b2zAkYctFVqe5bsXQpaGNn3T1-vhw..&ntm=1496506200&nkey=bbdd907a2610533bda51590c9e543dd3&nkey2=6d3d5cda304049fecde5c00d2bbbb44d&geo=CN-25-353-1&mmsid=62409838&tm=1496487956&key=74da91b87a869e8cfad574849eb03dda&playid=0&vtype=13&cvid=1290815915280&payff=0&m3v=1&hwtype=un&ostype=MacOS10.12.4&p1=1&p2=10&p3=-&tn=0.5462534467249832&vid=27416375&uuid=decdf201614806f14a1cf57434b9f4b291be47ce_0&sign=letv&uidx=0&errc=0&gn=898&ndtype=0&vrtmcd=202&buss=100&cips=182.245.21.158&r=1496487989439&appid=500"))
    # import requests
    # url="http://183.131.245.38/218/40/46/letv-uts/14/ver_00_22-1095122980-avc-420009-aac-48000-3529600-211910027-3382c87ddc75c42783b74ea9e3092f47-1491593062870.m3u8?crypt=90aa7f2e180&b=480&nlh=4096&nlt=60&bf=30&p2p=1&video_type=mp4&termid=1&tss=ios&platid=1&splatid=101&its=0&qos=3&fcheck=0&amltag=100&mltag=100&proxy=1945012610,3079193363,611247581&uid=3069515166.rp&keyitem=GOw_33YJAAbXYE-cnQwpfLlv_b2zAkYctFVqe5bsXQpaGNn3T1-vhw..&ntm=1496506200&nkey=bbdd907a2610533bda51590c9e543dd3&nkey2=6d3d5cda304049fecde5c00d2bbbb44d&geo=CN-25-353-1&mmsid=62409838&tm=1496487956&key=74da91b87a869e8cfad574849eb03dda&playid=0&vtype=13&cvid=1290815915280&payff=0&m3v=1&hwtype=un&ostype=MacOS10.12.4&p1=1&p2=10&p3=-&tn=0.5462534467249832&vid=27416375&uuid=decdf201614806f14a1cf57434b9f4b291be47ce_0&sign=letv&uidx=0&errc=0&gn=898&ndtype=0&vrtmcd=202&buss=100&cips=182.245.21.158&r=1496487989439&appid=500"
    # fake_headers = {
    #     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    #     'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
    #     'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:38.0) Gecko/20100101 Firefox/38.0 Iceweasel/38.2.1'
    # }
    # s = requests.Session()
    # r= s.get(url,headers=fake_headers)
    # print(r.request.headers)
    # # print(r.content)
    # r = s.get(url, headers=fake_headers)
    # print(r.request.headers)
    # # print(r.content)
