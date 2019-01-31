#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib.request, io, os, sys, json, re, threading, logging

from pyquery.pyquery import PyQuery

try:
    from ..common import *
except Exception as e:
    from common import *

__all__ = ["IQiYiAListParser", "IQiYiAListParser2",
           "IQiYiAListParser3", "IQiYiAListParser4",
           "IQiYiLibMListParser", "IQiYiVListParser"]


class IQiYiAListParser(Parser):
    filters = ["www.iqiyi.com/a_"]
    types = ["list"]
    RE_GET_AID = ' albumId: "([0-9]+)",'  # albumId: 202340701,
    RE_GET_CID = ' cid: "([0-9]+)",'  # cid: 2,
    """

    window.Q = window.Q || {};
    Q.PageInfo = Q.PageInfo || {};
    Q.PageInfo.playPageInfo = {
        albumId: "219950401",
        tvId: "898515400",
        sourceId: 0,
        cid: "2",
        videoLine: 0,
        position: 'album',
        pageType: 'zhuanji'
    };

    """
    # http://cache.video.qiyi.com/jp/avlist/202340701/2/
    URL_JS_API_PORT = 'http://cache.video.qiyi.com/jp/avlist/{}/{}/'
    MANY_PAGE = True
    PAGE_ID_START = 0
    PAGE_ID_END = sys.maxsize
    ONLY_IGNORE_EMPTY_PAGE = False
    ADD_NO_TO_NAME = True
    TAKE_CARE_CID = '2'
    TAKE_CARE_CID_TYPE = "INCLUDE"

    # get info from 271 javascript API port
    async def _get_info_from_js_port(self, html_text):
        # get album id
        aid = r1(self.RE_GET_AID, html_text)
        cid = r1(self.RE_GET_CID, html_text)
        # get info list
        vlist = await self._get_vinfo_list(aid, cid)
        # done
        return vlist

    # make js API port URL
    def _make_port_url(self, aid, cid, page_n=None):
        if self.MANY_PAGE:
            url = self.URL_JS_API_PORT.format(aid, page_n)
        else:
            url = self.URL_JS_API_PORT.format(aid)
        # print(url)
        return url

    # get vinfo list, get full list from js API port
    async def _get_vinfo_list(self, aid, cid):
        vlist = []
        # request each page
        page_n = self.PAGE_ID_START
        urls = []
        while page_n < self.PAGE_ID_END:
            # make request url
            page_n += 1
            url = self._make_port_url(aid, cid, page_n)
            # get text
            raw_text = await get_url_service.get_url_async(url)

            # get list
            sub_list = self._parse_one_page(raw_text)
            for sub in sub_list:
                url = sub['url']
                if url in urls:
                    sub_list = []
                else:
                    urls.append(url)
            if len(sub_list) > 0:
                vlist += sub_list
            else:  # no more data
                if not self.ONLY_IGNORE_EMPTY_PAGE:
                    break
            if not self.MANY_PAGE:
                break
        # get full vinfo list done
        return vlist

    # parse one page info, parse raw info
    def _parse_one_page(self, raw_text):
        # remove 'var tvInfoJs={' before json text, and json just ended with '}'
        json_text = '{' + raw_text.split('{', 1)[1]
        # load as json text
        info = json.loads(json_text)

        # check code, '"code":"A00000"' is OK, and '"code":"A00004"' is out of index
        if info['code'] == 'A00004':
            return []  # just return null result

        return self._parse_one_page_json(info)

    # parse one page json
    def _parse_one_page_json(self, info):
        # get and parse video info items
        vlist = info['data']['vlist']
        out = []  # output info
        for v in vlist:
            if v.get('type', 1) == "0":
                continue
            one = {}

            one['no'] = v['pd']
            one['title'] = v['vn']
            one['subtitle'] = v['vt']
            one['url'] = v['vurl']

            out.append(one)
        # get video info done
        return out

    async def _get_list_info_api(self, html_text):
        # get info from js API port
        info2 = await self._get_info_from_js_port(html_text)
        # replace vlist with js port data
        vlist = []
        for i in info2:
            one = {}
            if self.ADD_NO_TO_NAME:
                one['no'] = "第" + str(i['no']) + "集 " + str(i['subtitle'])
            else:
                one['no'] = i['title']
            one['subtitle'] = i['subtitle']
            one['url'] = i['url']
            vlist.append(one)
        # done
        return vlist

    async def _check_support(self, input_text):
        html_text = await get_url_service.get_url_async(input_text)
        # get cid
        cid = r1(self.RE_GET_CID, html_text)
        if self.TAKE_CARE_CID_TYPE == "INCLUDE":
            if cid is None or cid == self.TAKE_CARE_CID:
                return True
            else:
                logging.debug("%s ignore by cid: %s" % (str(self), cid))
                return False
        elif self.TAKE_CARE_CID_TYPE == "EXCLUDE":
            if cid is None or cid != self.TAKE_CARE_CID:
                return True
            else:
                logging.debug("%s ignore by cid: %s" % (str(self), cid))
                return False
        else:
            return True

    async def parse(self, input_text, *k, **kk):
        if not await self._check_support(input_text):
            return []
        html_text = await get_url_service.get_url_async(input_text)
        html = PyQuery(html_text)
        title = html('h1.main_title > a').text()
        if not title:
            for a in html('div.crumb-item > a'):
                a = PyQuery(a)
                if a.attr('href') in input_text:
                    title = a.text()
        if not title:
            try:
                title = match1(html_text, '<title>([^<]+)').split('-')[0]
            except AttributeError:
                pass
        data = {
            "data": [],
            "more": False,
            "title": title,
            "total": 0,
            "type": "list",
            "caption": "271视频全集"
        }
        data["data"] = await self._get_list_info_api(html_text)
        return data


