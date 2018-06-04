#!/usr/bin/env python  
# _*_ coding:utf-8 _*_

import json
import argparse
import ConfigParser
import requests
import scapy.all as scapy
import logging
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

# Configure Logger
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)
fileHandler = logging.FileHandler("argusscan.log")
fileHandler.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
streamHandler.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] #%(levelname)s# %(message)s')
fileHandler.setFormatter(formatter)
streamHandler.setFormatter(formatter)
logger.addHandler(fileHandler)
logger.addHandler(streamHandler)

try:
    from scapy_http import http
except ImportError:
    from scapy.layers import http


def extract_forward(packet):
    """
    提取数据包参数并转发到Master

    :param packet: 数据包

    """

    # 跳过非HTTP-Request包
    if not packet.haslayer(http.HTTPRequest):
        return

    http_request = packet["TCP"].payload

    # 跳过DOMAIN在黑名单或不在白名单内的请求
    request_host = http_request.Host
    request_path = http_request.Path

    # logger.debug("Get packet")

    # 黑白名单检测
    if white_domain:
        flag = True
        for domain in white_domain:
            if domain in request_host:
                flag = False
        if flag:
            logger.debug(u"[White List] Ignore %s: http://%s%s" % (http_request.Method, request_host, request_path))
            return
    elif black_domain:
        for domain in black_domain:
            if domain in request_host:
                logger.debug(u"[Black List] Ignore %s: http://%s%s" % (http_request.Method, request_host, request_path))
                return

    for ext in black_ext:
        if http_request.Path.endswith(".{ext}".format(ext=ext)):
            logger.debug(u"[Black Ext] Ignore %s: http://%s%s" % (http_request.Method, request_host, request_path))
            return

    try:
        if http_request.getfieldval("User-Agent").find("ArgusScan") != -1 \
                or http_request.getfieldval("User-Agent").find("sqlmap") != -1:
            return
        new_task = {"host": request_host,
                    "method": http_request.Method,
                    "path": request_path,
                    "user_agent": http_request.getfieldval("User-Agent"),
                    "cookie": http_request.Cookie,
                    "data": http_request["Raw"].load if http_request.Method == "POST" else None}

        server_resp = requests.post("http://{host}:{port}/api/task/add".format(host=master_host, port=master_port),
                                    data=json.dumps(new_task, "utf-8")).text
        resp = json.loads(server_resp)
        # 响应结果
        if resp["status"] == "success":
            logger.info(u"[New Task] %s: http://%s%s" % (http_request.Method, request_host, request_path))
    except UnicodeDecodeError:
        pass
    except IndexError:
        pass
    except ValueError or requests.exceptions.ConnectionError:
        logger.warning(u'Failed to connect Master-Server,Please confirm the Master-Server is online')


def sniff_http_packet():
    """
    调用scapy嗅探本地HTTP包
    """
    scapy.sniff(filter="tcp", prn=lambda p: extract_forward(p),
                lfilter=lambda x: x.haslayer(http.HTTPRequest))


def load_config(config_file):
    """
    加载配置文件
    :param config_file: 配置文件路径
    """
    cf = ConfigParser.ConfigParser()
    cf.read(config_file)

    global master_host, master_port, white_domain, black_domain, black_ext
    master_host = cf.get("Master", "host")
    master_port = cf.get("Master", "port")
    white_domain = cf.get("Sniffer", "white_list_domain").lower().split(",") if cf.has_option("Sniffer",
                                                                                              "white_list_domain") else None
    if white_domain:
        logger.info("[White List] {white_list}".format(white_list='|'.join(white_domain)))
    black_domain = cf.get("Sniffer", "black_list_domain").lower().split(",") if cf.has_option("Sniffer",
                                                                                              "black_list_domain") else None
    black_ext = cf.get("Sniffer", "black_list_ext").lower().split(",")


if __name__ == "__main__":
    logger.info(u"ArgusScan Client is running.")

    parser = argparse.ArgumentParser(description=u"ArgusScan Client")
    parser.add_argument("--config_file", "-c", default="setting.ini", help=u"Specify config file")
    args = parser.parse_args()
    load_config(args.config_file)

    sniff_http_packet()
