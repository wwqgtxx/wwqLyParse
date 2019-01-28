#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>
import typing


def green_target(target_name, target_module, raw_module):
    if isinstance(target_name, str):
        target = getattr(target_module, target_name)
        if hasattr(raw_module, target_name):
            new_target = getattr(raw_module, target_name)
            if isinstance(target, type) and not issubclass(target, BaseException):
                new_target = type(target_name, (target, new_target), {})
                new_target.__module__ = target.__module__
                new_target.__doc__ = target.__doc__
            setattr(target_module, target_name, new_target)
    elif isinstance(target_name, typing.Iterable):
        for item in target_name:
            green_target(item, target_module, raw_module)
    else:
        raise ValueError