class IQiYiAListParser2(IQiYiAListParser):
    # RE_GET_AID = ' albumId: "([0-9]+)",'  # albumId: 203342201,
    """

    window.Q = window.Q || {};
    Q.PageInfo = Q.PageInfo || {};
    Q.PageInfo.playPageInfo = {
        albumId: "203342201",
        tvId: "439048900",
        sourceId: 203342201,
        cid: "6",
        videoLine: 0,
        position: 'album',
        pageType: 'zhuanji'
    };

    """
    # http://cache.video.qiyi.com/jp/sdvlst/6/203342201/
    URL_JS_API_PORT = 'http://cache.video.qiyi.com/jp/sdvlst/{}/{}/'

    TAKE_CARE_CID = '2'
    TAKE_CARE_CID_TYPE = "EXCLUDE"
    MANY_PAGE = False
    ADD_NO_TO_NAME = False

    # make js API port URL
    def _make_port_url(self, aid, cid, page_n=None):
        url = self.URL_JS_API_PORT.format(cid, aid)
        # print(url)
        return url

    # parse one page json
    def _parse_one_page_json(self, info):
        # get and parse video info items
        vlist = info['data']
        out = []  # output info
        for v in vlist:
            one = {}

            one['no'] = v['desc']
            one['title'] = v['desc']
            one['subtitle'] = v['shortTitle']
            one['url'] = v['vUrl']

            out.append(one)
        # get video info done
        return out


class IQiYiAListParser3(IQiYiAListParser):
    replace_if_exists = ["IQiYiAListParser"]

    # https://pcw-api.iqiyi.com/albums/album/avlistinfo?aid=202340701&size=50&page=2
    URL_JS_API_PORT = "https://pcw-api.iqiyi.com/albums/album/avlistinfo?aid={}&size=50&page={}"
    # TAKE_CARE_CID = '2'
    TAKE_CARE_CID_TYPE = "ALL"

    # parse one page json
    def _parse_one_page_json(self, info):
        # get and parse video info items
        vlist = info['data']['epsodelist']
        out = []  # output info
        for v in vlist:
            one = {}

            one['no'] = v['order']
            one['title'] = v['name']
            one['subtitle'] = v.get('subtitle', '')
            one['url'] = v['playUrl']

            out.append(one)
        # get video info done
        return out


class IQiYiAListParser4(IQiYiAListParser):
    replace_if_exists = ["IQiYiAListParser2", "IQiYiAListParser3"]

    # https://pcw-api.iqiyi.com/album/source/svlistinfo?cid=6&sourceid=203342201&timelist=2016
    URL_JS_API_PORT = "https://pcw-api.iqiyi.com/album/source/svlistinfo?cid={}&sourceid={}&timelist=" + \
                      "%2C".join(str(i) for i in range(2000, 2051))
    TAKE_CARE_CID = '2'
    TAKE_CARE_CID_TYPE = "EXCLUDE"
    MANY_PAGE = False
    ADD_NO_TO_NAME = False

    # make js API port URL
    def _make_port_url(self, aid, cid, page_n=None):
        url = self.URL_JS_API_PORT.format(cid, aid)
        # print(url)
        return url

    # parse one page json
    def _parse_one_page_json(self, info):
        # get and parse video info items
        vlist = info['data']
        out = []  # output info
        for _v in vlist.values():
            for v in _v:
                one = {}

                one['no'] = v['order']
                one['title'] = v['name']
                one['subtitle'] = v['subtitle']
                one['url'] = v['playUrl']

                out.append(one)
        # get video info done
        return out


