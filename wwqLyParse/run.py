#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>

try:
    from . import listparse
except Exception as e:
    import listparse



def GetVersion():
    return listparse.GetVersion()
    
def Parse(input_text):
    return listparse.Parse(input_text)


#print (GetVersion())
#print (Parse('http://www.iqiyi.com/lib/m_209445514.html?src=search'))
#print (Parse('http://www.iqiyi.com/a_19rrhacdwt.html'))

