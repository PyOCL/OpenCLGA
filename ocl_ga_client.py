#!/usr/bin/python3
import pyopencl as cl
import socket
import time
import threading
from multiprocessing import Process, Pipe
from ocl_ga import OpenCLGA
# note: we can use multiprocessing.Queue or multiprocessing.Value to exchange data
class OpenCLGAWorker(Process):
    def __init__(self, platform_index, device_index, conn, handler):
        super().__init__()
        self.__platform_index = platform_index
        self.__device_index = device_index
        self.conn = conn
        self.recveiver_handler = handler

    def __create_context(self):
        platform = cl.get_platforms()[self.__platform_index]
        self.__device = platform.get_devices()[self.__device_index]
        self.__context = cl.Context(devices=[self.__device])
        return self.__context

    def run(self):
        ctx = self.__create_context()
        print('Worker started for context {}'.format(self.__device.name))
        while True:
            if self.conn.poll():
                dict_msg = self.conn.recv()
                self.recveiver_handler(dict_msg["command"], dict_msg["data"])
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
        self.recveiver_handler = None
        self.__connect()

    def setup_recv_handler(self, handler):
        self.recveiver_handler = handler

        self.__create_workers_for_devices()
        self.__start_workers()
        pass

    def __connect(self):
        from server_client import Client, OP_MSG_BEGIN, OP_MSG_END
        self.client = Client(self.__server_ip, self.__server_port)
        self.client.setup_callbacks_info({0 : { "pre" : OP_MSG_BEGIN,
                                                "post": OP_MSG_END,
                                                "callback" : self.__process_data}})
        pass

    def __send(self, command, data):
        '''
        # TBD: Send command or data or result back to Server ???
        '''
        if self.client:
            # NOTE : For now, just send data back to server.
            self.client.send(data)
        pass

    def __process_data(self, data):
        '''
        Called when data is received from server.
        '''
        # Conver bytearray "data" to string-like object
        msg = str(data, 'ASCII')
        print("[Client] processing data : %s"%(msg))
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
        assert self.recveiver_handler != None
        client_conn, worker_conn = Pipe()
        process = OpenCLGAWorker(platform_index, device_index, worker_conn, self.recveiver_handler)
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
        import examples.taiwan_travel as tt
        oclClient.setup_recv_handler(tt.send_taiwan_travel_cmddata)
        while True:
            if not oclClient.is_alive():
                print("[OpenCLGAClient] Bye Bye !!")
                break
            time.sleep(0.01)
    except KeyboardInterrupt:
        oclClient.shutdown()
    oclClient = None

if __name__ == '__main__':
    start_ocl_ga_client()
