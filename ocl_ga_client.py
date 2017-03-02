#!/usr/bin/python3
import pyopencl as cl
import socket
import time
import pickle
import threading
from multiprocessing import Process, Pipe
from ocl_ga import OpenCLGA
from abc import ABC, abstractmethod

class IOpenCLGA(ABC):
    @abstractmethod
    def prepare(self, info):
        pass
    @abstractmethod
    def run(self):
        pass
    @abstractmethod
    def pause(self):
        pass
    @abstractmethod
    def save(self):
        pass
    @abstractmethod
    def stop(self):
        pass
    @abstractmethod
    def get_statistics(self):
        pass
    @abstractmethod
    def get_statistics(self):
        pass
    @abstractmethod
    def get_the_best(self):
        pass

from generaltaskthread import Task, TaskThread
class MonitorWorkerTask(Task):
    def __init__(self, proc_2_conn, callback, evt):
        Task.__init__(self)
        self.proc_2_conn = proc_2_conn
        self.callback = callback
        self.evt = evt

    def run(self):
        print("[Client][WorkerMonitor] monitoring ... ")
        while True:
            time.sleep(0.01)
            if self.evt.is_set():
                print("[Client][Monitor] stop monitoring ... ")
                break
            # Receiving results from Worker Process, and callback to Target
            for conn in list(self.proc_2_conn.values()):
                if conn and conn.poll():
                    msg = conn.recv()
                    # print("[Client] received result from OCL Worker : %s"%(msg))
                    self.callback(msg)

class OpenCLGAWorker(Process):
    def __init__(self, platform_index, device_index, conn):
        super().__init__()
        self.__platform_index = platform_index
        self.__device_index = device_index
        self.conn = conn

    def __create_context(self):
        platform = cl.get_platforms()[self.__platform_index]
        self.__device = platform.get_devices()[self.__device_index]
        self.__context = cl.Context(devices=[self.__device])
        return self.__context

    def run(self):
        ctx = self.__create_context()
        print('Worker started for context {}'.format(self.__device.name))

        ga_target = None
        def recv_handler(cmd, data):
            nonlocal ga_target
            print("[TT] cmd = %s"%(cmd))
            if cmd == "prepare":
                assert ga_target == None
                info = pickle.loads(data)
                info['cl_context'] = ctx
                info['saved_filename'] = info['saved_filename']%(self.__platform_index, self.__device_index)
                ga_target = info['instantiation_func']()
                ga_target.prepare(info)
            elif cmd == "run":
                assert ga_target != None
                ga_target.run()
            elif cmd == "pause":
                assert ga_target != None
                ga_target.pause()
            elif cmd == "save":
                assert ga_target != None
                ga_target.save()
            elif cmd == "stop":
                assert ga_target != None
                ga_target.stop()
            elif cmd == "best":
                # TODO : Maybe return results in a specific class.
                assert ga_target != None
                return { "type" : "best",
                         "device"   : (self.__device_index, self.__device.name),
                         "platform_idx" : self.__platform_index,
                         "result"  : ga_target.get_the_best(),
                         "city_info" : ga_target.get_city_info() }
            elif cmd == "statistics":
                # TODO : Maybe return results in a specific class.
                assert ga_target != None
                return { "type" : "statistics",
                         "device"   : (self.__device_index, self.__device.name),
                         "platform_idx" : self.__platform_index,
                         "result"  : ga_target.get_statistics() }
            else:
                assert False, "Unexpected comand !!"

        while True:
            result = None
            if self.conn.poll():
                dict_msg = self.conn.recv()
                result = recv_handler(dict_msg["command"], dict_msg["data"])
            if result:
                self.conn.send(result)
            time.sleep(0.01)


class OpenCLGAClient():
    def __init__(self, ip, port=12345):
        self.alive = True
        self.__server_ip = ip
        self.__server_port = port
        self.__workerProcesses = []
        self.__proc_2_pipe = {}
        #TODO: try to fork as more as possible process to host each context and connect to server.
        self.client = None
        self.__result_monitor = None

        self.__create_workers_for_devices()
        self.__start_workers()
        self.__connect()

    def __connect(self):
        from server_client import Client, OP_MSG_BEGIN, OP_MSG_END
        self.client = Client(self.__server_ip, self.__server_port)
        self.client.setup_callbacks_info({0 : { "pre" : OP_MSG_BEGIN,
                                                "post": OP_MSG_END,
                                                "callback" : self.__process_data}})

        self.monitor_break_evt = threading.Event()
        self.monitor_break_evt.clear()
        self.monitor = TaskThread(name = "monitor_thread")
        self.monitor.daemon = True
        self.monitor.start()
        self.monitor.addtask(MonitorWorkerTask(self.__proc_2_pipe,
                                               self.__recv_from_worker,
                                               self.monitor_break_evt))

        pass

    def __recv_from_worker(self, dict_result):
        result_type = dict_result["type"]
        self.__send(repr(dict_result))

    def __send(self, data):
        if self.client:
            self.client.send(data)
        pass

    def __process_data(self, data):
        '''
        Called when data is received from server.
        '''
        # Conver bytearray "data" to string-like object
        msg = str(data, 'ASCII')
        # print("[Client] processing data : %s"%(msg))
        dict_msg = eval(msg)
        if dict_msg.get("command", "") == "exit":
            self.__shutdown()
        else:
            # Sending message to WorkerProcesses
            for proc, conn in list(self.__proc_2_pipe.items()):
                conn.send(dict_msg)
        pass

    def __create_workers_for_devices(self):
        devices = []
        platforms = cl.get_platforms()
        for pidx in range(len(platforms)):
            devices = platforms[pidx].get_devices()
            for didx in range(len(devices)):
                self.__fork_process(pidx, didx)

    def __fork_process(self, platform_index, device_index):
        client_conn, worker_conn = Pipe()
        process = OpenCLGAWorker(platform_index, device_index, worker_conn)
        self.__workerProcesses.append(process)
        self.__proc_2_pipe[process] = client_conn

    def __start_workers(self):
        for worker in self.__workerProcesses:
            worker.start()

    def __stop_workers(self):
        while list(self.__proc_2_pipe.keys()):
            proc, conn = self.__proc_2_pipe.popitem()
            conn.close()
        for worker in self.__workerProcesses:
            print('process is alive'.format(worker.is_alive()))
            worker.terminate()
        self.__workerProcesses = []

    def __shutdown(self):
        if self.monitor:
            self.monitor_break_evt.set()
            self.monitor.stop()
            self.monitor = None
        if self.client:
            self.client.shutdown()
        self.client = None
        self.__stop_workers()
        self.alive = False

    def shutdown(self):
        self.__shutdown()

    def is_alive(self):
        return self.alive

oclClient = None
def start_ocl_ga_client():
    global oclClient
    assert oclClient == None
    oclClient = OpenCLGAClient("127.0.0.1")
    try:
        while True:
            if not oclClient.is_alive():
                print("[OpenCLGAClient] Bye Bye !!")
                break
            time.sleep(0.01)
    except KeyboardInterrupt:
        oclClient.shutdown()
    oclClient = None

if __name__ == '__main__':
    # NOTE : NOT support executing ocl_ga_client.py directly.
    #        Please call start_ocl_ga_client from each example.
    assert False, "NOT support executing ocl_ga_client.py directly. "\
                  "Please call start_ocl_ga_client in each example."
    pass
