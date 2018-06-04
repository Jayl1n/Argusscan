#!/usr/bin/env python 
# coding: utf-8

import argparse
import ConfigParser
from web.app import http_run

VERSION = "0.1"

logo = """
         ____ _   _____   ____ _  __  __   _____
        / __ `/  / ___/  / __ `/ / / / /  / ___/
       / /_/ /  / /     / /_/ / / /_/ /  (__  ) 
       \__,_/  /_/      \__, /  \__,_/  /____/  
                       /____/                   Ver %s
                                             By Jaylin
""" % VERSION


def load_config(config_file):
    """
    加载配置文件
    :param config_file:
    """
    cf = ConfigParser.ConfigParser()
    cf.read(config_file)

    global host, port
    host = cf.get("Master", "host")
    port = cf.getint("Master", "port")


if __name__ == '__main__':
    print logo

    parser = argparse.ArgumentParser(description=u"ArgusScan 主服务器端")
    parser.add_argument("--config_file", "-c", default="setting.ini", help=u"指定配置文件")
    args = parser.parse_args()
    load_config(args.config_file)

    http_run(host, port)