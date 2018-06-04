#!/usr/bin/env python  
# _*_ coding:utf-8 _*_  

import json

import logging


def jsonize(o):
    """
    Serialize Python object to json
    """
    return json.dumps(o)


def dejsonize(s):
    """
    Deserialize json to Python object
    :param s:
    """
    return json.loads(s)


def class_to_dict(obj):
    is_list = obj.__class__ == [].__class__
    is_set = obj.__class__ == set().__class__

    if is_list or is_set:
        objs = []
        for o in obj:
            d = {}
            d.update(o.__dict__)
            objs.append(d)
        return objs
    else:
        d = {}
        d.update(obj.__dict__)
        return d


def to_sqlmap_option(task):
    return {"url": task.host + task.path,
            "method": task.method,
            "cookie": task.cookie,
            "headers": "User-Agent:{} ArgusScan".format(task.user_agent),
            "data": task.data}


# Configure Logger
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)
fileHandler = logging.FileHandler("argusscan.log")
fileHandler.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
streamHandler.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s] #%(levelname)s# %(message)s')
fileHandler.setFormatter(formatter)
streamHandler.setFormatter(formatter)
logger.addHandler(fileHandler)
logger.addHandler(streamHandler)
