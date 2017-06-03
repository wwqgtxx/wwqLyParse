#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib.request, io, os, sys, json, re, threading, queue, logging

from pyquery.pyquery import PyQuery

try:
    from ..common import *
except Exception as e:
    from common import *

__MODULE_CLASS_NAMES__ = ["IQiYiAListParser", "IQiYiLibMListParser", "IQiYiVListParser"]


class IQiYiAListParser(Parser):
    filters = ["www.iqiyi.com/a_"]
    types = ["list"]

    def Parse(self, input_text, pool=pool_getUrl):
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
                    raw_text = getUrl(url, pool=pool)

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
                raw_text = getUrl(url, pool=pool)
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
                i = i + 1
            return data

        # print("2"+input_text)
        def run(queue, get_list_info, html_text):
            try:
                result = get_list_info(html_text)
                if result != []:
                    queue.put(result)
            except Exception as e:
                # import traceback
                # traceback.print_exc()
                logging.error(str(get_list_info) + str(e))

        html_text = getUrl(input_text, pool=pool)
        html = PyQuery(html_text)
        title = html('h1.main_title').children('a').text()
        for a in html('div.crumb-item').children('a'):
            a = PyQuery(a)
            if a.attr('href') in input_text:
                title = a.text()
        i = 0
        data = {
            "data": [],
            "more": False,
            "title": title,
            "total": i,
            "type": "list",
            "caption": "271视频全集"
        }
        results = []
        parser_threads = []
        q_results = queue.Queue()
        parser_threads.append(threading.Thread(target=run, args=(q_results, get_list_info_api1, html_text)))
        parser_threads.append(threading.Thread(target=run, args=(q_results, get_list_info_api2, html_text)))
        for parser_thread in parser_threads:
            parser_thread.start()
        for parser_thread in parser_threads:
            parser_thread.join()
        while not q_results.empty():
            data["data"] = q_results.get()
            break
        if data["data"] == []:
            try:
                data["data"] = get_list_info_html(html)
            except Exception as e:
                # import traceback
                # traceback.print_exc()
                logging.error(str(get_list_info_html) + e)

        data["total"] = len(data["data"])
        return data


class IQiYiLibMListParser(Parser):
    filters = ["www.iqiyi.com/lib/m"]
    types = ["list"]

    def Parse(self, input_text, pool=pool_getUrl):
        html = PyQuery(getUrl(input_text, pool=pool))

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
        ejson_url = 'http://rq.video.iqiyi.com/aries/e.json?site=iqiyi&docId=' + data_doc_id + '&count=100000'
        ejson = json.loads(getUrl(ejson_url, pool=pool))
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

    def Parse(self, input_text, pool=pool_getUrl):
        logging.debug(input_text)
        html = PyQuery(getUrl(input_text, pool=pool))
        datainfo_navlist = PyQuery(html("#datainfo-navlist"))
        for a in datainfo_navlist.children('a'):
            a = PyQuery(a)
            url = a.attr("href")
            logging.info("change %s to %s" % (input_text, url))
            try:
                from ..main import Parse as main_parse
            except Exception as e:
                from main import Parse as main_parse
            result = main_parse(input_text=url, types="list")
            if result:
                return result[0]
