#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib.request, io, os, sys, json, re, threading, queue, logging

from pyquery.pyquery import PyQuery

try:
    from ..common import *
except Exception as e:
    from common import *

__all__ = ["IQiYiAListParser", "IQiYiLibMListParser", "IQiYiVListParser"]


class IQiYiAListParser(Parser):
    filters = ["www.iqiyi.com/a_"]
    types = ["list"]

    def parse(self, input_text, *k, **kk):
        # modity from sceext2's list271.py
        def get_list_info_api1(html_text):
            RE_GET_AID = ' albumId: ([0-9]+),'  # albumId: 202340701,
            # http://cache.video.qiyi.com/jp/avlist/202340701/2/
            URL_JS_API_PORT = 'http://cache.video.qiyi.com/jp/avlist/'

            # get info from 271 javascript API port
            def get_info_from_js_port(html_text):
                # get album id
                aid = get_aid(html_text)
                # get info list
                vlist = get_vinfo_list(aid)
                # done
                return vlist

            # get album id
            def get_aid(html_text):
                m = re.findall(RE_GET_AID, html_text)
                return m[0]

            # make js API port URL
            def make_port_url(aid, page_n):
                url = URL_JS_API_PORT + str(aid) + '/' + str(page_n) + '/'
                # print(url)
                return url

            # get vinfo list, get full list from js API port
            def get_vinfo_list(aid):
                vlist = []
                # request each page
                page_n = 0
                urls = []
                while True:
                    # make request url
                    page_n += 1
                    url = make_port_url(aid, page_n)
                    # get text
                    raw_text = get_url(url)

                    # get list
                    sub_list = parse_one_page(raw_text)
                    for sub in sub_list:
                        url = sub['url']
                        if url in urls:
                            sub_list = []
                        else:
                            urls.append(url)
                    if len(sub_list) > 0:
                        vlist += sub_list
                    else:  # no more data
                        break
                # get full vinfo list done
                return vlist

            # parse one page info, parse raw info
            def parse_one_page(raw_text):
                # remove 'var tvInfoJs={' before json text, and json just ended with '}'
                json_text = '{' + raw_text.split('{', 1)[1]
                # load as json text
                info = json.loads(json_text)

                # check code, '"code":"A00000"' is OK, and '"code":"A00004"' is out of index
                if info['code'] == 'A00004':
                    return []  # just return null result

                # get and parse video info items
                vlist = info['data']['vlist']
                out = []  # output info
                for v in vlist:
                    one = {}

                    one['no'] = v['pd']
                    one['title'] = v['vn']
                    one['subtitle'] = v['vt']
                    one['url'] = v['vurl']

                    # get more info
                    one['vid'] = v['vid']
                    one['time_s'] = v['timeLength']
                    one['tvid'] = v['id']

                    out.append(one)
                # get video info done
                return out

            # get info from js API port
            info2 = get_info_from_js_port(html_text)
            # replace vlist with js port data
            vlist = []
            for i in info2:
                one = {}
                one['no'] = "第" + str(i['no']) + "集 " + str(i['subtitle'])
                one['subtitle'] = i['subtitle']
                one['url'] = i['url']
                vlist.append(one)
            # done
            return vlist

        def get_list_info_api2(html_text):
            RE_GET_AID = ' albumId: ([0-9]+),'  # albumId: 203342201,
            # http://cache.video.qiyi.com/jp/sdvlst/6/203342201/
            URL_JS_API_PORT = 'http://cache.video.qiyi.com/jp/sdvlst/6/'

            # get info from 271 javascript API port
            def get_info_from_js_port(html_text):
                # get album id
                aid = get_aid(html_text)
                # get info list
                vlist = get_vinfo_list(aid)
                # done
                return vlist

            # get album id
            def get_aid(html_text):
                m = re.findall(RE_GET_AID, html_text)
                return m[0]

            # make js API port URL
            def make_port_url(aid):
                url = URL_JS_API_PORT + str(aid) + '/'
                # print(url)
                return url

            # get vinfo list, get full list from js API port
            def get_vinfo_list(aid):
                vlist = []
                # make request url
                url = make_port_url(aid)
                # get text
                raw_text = get_url(url)
                # get list
                vlist = parse_one_page(raw_text)
                # get full vinfo list done
                return vlist

            # parse one page info, parse raw info
            def parse_one_page(raw_text):
                # remove 'var tvInfoJs={' before json text, and json just ended with '}'
                json_text = '{' + raw_text.split('{', 1)[1]
                # load as json text
                info = json.loads(json_text)

                # check code, '"code":"A00000"' is OK, and '"code":"A00004"' is out of index
                if info['code'] == 'A00004':
                    return []  # just return null result

                # get and parse video info items
                vlist = info['data']
                out = []  # output info
                for v in vlist:
                    one = {}

                    one['no'] = v['desc']
                    one['title'] = v['desc']
                    one['subtitle'] = v['shortTitle']
                    one['url'] = v['vUrl']

                    # get more info
                    one['vid'] = v['vid']
                    one['time_s'] = v['timeLength']
                    one['tvid'] = v['tvId']

                    out.append(one)
                # get video info done
                return out

            # get info from js API port
            info2 = get_info_from_js_port(html_text)
            # replace vlist with js port data
            vlist = []
            for i in info2:
                one = {}
                one['no'] = i['no']
                one['subtitle'] = i['subtitle']
                one['url'] = i['url']
                vlist.append(one)
            # done
            return vlist

        def get_list_info_html(html):
            # print("get_list_info_html")
            data = []
            album_items = html('ul.site-piclist').children('li')
            for album_item in album_items:
                album_item = PyQuery(album_item)
                site_piclist_info = PyQuery(album_item.children('div.site-piclist_info'))
                site_piclist_info_title = PyQuery(site_piclist_info.children('p.site-piclist_info_title'))
                site_piclist_info_title_a = PyQuery(site_piclist_info_title.children('a'))
                site_piclist_info_title_fs12 = PyQuery(site_piclist_info.children('p.fs12'))
                site_piclist_info_title_fs12_a = PyQuery(site_piclist_info_title_fs12.children('a'))
                no = site_piclist_info_title_a.text()
                # if re.search("预告",no):
                # continue
                name = site_piclist_info_title_fs12_a.text()
                url = site_piclist_info_title_fs12_a.attr('href')
                if url is None:
                    continue
                subtitle = site_piclist_info_title_fs12_a.text()
                info = {
                    "name": name,
                    "no": no,
                    "subtitle": subtitle,
                    "url": url
                }
                data.append(info)
            return data

        # print("2"+input_text)
        html_text = get_url(input_text)
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
        q_results = queue.Queue()
        with WorkerPool() as pool:
            pool.spawn(call_method_and_save_to_queue, queue=q_results, method=get_list_info_api1, args=(html_text,),
                       allow_none=False)
            pool.spawn(call_method_and_save_to_queue, queue=q_results, method=get_list_info_api2, args=(html_text,),
                       allow_none=False)
            pool.join()
        while not q_results.empty():
            data["data"] = q_results.get()
            break
        if not data["data"]:
            try:
                data["data"] = get_list_info_html(html)
            except Exception:
                # import traceback
                # traceback.print_exc()
                logging.exception(str(get_list_info_html))

        data["total"] = len(data["data"])
        return data


class IQiYiLibMListParser(Parser):
    filters = ["www.iqiyi.com/lib/m"]
    types = ["list"]

    def parse(self, input_text, *k, **kk):
        html = PyQuery(get_url(input_text))
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
            ejson = json.loads(get_url(ejson_url))
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

    def parse(self, input_text, *k, **kk):
        logging.debug(input_text)
        html = PyQuery(get_url(input_text))
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
