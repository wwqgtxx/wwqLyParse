#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>

import os
import importlib
import logging


def get_all_filename_by_dir(dir_name, suffix=".py"):
    list_dirs = os.walk(dir_name)
    file_names = []
    for dirName, subdirList, fileList in list_dirs:
        for file_name in fileList:
            if file_name[-len(suffix):] == suffix:
                if file_name != "__init__.py":
                    file_names.append(file_name[0:-len(suffix)])
    logging.debug("<%s> has %s" % (dir_name, str(file_names)))
    return file_names


imported_class_map = {}
imported_module_map = {}


def import_by_name(class_names=None, module_names=None, prefix="", super_class=object, showinfo=True):
    lib_class_map = {}
    if class_names is not None:
        lib_names = class_names
        for lib_name in lib_names:
            if "." in lib_name:
                full_name = prefix + lib_name
                list_lib_name = lib_name.split(".")
                lib_name = list_lib_name[-1]
                module_name = prefix
                module_name += "".join(list_lib_name[0:-1])
            else:
                full_name = prefix + lib_name.lower() + "." + lib_name
                module_name = prefix + lib_name.lower()
            try:
                lib_class_map[lib_name] = imported_class_map[full_name]
            except:
                try:
                    lib_module = importlib.import_module(module_name)
                    lib_class = getattr(lib_module, lib_name)
                    if isinstance(lib_class(), super_class):
                        imported_class_map[full_name] = lib_class
                        lib_class_map[lib_name] = lib_class
                        if showinfo:
                            logging.debug("successful load " + str(lib_class) + " is a instance of " + str(super_class))
                    else:
                        logging.warning(str(lib_class) + " is not a instance of " + str(super_class))
                except:
                    logging.exception("load " + str(lib_name) + " fail")
    elif module_names is not None:
        lib_names = module_names
        for lib_name in lib_names:
            try:
                for item in imported_module_map[prefix + lib_name]:
                    lib_class_map[item["lib_name"]] = item["lib_class"]
            except:
                try:
                    lib_module = importlib.import_module(prefix + lib_name)
                    lib_module_class_names = getattr(lib_module, "__MODULE_CLASS_NAMES__")
                    imported_module_map[prefix + lib_name] = []
                    for lib_module_class_name in lib_module_class_names:
                        try:
                            lib_class = getattr(lib_module, lib_module_class_name)
                            if isinstance(lib_class(), super_class):
                                imported_module_map[prefix + lib_name].append({
                                    "lib_name": lib_class.__name__,
                                    "lib_class": lib_class
                                })
                                imported_class_map[prefix + lib_name + "." + lib_class.__name__] = lib_class
                                lib_class_map[lib_class.__name__] = lib_class
                                if showinfo:
                                    logging.debug(
                                        "successful load " + str(lib_class) + " is a instance of " + str(super_class))
                            else:
                                logging.warning(str(lib_class) + " is not a instance of " + str(super_class))
                        except:
                            logging.exception("load " + str(lib_module_class_name) + " fail")
                except:
                    logging.exception("load " + str(prefix + lib_name) + " fail")
    return lib_class_map


def new_objects(class_map, showinfo=False, *k, **kk):
    _objects = []
    for _class in class_map.values():
        try:
            _object = _class(*k, **kk)
            _objects.append(_object)
            if showinfo:
                logging.debug("successful new " + str(_object))
        except:
            logging.exception("new " + str(_class) + " fail")
    return _objects
