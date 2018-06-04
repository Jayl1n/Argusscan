#!/usr/bin/env python  
# _*_ coding:utf-8 _*_
from flask import *

from model import Slave
from util import dejsonize
from master import master
import logging

# Configure Logger
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)
fileHandler = logging.FileHandler("argusscan.log")
fileHandler.setLevel(logging.INFO)
streamHandler = logging.StreamHandler()
streamHandler.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] #%(levelname)s# %(message)s')
fileHandler.setFormatter(formatter)
streamHandler.setFormatter(formatter)
logger.addHandler(fileHandler)
logger.addHandler(streamHandler)

argus = Flask(__name__)


@argus.route("/api/slave/connect", methods=["POST"])
def api_slave_connect():
    """
    添加节点
    """
    port, admin_id = dejsonize(request.data)["port"], dejsonize(request.data)["admin_id"]
    addr = request.remote_addr
    slave = Slave(admin_id=admin_id, address=addr, port=port)
    if "{}:{}".format(addr, port) not in master.slaves:
        if master.add_slave(slave):
            logger.info(
                "{addr}:{port}:{admin_id} try to connect successfully".format(addr=request.remote_addr, port=port,
                                                                              admin_id=admin_id))
            return jsonify({"status": "success"})
        else:
            logger.info("{addr}:{port}:{admin_id} try to connect failed".format(addr=request.remote_addr, port=port,
                                                                                admin_id=admin_id))
    else:
        return jsonify({"status": "exist"})


@argus.route("/api/task/add", methods=["POST"])
def api_task_add():
    """
    添加任务
    """
    if master.add_task(request.data):
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "fail"})


@argus.route("/api/task/remove/<task_id>")
def api_task_remove(task_id):
    """
    删除任务
    """
    master.remove_task(task_id)
    return jsonify({"status": "success"})


@argus.route("/api/status")
def api_system_status():
    """
    系统状态
    """
    return jsonify(master.sys_status())


@argus.route("/api/charts")
def api_charts_data():
    """
    图表数据
    """
    return jsonify(master.charts_data())


@argus.route("/api/result", methods=["POST"])
def api_result_data():
    """
    扫描结果数据
    """
    start = 0
    length = 0
    sEcho = 0
    aoData = dejsonize(request.form["aoData"])
    for k in aoData:
        if k["name"] == "iDisplayStart":
            start = k["value"]
        if k["name"] == "iDisplayLength":
            length = k["value"]
        if k["name"] == "sEcho":
            sEcho = k["value"]

    aData, total = master.result_data(start, length)

    return jsonify({"sEcho": sEcho + 1,
                    "iTotalRecords": length,
                    "iTotalDisplayRecords": total,
                    "aData": aData})


@argus.route("/api/detail/<task_id>")
def api_get_detail_by_id(task_id):
    """
    根据`task_id`查看任务详情
    """
    return jsonify(master.get_task_detail(task_id))


@argus.route("/api/conf/slave/<slave_id>/enable")
def api_conf_slave_enable(slave_id):
    """
    启用节点
    """
    if master.disable_slave(slave_id):
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "fail"})


@argus.route("/api/conf/slave/<slave_id>/disable")
def api_conf_slave_disable(slave_id):
    """
    停用节点
    """
    if master.enable_slave(slave_id):
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "fail"})


@argus.route("/")
def index():
    """
    首页
    """
    return redirect(url_for("index_page"))


@argus.route("/index")
def index_page():
    return render_template("index.html",
                           notification=[])


@argus.route("/result")
def result_page():
    return render_template("result.html")


@argus.route("/config")
def config_page():
    return render_template("config.html")


def http_run(listen_host="0.0.0.0", listen_port=80):
    """
    启动WEB服务
    """
    argus.run(host=listen_host, port=listen_port, debug=True, use_reloader=False)
