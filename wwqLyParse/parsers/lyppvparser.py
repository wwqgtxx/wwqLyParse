#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib.request,io,os,sys,json,re,math,subprocess,traceback


try:
    from .. import common
except Exception as e:
    import common
    


class LypPvParser(common.Parser):
    try:
        try:
            from ..lyp_pv import run
        except Exception as e:
            from lyp_pv import run
        filters = run.GetVersion()['filter'] 
    except Exception as e:
        filters = []

    # parse functions
    def Parse(self,url,types=None):
        if (types is not None) and ("formats" not in types):
            return
        if ('www.iqiyi.com' in url):
            return []
        try:
            from ..lyp_pv import run
        except Exception as e:
            from lyp_pv import run
        if re.search('www.iqiyi.com/(lib/m|a_)',url):
            return []
        print("call lyp_pv.run.Parse("+url+")")
        out = run.Parse(url)
        if "data" in out:
            for data in out['data']:
                data['label'] = re.compile('\(\d\)\s*').sub('',str(data['label']))
                parts = data['label'].split('_')
                num = int(parts[0])
                if num == -3:
                    parts[0] = "0"
                elif num == -1:
                    parts[0] = "1"
                elif num == 0:
                    parts[0] = "2"
                elif num == 2:
                    parts[0] = "3"
                elif num == 4:
                    parts[0] = "4"
                elif num == 7:
                    parts[0] = "5"
                data['label']=('_').join(parts)
                data['label'] = data['label'] + ("@lyppv")
            out["caption"]= "负锐解析"
            out.pop("icon")
            out.pop("warning")
        return out

    def ParseURL(self,url,label,min=None,max=None):
        assert "@lyppv" in label
        try:
            from ..lyp_pv import run
        except Exception as e:
            from lyp_pv import run
        parts = label.split('_')
        num = int(parts[0])
        if num == 0:
            parts[0] = "-3"
        elif num == 1:
            parts[0] = "-1"
        elif num == 0:
            parts[0] = "0"
        elif num == 3:
            parts[0] = "2"
        elif num == 4:
            parts[0] = "4"
        elif num == 5:
            parts[0] = "7"
        label=('_').join(parts)
        label = "() "+label
        print("call lyp_pv.run.ParseURL("+url+","+label+","+str(min)+","+str(max)+")")
        result = run.ParseURL(url,label,min,max)
        if "iqiyi" in url:
            for item in result:
                item["unfixIp"] = True
        return result
        
    def getLypPvVersion(self):
        try:
            try:
                from ..lyp_pv import run
            except Exception as e:
                from lyp_pv import run
            print("call lyp_pv.run._lyyc_about()")
            info = run._lyyc_about()
            return "负锐解析["+str(info['pack_version'])+"]"+str(info['version'])
        except Exception as e:
            #print(e)
            import traceback  
            traceback.print_exc()  
        return ""



