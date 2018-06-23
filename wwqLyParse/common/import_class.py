#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>

import os
import importlib
import inspect
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
_place_hold = object()


def import_by_class_name(class_names, prefix="", super_class=object, showinfo=True):
    lib_class_map = {}
    for class_name in class_names:
        if "." in class_name:
            full_name = prefix + class_name
            list_lib_name = class_name.split(".")
            class_name = list_lib_name[-1]
            module_name = prefix
            module_name += "".join(list_lib_name[0:-1])
            lib_class = imported_module_map.get(full_name, _place_hold)
            if lib_class is not _place_hold:
                lib_class_map[class_name] = imported_class_map[full_name]
            else:
                try:
                    lib_module = importlib.import_module(module_name)
                    lib_class = getattr(lib_module, class_name)
                    if inspect.isclass(lib_class) \
                            and issubclass(lib_class, super_class) \
                            and lib_class is not super_class:
                        imported_class_map[full_name] = lib_class
                        lib_class_map[class_name] = lib_class
                        if showinfo:
                            logging.debug(
                                "successful load %s is a subclass of %s" % (lib_class, super_class))
                    else:
                        logging.warning("%s is not a subclass of %s" % (lib_class, super_class))
                except:
                    logging.exception("load %s fail" % class_name)
        else:
            for k, v in imported_class_map.items():
                if k.startswith(prefix) and class_name == k.split('.')[-1] and issubclass(v, super_class):
                    logging.debug("successful load %s from imported_class_map" % v)
                    lib_class_map[k] = v
                    break
    return lib_class_map


def import_by_module_name(module_names=None, prefix="", super_class=object, showinfo=True):
    lib_class_map = {}
    for module_name in module_names:
        module_name = prefix + module_name
        imported_module_map_key = (module_name, super_class)
        imported_module = imported_module_map.get(imported_module_map_key, _place_hold)
        if imported_module is not _place_hold:
            for item in imported_module:
                lib_class_map[item["lib_name"]] = item["lib_class"]
        else:
            try:
                lib_module = importlib.import_module(module_name)
                imported_module_map[imported_module_map_key] = []
                lib_module_class_names = getattr(lib_module, "__all__", _place_hold)
                from_dir = False
                if lib_module_class_names is _place_hold:
                    lib_module_class_names = dir(lib_module)
                    logging.warning("module %s don't have '__all__' try to use dir() get classes!" % lib_module)
                    from_dir = True
                for lib_module_class_name in lib_module_class_names:
                    try:
                        lib_class = getattr(lib_module, lib_module_class_name)
                        if from_dir and inspect.getmodule(lib_class) is not lib_module:
                            continue
                        if inspect.isclass(lib_class) \
                                and issubclass(lib_class, super_class) \
                                and lib_class is not super_class:
                            lib_name = lib_class.__name__
                            imported_module_map[imported_module_map_key].append({
                                "lib_name": lib_name,
                                "lib_class": lib_class
                            })
                            imported_class_map[module_name + "." + lib_name] = lib_class
                            lib_class_map[lib_name] = lib_class
                            if showinfo:
                                logging.debug(
                                    "successful load " + str(lib_class) + " is a subclass of " + str(super_class))
                        else:
                            if not from_dir:
                                logging.warning(str(lib_class) + " is not a subclass of " + str(super_class))
                    except KeyError:
                        logging.warning("%s not in %s" % (lib_module_class_name, lib_module))
                    except:
                        logging.exception("load %s fail" % lib_module_class_name)
            except:
                logging.exception("load %s fail" % module_name)
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
