#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib.request, io, os, sys, json, re

from pyquery.pyquery import PyQuery
import base64
import uuid

try:
    from ..common import *
except Exception as e:
    from common import *

JUDGE_VIP = True

__all__ = ["MgTVParser", "MgTVParser2", "MgTVListParser"]


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
    name = "芒果TV解析"

    def get_vid(self, url):
        # id = re.match('^http://[^\s]+/[^\s]+/([^\s]+)\.html', url).group(1)

        vid = match1(url, r'https?://www.mgtv.com/(?:b|l)/\d+/(\d+).html')
        if not vid:
            vid = match1(url, r'https?://www.mgtv.com/hz/bdpz/\d+/(\d+).html')

        return vid

    def get_tk2(self, did, clit):
        return encode_tk2("did={}|pno=1030|ver=5.5.1|{}".format(did, clit))

    def get_api_url1(self, vid, tk2):
        return 'https://pcweb.api.mgtv.com/player/video?video_id={}&tk2={}'.format(vid, tk2)

    def get_api_url2(self, vid, tk2, clit, pm2):
        return 'https://pcweb.api.mgtv.com/player/getSource?video_id={}&tk2={}&pm2={}'.format(vid, encode_tk2(clit),
                                                                                              pm2)

    def get_api_url3(self, domain, url, did):
        return '{}{}'.format(domain, url)

    async def get_api_data(self, url, cookie_jar=None, only_api1=False):
        vid = self.get_vid(url)
        clit = "clit=%d" % int(time.time())
        did = str(uuid.uuid4())
        tk2 = self.get_tk2(did, clit)
        api_url = self.get_api_url1(vid, tk2)
        api_data1 = await get_url_service.get_url_async(api_url, allow_cache=False, cookie_jar=cookie_jar)
        api_data1 = json.loads(api_data1)
        logging.debug(api_data1)
        assert api_data1['code'] == 200
        api_data = api_data1['data']
        api_data['did'] = did
        if not only_api1:
            pm2 = api_data['atc']['pm2']
            api_url2 = self.get_api_url2(vid, tk2, clit, pm2)
            api_data2 = await get_url_service.get_url_async(api_url2, allow_cache=False, cookie_jar=cookie_jar)
            api_data2 = json.loads(api_data2)
            logging.debug(api_data2)
            assert api_data2['code'] == 200
            api_data.update(api_data2['data'])
        logging.debug(api_data)
        return api_data

    async def parse(self, input_text, types=None, *k, **kk):
        data = {
            "type": "formats",
            "name": "",
            "icon": "http://xxx.cn/xxx.jpg",
            "provider": "芒果TV",
            "caption": self.name,
            # "warning" : "提示信息",
            "sorted": 1,
            "data": []
        }
        cookie_jar = get_url_service.new_cookie_jar()
        api_data = await self.get_api_data(input_text, cookie_jar)
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

    async def parse_url(self, input_text, label, min=None, max=None, *k, **kk):
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
        cookie_jar = get_url_service.new_cookie_jar()
        api_data = await self.get_api_data(input_text, cookie_jar)
        did = api_data['did']
        # domain = api_data['data']['stream_domain'][0]
        headers = get_url_service.new_headers_from_fake({"Referer": input_text})
        for lstream in api_data['stream']:
            if lstream['url'] and lstream['def'] == label:
                for domain in api_data['stream_domain']:
                    api_data3_url = self.get_api_url3(domain, lstream['url'], did)
                    api_data3_url = api_data3_url.replace("http://", "https://")
                    api_data3 = await get_url_service.get_url_async(api_data3_url, headers=headers, allow_cache=False, cookie_jar=cookie_jar)
                    # print(api_data3)
                    api_data3 = json.loads(api_data3)
                    # print(api_data3)
                    url = api_data3['info']
                    url = url.replace("https://", "http://")
                    data["urls"].append(url)
                    break
        logging.debug(list(cookie_jar))
        return [data]


class MgTVParser2(MgTVParser):
    name = "芒果TV解析-PCH5"

    def get_tk2(self, did, clit):
        return encode_tk2("did={}|pno=1030|ver=0.3.0301|{}".format(did, clit))

    def get_api_url1(self, vid, tk2):
        return 'https://pcweb.api.mgtv.com/player/video?video_id={}&tk2={}&type=pch5'.format(vid, tk2)

    def get_api_url2(self, vid, tk2, clit, pm2):
        return 'https://pcweb.api.mgtv.com/player/getSource?video_id={}&tk2={}&pm2={}&type=pch5'.format(vid, tk2, pm2)

    def get_api_url3(self, domain, url, did):
        return '{}{}&did={}'.format(domain, url, did)


class MgTVListParser(MgTVParser):
    filters = MgTVParser.filters + [r'https?://www.mgtv.com/h/(\d+).html']
    types = ["collection"]

    async def parse(self, input_text, *k, **kk):
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
            api_data = await self.get_api_data(input_text, only_api1=True)
            info = api_data['info']
            collection_id = info['collection_id']
        url1 = 'https://pcweb.api.mgtv.com/variety/showlist?collection_id=' + collection_id
        api_data1 = json.loads(await get_url_service.get_url_async(url1))
        # print(api_data1)
        if api_data1['code'] != 200 and not api_data1['data']:
            return []
        data['title'] = api_data1['data']['info']['title']
        for tab in api_data1['data']['tab_m']:
            url2 = url1 + '&month=' + tab['m']
            api_data2 = json.loads(await get_url_service.get_url_async(url2))
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
