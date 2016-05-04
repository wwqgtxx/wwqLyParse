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
        try:
            from ..lyp_pv import run
        except Exception as e:
            from lyp_pv import run
        if (types is not None) and ("formats" not in types):
            return
        print("call lyp_pv.run.Parse("+url+")")
        out = run.Parse(url)
        for data in out['data']:
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
        print("call lyp_pv.run.ParseURL("+url+","+label+","+str(min)+","+str(max)+")")
        return run.ParseURL(url,label,min,max)
        
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