class IQiYiLibMListParser(Parser):
    filters = ["www.iqiyi.com/lib/m"]
    types = ["list"]

    async def parse(self, input_text, *k, **kk):
        html = PyQuery(await get_url_service.get_url_async(input_text))
        a = html("a.albumPlayBtn")
        url = a.attr("href")
        if str(url).startswith("//"):
            url = "http:" + str(url)
        logging.info("change %s to %s" % (input_text, url))
        if url and re.search(r"www.iqiyi.com/lib/m", url):
            url = None
        if url:
            return ReCallMainParseFunc(input_text=url, types="list")

        """
        album_items = html('div.clearfix').children('li.album_item')
        title = html('h1.main_title').children('a').text()
        i =0
        data = {
            "data": [],
            "more": False,
            "title": title,
            "total": i,
            "type": "list"
        }
        for album_item in album_items:
            no = '第'+str(i+1)+'集'
            name = title+'('+no+')'
            url = PyQuery(album_item).children('a').attr('href')
            subtitle = ''
            info = {
                "name": name,
                "no": no,
                "subtitle": subtitle,
                "url": url
            }
            data["data"].append(info)
            i = i+1
        total = i
        data["total"] = total
        """
        data = {
            "data": [],
            "more": False,
            "title": '',
            "total": 0,
            "type": "list",
            "caption": "271视频全集"
        }

        data_doc_id = html('span.play_source').attr('data-doc-id')
        if data_doc_id:
            ejson_url = 'http://rq.video.iqiyi.com/aries/e.json?site=iqiyi&docId=' + data_doc_id + '&count=100000'
            ejson = json.loads(await get_url_service.get_url_async(ejson_url))
            ejson_datas = ejson["data"]["objs"]
            data["total"] = ejson_datas["info"]["total_video_number"]
            data["title"] = ejson_datas["info"]["album_title"]
            album_items = ejson_datas["episode"]["data"]
            for album_item in album_items:
                no = '第' + str(album_item["play_order"]) + '集'
                name = album_item["title"]
                url = album_item["play_url"]
                subtitle = album_item["desciption"]
                info = {
                    "name": name,
                    "no": no,
                    "subtitle": subtitle,
                    "url": url
                }
                data["data"].append(info)
            # print(ejson)
        return data


