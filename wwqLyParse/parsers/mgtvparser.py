#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib.request, io, os, sys, json, re

from pyquery.pyquery import PyQuery
import base64

try:
    from ..common import *
except Exception as e:
    from common import *

JUDGE_VIP = True

__all__ = ["MgTVParser", "MgTVListParser"]


def encode_tk2(string: str):
    string = base64.b64encode(string.encode()).decode()  # type:str
    string = re.sub(r'/\+/g', "_", string)
    string = re.sub(r'///g', "~", string)
    string = re.sub(r'/=/g', "-", string)
    string = string[::-1]
    return string


class MgTVParser(Parser):
    filters = [r'https?://www.mgtv.com/(?:b|l)/\d+/(\d+).html', r'https?://www.mgtv.com/hz/bdpz/\d+/(\d+).html']
    types = ["formats"]
    cookies = {"PM_CHKID": "1"}

    def get_api_data(self, url, only_api1=False):
        # id = re.match('^http://[^\s]+/[^\s]+/([^\s]+)\.html', url).group(1)

        vid = match1(url, r'https?://www.mgtv.com/(?:b|l)/\d+/(\d+).html')
        if not vid:
            vid = match1(url, r'https?://www.mgtv.com/hz/bdpz/\d+/(\d+).html')
        clit = "clit=%d" % int(time.time())
        did = str(uuid.uuid4())
        tk2 = "did={}|pno=1030|ver=5.5.1|{}".format(did, clit)
        api_url = 'https://pcweb.api.mgtv.com/player/video?video_id={}&tk2={}'.format(vid, encode_tk2(tk2))
        api_data1 = get_url(api_url, allow_cache=False, cookies=self.cookies)
        api_data1 = json.loads(api_data1)
        logging.debug(api_data1)
        assert api_data1['code'] == 200
        api_data = api_data1['data']
        if not only_api1:
            pm2 = api_data['atc']['pm2']
            api_url2 = 'https://pcweb.api.mgtv.com/player/getSource?video_id={}&tk2={}&pm2={}'.format(vid,
                                                                                                      encode_tk2(clit),
                                                                                                      pm2)
            api_data2 = get_url(api_url2, allow_cache=False, cookies=self.cookies)
            api_data2 = json.loads(api_data2)
            logging.debug(api_data2)
            assert api_data2['code'] == 200
            api_data.update(api_data2['data'])
        logging.debug(api_data)
        return api_data

    def parse(self, input_text, types=None, *k, **kk):
        data = {
            "type": "formats",
            "name": "",
            "icon": "http://xxx.cn/xxx.jpg",
            "provider": "芒果TV",
            "caption": "芒果TV解析",
            # "warning" : "提示信息",
            "sorted": 1,
            "data": []
        }
        api_data = self.get_api_data(input_text)
        info = api_data['info']
        data["name"] = info['series'] + ' ' + info['title'] + ' ' + info['desc']
        data["icon"] = info['thumb']
        for lstream in api_data['stream']:
            if lstream['url']:
                data["data"].append({
                    "label": lstream['name'],
                    "code": lstream['def'],
                    # "ext" : "",
                    # "size" : "",
                    # "type" : "",
                })
        return data

    def parse_url(self, input_text, label, min=None, max=None, *k, **kk):
        data = {
            "protocol": "m3u8",
            "urls": [],
            # "args" : {},
            # "duration" : 1111,
            # "length" : 222222,
            # "decrypt" : "KanKan",
            # "decryptData" : {},
            # "adjust" : "KanKan",
            # "adjustData" : { },
            # "segmentSize": 1024,
            # "maxDown" : 5,
            # "convert" : "",
            # "convertData" : "",
        }
        api_data = self.get_api_data(input_text)
        # domain = api_data['data']['stream_domain'][0]
        for lstream in api_data['stream']:
            if lstream['url'] and lstream['def'] == label:
                for domain in api_data['stream_domain']:
                    api_data2_url = domain + lstream['url']
                    api_data2_url = api_data2_url.replace("http://", "https://")
                    api_data2 = json.loads(get_url(api_data2_url, allow_cache=False, cookies=self.cookies))
                    # print(api_data2)
                    url = api_data2['info']
                    data["urls"].append(url)
                    break
        return [data]


class MgTVListParser(MgTVParser):
    filters = MgTVParser.filters + [r'https?://www.mgtv.com/h/(\d+).html']
    types = ["collection"]

    def parse(self, input_text, *k, **kk):
        data = {
            "data": [],
            "more": False,
            "title": '',
            "total": 0,
            "type": "collection",
            "caption": "芒果TV全集"
        }
        collection_id = match1(input_text, r'https?://www.mgtv.com/h/(\d+).html')
        if not collection_id:
            api_data = self.get_api_data(input_text, only_api1=True)
            info = api_data['info']
            collection_id = info['collection_id']
        url1 = 'https://pcweb.api.mgtv.com/variety/showlist?collection_id=' + collection_id
        api_data1 = json.loads(get_url(url1))
        # print(api_data1)
        if api_data1['code'] != 200 and not api_data1['data']:
            return []
        data['title'] = api_data1['data']['info']['title']
        for tab in api_data1['data']['tab_m']:
            url2 = url1 + '&month=' + tab['m']
            api_data2 = json.loads(get_url(url2))
            # print(api_data2)
            if api_data2['code'] == 200 and api_data2['data']:
                for item in api_data2['data']['list']:
                    if item['isnew'] == '2':
                        continue
                    info = {
                        "no": item['t2'] + ' ' + item['t1'],
                        "subtitle": item['t3'],
                        "url": 'https://www.mgtv.com' + item['url']
                    }
                    # print(info)
                    data["data"].append(info)
        return data
