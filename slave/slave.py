# coding=utf-8

import contextlib
import logging
import os
import socket
import json
import tempfile
import ConfigParser
import argparse
import urllib2

from lib.core.common import getSafeExString, setPaths
from lib.core.data import logger
from lib.core.enums import MKSTEMP_PREFIX
from lib.core.settings import RESTAPI_DEFAULT_ADDRESS, RESTAPI_DEFAULT_PORT, RESTAPI_DEFAULT_ADAPTER
from lib.utils.api import DataStore, Database
from sqlmap import modulePath
from thirdparty.bottle.bottle import run, server_names


# 启动Slave节点
def start_slave_node(host=RESTAPI_DEFAULT_ADDRESS,
                     port=RESTAPI_DEFAULT_PORT,
                     adapter=RESTAPI_DEFAULT_ADAPTER,
                     username=None,
                     password=None):
    """
    REST-JSON API 服务器
    """

    DataStore.admin_id = token
    DataStore.username = username
    DataStore.password = password

    _, Database.filepath = tempfile.mkstemp(prefix=MKSTEMP_PREFIX.IPC, text=False)
    os.close(_)

    logger.setLevel(logging.DEBUG)

    if port == 0:  # random
        with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            s.bind((host, 0))
            port = s.getsockname()[1]

    logger.info("Admin ID: %s" % DataStore.admin_id)

    # 初始化IPC数据库
    DataStore.current_db = Database()
    DataStore.current_db.connect()
    DataStore.current_db.init()

    # 启动 RESTful API
    try:
        if adapter == "gevent":
            from gevent import monkey
            monkey.patch_all()
        elif adapter == "eventlet":
            import eventlet
            eventlet.monkey_patch()
        logger.debug("Using adapter '%s' to run bottle" % adapter)

        # Connect to Master-Server
        master_url = "http://{host}:{port}/api/slave/connect".format(host=master_host,
                                                                     port=master_port)
        request = urllib2.Request(master_url, headers={"Content-Type": "application/json"})
        data = json.dumps({"port": port, "admin_id": token})
        try:
            response = json.loads(urllib2.urlopen(request, data=data).read())
            if response["status"] != "fail":
                logger.info("Connect to Master-Server successfully")
            else:
                logger.error("Connect to Master-Server failed")
                exit(-1)
        except urllib2.URLError:
            logger.error("Failed to connect Master-Server,Please confirm the Master-Server is online")
            exit(-1)

        run(host=host, port=port, quiet=True, debug=True, server=adapter)
    except socket.error, ex:
        if "already in use" in getSafeExString(ex):
            logger.error("Address already in use ('%s:%s')" % (host, port))
        else:
            raise
    except ImportError:
        if adapter.lower() not in server_names:
            errMsg = "Adapter '%s' is unknown. " % adapter
            errMsg += "(Note: available adapters '%s')" % ', '.join(sorted(server_names.keys()))
        else:
            errMsg = "Server support for adapter '%s' is not installed on this system " % adapter
            errMsg += "(Note: you can try to install it with 'sudo apt-get install python-%s' or 'sudo pip install %s')" % (
                adapter, adapter)
        logger.critical(errMsg)


def load_config(config_file):
    """
    加载配置文件
    :param config_file: 配置文件路径
    """
    cf = ConfigParser.ConfigParser()
    cf.read(config_file)

    global master_host, master_port, token, slave_port
    master_host = cf.get("Master", "host")
    master_port = cf.get("Master", "port")
    token = cf.get("Slave", "token") if cf.has_option("Slave", "token") else 'xxxxxxxx'
    slave_port = cf.get("Slave", "port") if cf.has_option("Slave", "port") else '23333'


if __name__ == '__main__':
    # 初始化路径
    setPaths(modulePath())

    parser = argparse.ArgumentParser(description=u"ArgusScan Slave")
    parser.add_argument("--config_file", "-c", default="setting.ini", help=u"Specify config file")
    parser.add_argument("--port", "-p", help=u"Specify port to listen")
    args = parser.parse_args()
    load_config(args.config_file)
    slave_port = args.port if args.port is not None else slave_port
    logger.info(u"ArgusScan Slave is running.")

    # 启动节点
    start_slave_node(port=slave_port)
