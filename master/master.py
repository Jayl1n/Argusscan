#!/usr/bin/env python  
# _*_ coding:utf-8 _*_
import sqlite3
import threading
import time
from Queue import Queue
from util import dejsonize, jsonize, logger
from model import Slave, Task


class Master(object):

    def __init__(self):
        self.slaves = {}
        self.db = self.__init_db("argus_cache.db")
        self.task_queue = Queue()

        for task in self.get_undo_tasks():
            self.task_queue.put(task)

        t_add_task = threading.Thread(target=self.run)
        t_add_task.start()

        t_update_task = threading.Thread(target=self.update_task_status)
        t_update_task.start()

    def add_slave(self, slave):
        k = "{address}:{port}".format(address=slave.address, port=slave.port)
        if k not in self.slaves:
            self.slaves[k] = slave
            c = self.db.cursor()
            try:
                c.execute("INSERT INTO slave(full_address,admin_id,create_datetime,enable) "
                          "VALUES(?,?,DATETIME('now','localtime'),1)",
                          ("{}:{}".format(slave.address, slave.port), slave.admin_id,))
                self.db.commit()
                return True
            except self.db.IntegrityError:
                return True
            except self.db.Error:
                pass
        return False

    def disable_slave(self, slave):
        if self.slaves[slave.admin_id] == slave:
            slave.enable = False
            return True
        return False

    def add_task(self, task):
        c = self.db.cursor()
        try:
            c.execute("INSERT INTO task(options,create_time,valid) VALUES(?,DATETIME('now','localtime'),1)", (task,))
            self.task_queue.put({"id": c.lastrowid, "options": Task(**dejsonize(task))})
            self.db.commit()
            return True
        except self.db.Error:
            logger.error("Database Error")
            return False

    def remove_task(self, task_id):
        self.db.execute("DELETE FROM task WHERE id = ?", (task_id,))
        self.db.commit()
        return True

    def get_slaves(self):
        slaves = []
        for slave in self.db.execute("SELECT id,full_address, admin_id FROM slave WHERE enable = 1"):
            id = slave[0]
            addr = slave[1].split(":")[0]
            port = slave[1].split(":")[1]
            admin_id = slave[2]
            slaves.append({"id": id, "slave": Slave(address=addr, port=port, admin_id=admin_id)})
        return slaves

    def get_free_slave(self):
        s = self.db.execute("SELECT slave.id, slave.full_address, slave.admin_id, "
                            "(SELECT COUNT(*) FROM task WHERE slave_id = slave.id AND done_time IS NULL) AS total "
                            "FROM slave "
                            "ORDER BY total "
                            "LIMIT 1 ").fetchone()
        return {"id": s[0], "slave": Slave(full_address=s[1], admin_id=s[2])}

    def get_undo_tasks(self):
        tasks = []
        for task in self.db.execute("SELECT id, options FROM task "
                                    "WHERE task_id IS NULL AND done_time IS NULL AND valid = 1"):
            tasks.append({"id": task[0], "options": Task(**dejsonize(task[1]))})
        return tasks

    def sys_status(self):
        """
        Get the runtime status from database
        """
        status = self.db.execute("SELECT slave_total, task_total, task_undo_total, bug_total, progress_percent "
                                 "FROM SYS_STATUS_VIEW").fetchone()
        return {"slave_total": status[0],
                "task_total": status[1],
                "task_undo_total": status[2],
                "bug_total": status[3],
                "progress_percent": round(status[4] * 100, 2)}

    def charts_data(self):
        """
        Get charts data
        """
        c = self.db.cursor()
        data = c.execute("""SELECT
  (SELECT COUNT(id)
   FROM task
   WHERE create_time > datetime('now', 'localtime', '-6 hour'))      AS new_task_now,
  (SELECT COUNT(id)
   FROM task
   WHERE create_time > datetime('now', 'localtime', '-12 hour')
         AND create_time < datetime('now', 'localtime', '-6 hour'))  AS new_task_before_12h,
  (SELECT COUNT(id)
   FROM task
   WHERE create_time > datetime('now', 'localtime', '-18 hour')
         AND create_time < datetime('now', 'localtime', '-12 hour')) AS new_task_before_18h,
  (SELECT COUNT(id)
   FROM task
   WHERE create_time > datetime('now', 'localtime', '-24 hour')
         AND create_time < datetime('now', 'localtime', '-18 hour')) AS new_task_before_24h,
  (SELECT COUNT(id)
   FROM task
   WHERE create_time > datetime('now', 'localtime', '-30 hour')
         AND create_time < datetime('now', 'localtime', '-24 hour')) AS new_task_before_30h,
  (SELECT COUNT(id)
   FROM task
   WHERE create_time > datetime('now', 'localtime', '-36 hour')
         AND create_time < datetime('now', 'localtime', '-30 hour')) AS new_task_before_36h,
  (SELECT COUNT(id)
   FROM task
   WHERE create_time > datetime('now', 'localtime', '-42 hour')
         AND create_time < datetime('now', 'localtime', '-36 hour')) AS new_task_before_42h,
  (SELECT COUNT(id)
   FROM task
   WHERE create_time > datetime('now', 'localtime', '-6 hour')
         AND done_time NOT NULL)                                     AS done_task_now,
  (SELECT COUNT(id)
   FROM task
   WHERE create_time > datetime('now', 'localtime', '-12 hour')
         AND create_time < datetime('now', 'localtime', '-6 hour')
         AND done_time NOT NULL)                                     AS done_task_before_12h,
  (SELECT COUNT(id)
   FROM task
   WHERE create_time > datetime('now', 'localtime', '-18 hour')
         AND create_time < datetime('now', 'localtime', '-12 hour')
         AND done_time NOT NULL)                                     AS done_task_before_18h,
  (SELECT COUNT(id)
   FROM task
   WHERE create_time > datetime('now', 'localtime', '-24 hour')
         AND create_time < datetime('now', 'localtime', '-18 hour')
         AND done_time NOT NULL)                                     AS done_task_before_24h,
  (SELECT COUNT(id)
   FROM task
   WHERE create_time > datetime('now', 'localtime', '-30 hour')
         AND create_time < datetime('now', 'localtime', '-24 hour')
         AND done_time NOT NULL)                                     AS done_task_before_30h,
  (SELECT COUNT(id)
   FROM task
   WHERE create_time > datetime('now', 'localtime', '-36 hour')
         AND create_time < datetime('now', 'localtime', '-30 hour')
         AND done_time NOT NULL)                                     AS done_task_before_36h,
  (SELECT COUNT(id)
   FROM task
   WHERE create_time > datetime('now', 'localtime', '-42 hour')
         AND create_time < datetime('now', 'localtime', '-36 hour')
         AND done_time NOT NULL)                                     AS done_task_before_42h,
  (SELECT COUNT(id)
   FROM task
   WHERE create_time > datetime('now', 'localtime', '-6 hour')
         AND vulnerable = 1)                                         AS bug_now,
  (SELECT COUNT(id)
   FROM task
   WHERE create_time > datetime('now', 'localtime', '-12 hour')
         AND create_time < datetime('now', 'localtime', '-6 hour')
         AND vulnerable = 1)                                         AS bug_before_12h,
  (SELECT COUNT(id)
   FROM task
   WHERE create_time > datetime('now', 'localtime', '-18 hour')
         AND create_time < datetime('now', 'localtime', '-12 hour')
         AND vulnerable = 1)                                         AS bug_before_18h,
  (SELECT COUNT(id)
   FROM task
   WHERE create_time > datetime('now', 'localtime', '-24 hour')
         AND create_time < datetime('now', 'localtime', '-18 hour')
         AND vulnerable = 1)                                         AS bug_before_24h,
  (SELECT COUNT(id)
   FROM task
   WHERE create_time > datetime('now', 'localtime', '-30 hour')
         AND create_time < datetime('now', 'localtime', '-24 hour')
         AND vulnerable = 1)                                         AS bug_before_30h,
  (SELECT COUNT(id)
   FROM task
   WHERE create_time > datetime('now', 'localtime', '-36 hour')
         AND create_time < datetime('now', 'localtime', '-30 hour')
         AND vulnerable = 1)                                         AS bug_before_36h,
  (SELECT COUNT(id)
   FROM task
   WHERE create_time > datetime('now', 'localtime', '-42 hour')
         AND create_time < datetime('now', 'localtime', '-36 hour')
         AND vulnerable = 1)                                         AS bug_before_42h""").fetchone()
        col_name = [t[0] for t in c.description]
        return dict(zip(col_name, data))

    def result_data(self, start, offset):
        """
        Get task result
        """
        task_info = self.db.execute("SELECT id, options, vulnerable, done_time "
                                    "FROM task "
                                    "ORDER BY vulnerable DESC,done_time DESC "
                                    "LIMIT ?,?", (start, offset,)).fetchall()
        task_total = self.db.execute("SELECT COUNT(id) "
                                     "FROM task").fetchone()
        result = []
        for info in task_info:
            option = dejsonize(info[1])
            result.append({"id": info[0],
                           "host": option["host"],
                           "method": option["method"],
                           "option": info[1],
                           "vulnerable": u'否' if info[2] == 0 else '是',
                           "done_time": info[3]})
        return result, task_total[0]

    def get_task_detail(self, task_id):
        """
        Get task detail by task id
        """
        task_info = self.db.execute("SELECT id,slave_id,options,done_time,vulnerable,result "
                                    "FROM task WHERE id= ?", (task_id,)).fetchone()
        options = dejsonize(task_info[2])

        return {"id": task_info[0],
                "slave_id": task_info[1],
                "method": options["method"],
                "host": options["host"],
                "path": options["path"],
                "done_time": task_info[3],
                "cookie": options["cookie"] if options["cookie"] is not None else u'无',
                "data": options["data"] if options["data"] is not None else u'无',
                "vulnerable": u'否' if task_info[4] == 0 else u'是',
                "result": task_info[5] if task_info[4] == 1 else None}

    def run(self):
        while True:
            slaves = self.get_slaves()
            if self.task_queue.empty():
                pass
            elif len(slaves) < 1:
                logger.info(u"No slave could be used.")
            else:
                s = self.get_free_slave()
                s_id = s["id"]
                slave = s["slave"]
                try:
                    taskid = slave.new_task()
                    logger.info(u"New taskid {}".format(taskid))

                    # 获取任务参数
                    task = self.task_queue.get()
                    t_id = task["id"]
                    task_options = task["options"]

                    if slave.start_task(taskid, task_options):
                        logger.info(u"Delegate new tasks to {}".format(slave.full_address))
                        # Update task info
                        self.db.execute("UPDATE task SET task_id = ?,slave_id =?  WHERE id = ?",
                                        (taskid, s_id, t_id,))
                        self.db.commit()
                except Exception:
                    pass
            time.sleep(5)

    def update_task_status(self):
        while True:
            tasks = self.db.execute(
                "SELECT full_address,admin_id,task_id,id,options FROM TASK_STATUS_VIEW WHERE task_id NOT NULL "
                "AND done_time IS NULL")
            for task in tasks:
                s = Slave(full_address=task[0], admin_id=task[1])
                if s.get_task_status(task[2]) == "terminated":
                    data = s.get_task_data(task[2])
                    logger.info("Task[{}] terminated".format(task[2]))
                    if len(data) != 0:
                        logger.info("Task[{}] find new sql vulnerable.".format(task[2]))
                        self.db.execute(
                            "UPDATE task SET done_time = DATETIME('now','localtime') , result = ? , vulnerable = 1 "
                            "WHERE task_id = ?", (jsonize(data), task[2]))
                    else:
                        self.db.execute(
                            "UPDATE task SET done_time = DATETIME('now','localtime') , result = ? , vulnerable = 0 "
                            "WHERE task_id = ?", (jsonize(data), task[2]))
                    self.db.commit()
                elif s.get_task_status(task[2]) == ("unreachable" or "Invalid task ID"):
                    self.db.execute("UPDATE task SET task_id = NULL, slave_id=NULL WHERE task_id = ?", (task[2],))
                    self.db.commit()
                    self.task_queue.put({"id": task[3], "options": task[4]})
            time.sleep(10)

    @staticmethod
    def __init_db(db_name):
        conn = sqlite3.connect(db_name, check_same_thread=False)
        return conn


master = Master()