class IQiYiVListParser(Parser):
    filters = ["www.iqiyi.com/v_"]
    types = ["list"]

    async def parse(self, input_text, *k, **kk):
        logging.debug(input_text)
        html = PyQuery(await get_url_service.get_url_async(input_text))
        url = ""
        # logging.debug(html)
        if not url:
            jss = html("script[type='text/javascript']")
            for item in jss:
                text = PyQuery(item).text()
                # logging.debug(text)
                if "Q.PageInfo.playPageData = {" in text or \
                        "Q.PageInfo.playPageInfo = Q.PageInfo.playPageInfo || {" in text:
                    split_text = text.replace("\r", ""). \
                                     replace("\n", ""). \
                                     replace("Q.PageInfo.playPageData = {", ""). \
                                     replace("window.Q = window.Q || {};", ""). \
                                     replace("var Q = window.Q; Q.PageInfo = Q.PageInfo || {};", ""). \
                                     replace("Q.PageInfo.playPageInfo = Q.PageInfo.playPageInfo ||", ""). \
                                     strip(). \
                                     replace("albumData:", ""). \
                                     strip()[:-1].strip()
                    logging.debug(split_text)
                    try:
                        data = json.loads(split_text)
                        print(json.dumps(data))
                        if "mixinVideos" in data and type(data["mixinVideos"]) == list:
                            for item1 in data["mixinVideos"]:
                                if type(item1) == dict and 'crumbList' in item1 and type(item1['crumbList']) == list:
                                    for item2 in item1['crumbList']:
                                        if type(item2) == dict and 'level' in item2 and \
                                                item2['level'] == 3 and 'url' in item2:
                                            url = item2['url']
                                            if url and re.search(r"www.iqiyi.com/v_", url):
                                                url = None
                                if url:
                                    logging.debug(url)
                                    break
                        elif "albumUrl" in data and data["albumUrl"]:
                            url = "http:" + data["albumUrl"]
                            logging.debug(url)
                            break
                    except json.JSONDecodeError:
                        logging.exception("IQiYiVListParser Error")
                if url:
                    break
        if not url:
            ld_json = html("script[type='application/ld+json']")
            for item in ld_json:
                text = PyQuery(item).text().replace("\n", "").replace("\r", "")
                try:
                    data = json.loads(text)
                    if "itemListElement" in data and type(data["itemListElement"]) == list:
                        for item1 in data["itemListElement"]:
                            if type(item1) == dict and 'position' in item1 and \
                                    item1['position'] == 3 and 'item' in item1:
                                if type(item1['item']) == dict and '@id' in item1['item']:
                                    url = item1['item']['@id']
                                    if url and re.search(r"www.iqiyi.com/v_", url):
                                        url = None
                        if url:
                            logging.debug(url)
                            break
                except json.JSONDecodeError:
                    logging.exception("IQiYiVListParser Error")
                if url:
                    break
        if not url:
            data_info_list = PyQuery(html("h2.playList-title-txt"))
            for a in data_info_list.children('a'):
                a = PyQuery(a)
                url = a.attr("href")
                if url:
                    logging.debug(url)
                    break
        if not url:
            a = PyQuery(html("a[data-albumurlkey]"))
            url = a.attr("href")
            logging.debug(url)
        if url and re.search(r"www.iqiyi.com/v_", url):
            url = None
        if url:
            if str(url).startswith("//"):
                url = "http:" + str(url)
            logging.info("change %s to %s" % (input_text, url))
            return ReCallMainParseFunc(input_text=url, types="list")

    # plan B
    # http://cache.video.qiyi.com/jp/vi/451038600/faca833cc73ec8d7d8d248199bc3e7b8/?callback=Q9edfe6276cafa46823e1a575b86be2cb
    # <script type="text/javascript">
    #   QiyiPlayerLoader.ready(function(playerManager) {
    #     var param = {};
    #     param['parentId'] = 'flashbox';
    #     param['albumid'] = "203622401";
    #     param['tvid'] = "451038600";
    #     param['vid'] = "faca833cc73ec8d7d8d248199bc3e7b8";
    #     param['albumId'] = "203622401";
    #     param['channelID'] = "2";
    #     param['isMember'] = "false";
    #     param['qiyiProduced'] = "0";
    #     param['exclusive'] = "0";
    #     param['origin'] = "flash";
    #     param['collectionID'] = "";
    #     param['share_sTime'] = "";
    #     param['share_eTime'] = "";
    #     param['autoplay'] = true;
    #     param['cyclePlay'] = false;
    #     param['isSource'] = "0";
    #     param['pgct'] = window.__qlt.statisticsStart;
    #     param['usevr'] = false;
    #     param['supportedDrmTypes']  = 0;
    #     param['ppt']  = 0;
    #     playerManager.createPlayer(param);
    #   });
    # </script>
    # ------result------
    # try{Q9edfe6276cafa46823e1a575b86be2cb(
    # {"shortTitle":"五鼠闹东京DVD版第1集",
    #  "editorInfo":"王明芸 AS003",
    #  "videoQipuId":451038600,
    #  "rewardAllowed":0,
    #  "nurl":"http:\/\/www.iqiyi.com\/v_19rrl8pofw.html",
    # ...................................................
    #  });}catch(e){};

# backup(unused)
# def get_list_info_html(html):
#     # print("get_list_info_html")
#     data = []
#     album_items = html('ul.site-piclist').children('li')
#     for album_item in album_items:
#         album_item = PyQuery(album_item)
#         site_piclist_info = PyQuery(album_item.children('div.site-piclist_info'))
#         site_piclist_info_title = PyQuery(site_piclist_info.children('p.site-piclist_info_title'))
#         site_piclist_info_title_a = PyQuery(site_piclist_info_title.children('a'))
#         site_piclist_info_title_fs12 = PyQuery(site_piclist_info.children('p.fs12'))
#         site_piclist_info_title_fs12_a = PyQuery(site_piclist_info_title_fs12.children('a'))
#         no = site_piclist_info_title_a.text()
#         # if re.search("预告",no):
#         # continue
#         name = site_piclist_info_title_fs12_a.text()
#         url = site_piclist_info_title_fs12_a.attr('href')
#         if url is None:
#             continue
#         subtitle = site_piclist_info_title_fs12_a.text()
#         info = {
#             "name": name,
#             "no": no,
#             "subtitle": subtitle,
#             "url": url
#         }
#         data.append(info)
#     return data
