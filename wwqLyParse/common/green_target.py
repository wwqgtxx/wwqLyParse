#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


def green_target(target_name, target_module, raw_module):
    target = getattr(target_module, target_name)
    if hasattr(raw_module, target_name):
        new_target = getattr(raw_module, target_name)
        if type(target) is type:
            new_target = type(target_name, (target, new_target), {})
            new_target.__module__ = target.__module__
            new_target.__doc__ = target.__doc__
        setattr(target_module, target_name, new_target)
