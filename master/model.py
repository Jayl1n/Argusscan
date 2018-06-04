#!/usr/bin/env python  
# _*_ coding:utf-8 _*_

from requests import get, post, ConnectionError
from util import jsonize, dejsonize, logger, to_sqlmap_option


class Slave(object):
    """
    model Slave节点
    """

    def __init__(self, admin_id, address=None, port=None, full_address=None):
        """
        Init Slave object
        """
        self.address = address
        self.port = port
        self.admin_id = admin_id
        self.enable = True
        self.full_address = address + ":" + str(port) if full_address is None else full_address

    def new_task(self):
        resp = get("http://{}/task/new".format(self.full_address)).json()
        if not resp["success"]:
            return ""
        return resp["taskid"]

    def start_task(self, taskid, task):
        resp = post(url="http://{}/scan/{}/start".format(self.full_address, taskid),
                    json=to_sqlmap_option(task)).json()
        if not resp["success"]:
            return False
        return True

    def get_task_status(self, taskid):
        try:
            resp = get(url="http://{}/scan/{}/status".format(self.full_address, taskid)).json()
            if resp["success"]:
                return resp["status"]
            else:
                return resp["message"]
        except ConnectionError:
            return "unreachable"

    def get_task_data(self, taskid):
        resp = get(url="http://{}/scan/{}/data".format(self.full_address, taskid)).json()
        return resp["data"]

    def list_task(self):
        resp = dejsonize(get(self.address + "/admin/list"))
        if resp["success"]:
            return resp["tasks"]
        return []

    def __eq__(self, other):
        if self.address != other.address \
                or self.port != other.port \
                or self.admin_id != other.admin_id:
            return False
        return True


class Task(object):
    """
    model 扫描任务
    """

    def __init__(self, host, method, path, user_agent, cookie, data):
        self.host = host
        self.method = method
        self.path = path
        self.user_agent = user_agent
        self.cookie = cookie
        self.data = data
