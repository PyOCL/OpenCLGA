from threading import Thread, Event, Lock, current_thread
from logger import *

class Task(Logger):
    __id = 0
    def __init__(self, *args, **argd):
        Logger.__init__(self)
        Task.__id += 1
        self.__taskid = Task.__id

    def __getattr__(self, name):
        if name == "taskid":
            return self.__taskid
        return None

    def run(self):
        raise NotImplementedError

    def get_current_thread_name(self):
        t = current_thread()
        return t.name

class TaskThread(Thread):
    def __init__(self, name = "Unknown"):
        Thread.__init__(self, name = name)
        self.__qlock = Lock()
        self.tasks = []
        self.wati_for_task = Event()
        self.wati_for_stop = Event()
        # Dump msg
        self.debug = True

    def debug_log(self, msg, prefixname = False, postfixname = False):
        if self.debug:
            self.log(msg, prefixname, postfixname)

    def log(self, msg, prefixname = False, postfixname = False):
        pre = "[%s]"%(self.name) if prefixname else ""
        post = "[%s]"%(self.name) if postfixname else ""
        print(pre+msg+post)

    def start(self):
        Thread.start(self)

    def run(self):
        self.log(">>>>> TT : start running ...", prefixname = True)
        while True:
            # If there's not pending task, wait to avoid busy-looping.
            if len(self.tasks) == 0:
                self.wati_for_task.wait()

            # If stop() is called, remaining tasks won't be exectued !
            if self.wati_for_stop.isSet():
                break

            # Remove a pending task from the queue.
            self.__qlock.acquire()
            task = self.tasks.pop(0)
            self.__qlock.release()

            if task:
                self.debug_log(">>>>> TT : start executing ... task (%d)"%(task.taskid), prefixname = True)
                task.run()
        self.log(">>>>> TT : ending.", prefixname = True)

    def stop(self):
        self.log("stop ...", postfixname = True)
        self.wati_for_stop.set()
        self.wati_for_task.set()
        self.join()
        self.tasks.clear()
        self.tasks = None
        self.wati_for_task = None
        self.wati_for_stop = None
        self.__qlock = None

    def addtask(self, task):
        self.debug_log("adding task(%d) to ..."%(task.taskid), postfixname = True)
        # TODO : Add priority re-order for tasks.
        self.__qlock.acquire()
        self.tasks.append(task)
        self.__qlock.release()
        self.wati_for_task.set()
        self.wati_for_task.clear()
        return task.taskid

    def canceltask(self, taskid):
        self.debug_log("canceling task(%d) in ..."%(taskid), postfixname = True)
        self.__qlock.acquire()
        task = list(filter(lambda x: x.taskid == taskid, self.tasks))
        if len(task) == 1:
            self.tasks.remove(task[0])
            self.debug_log("task(%d) canceled in ..."%(taskid), postfixname = True)
        self.__qlock.release()
