#!/usr/bin/python3
import traceback
import argparse
import pickle
import pyopencl as cl
from pyopencl import device_info as di
import random
import tempfile
import time
import uuid
from multiprocessing import Process, Pipe, Value, Event

from .ocl_ga import OpenCLGA
from .utilities.generaltaskthread import Logger
from .utilities.socketserverclient import Client, OP_MSG_BEGIN, OP_MSG_END

oclClient = None

## Queuy the list of platforms and the list of devices for specific platform.
def query_devices(c_p):
    import pyopencl as cl
    platforms = cl.get_platforms()
    devices = platforms[0].get_devices()

    data = []
    for pidx in range(len(platforms)):
            devices = platforms[pidx].get_devices()
            for didx in range(len(devices)):
                data.append((pidx, didx))
    c_p.send(data)

## OpenCLGAWorker is a spawned process which is supposed to run OpenCLGA on a
#  target device which is decided by OpenCLGAClient.
#  @param platform_index Platform index which is queried and assigned by Client.
#  @param device_index Device index which is queried and assigned by Client.
#  @param ip The IP of server.
#  @param port The listening port of server.
#  @var exit_evt A event to wait in method run(), and will be set when receving
#                'exit' command, or terminating.
#  @var uuid A unique ID for UI to identify the worker.
#  @var running A varialbe shared by client & worker process to identify if worker
#               is running or not.
class OpenCLGAWorker(Process, Logger):
    def __init__(self, platform_index, device_index, ip, port):
        Process.__init__(self)
        Logger.__init__(self)
        # self.logger_level ^= Logger.MSG_VERBOSE
        self.daemon = True
        self.exit_evt = Event()
        self.running = Value('i', 0)
        self.platform_index = platform_index
        self.device_index = device_index
        self.ip = ip
        self.port = port
        self.uuid = uuid.uuid1().hex
        self.ocl_ga = None

    ## Terminate worker process, this should be only called when OpenCLGAClient
    #  is shutting down. The exti_evt will be set to break the wait in the
    #  process's run.
    def terminate(self):
        self.exit_evt.set()
        while self.running.value:
            time.sleep(0.1)
        super(OpenCLGAWorker, self).terminate()

    ## The actual execution place in worker process.
    #  First, mark the process as running.
    #  Second, create opencl context according to the platform, device indices.
    #  Third, create a socket client as the communication channel to server.
    def run(self):
        self.running.value = 1
        random.seed()
        try:
            self.__create_context()
            self.info('Worker created for context {}'.format(self.device.name))
            self.info('Worker [{0}] connect to server {1}:{2}'.format(
                                self.device.name, self.ip, self.port))
        except:
            self.error('Create OpenCL context failed !')
            return
        try:
            self.client = Client(self.ip, self.port, { 'pre' : OP_MSG_BEGIN,
                                                       'post': OP_MSG_END,
                                                       'callback' : self._process_data })
            self.__notify_client_online(self.client.get_address())
            self.info('Worker [{0}] wait for commands'.format(self.device.name))

            # If client is terminated by ctrl+c, exception will be caught in
            # worker process.
            self.exit_evt.wait()
        except ConnectionRefusedError:
            self.error('Connection refused! Please check Server status.')
            self.client = None
        except KeyboardInterrupt:
            pass
        finally:
            self.__shutdown()

    ## Create opencl context according to specific information.
    def __create_context(self):
        self.platform = cl.get_platforms()[self.platform_index]
        assert self.platform is not None
        self.device = self.platform.get_devices()[self.device_index]
        assert self.device is not None
        self.dev_type = self.device.get_info(di.TYPE)
        self.context = cl.Context(devices=[self.device])
        return self.context

    ## Create opencl context according to specific information.
    def __send_and_dump_info(self, index, data):
        assert self.ocl_ga != None
        self.verbose('{0}\t\t==> {1} ~ {2} ~ {3}'.format(index, data['best'], data['avg'],
                                                                data['worst']))

        self.__send({'type' : 'generationResult',
                     'data' : { 'worker' :   self.uuid,
                                'result' : { 'best_fitness' : data['best'],
                                             'avg_fitness'  : data['avg'],
                                             'worst_fitness': data['worst'],
                                             'best_result'  : data['best_result'] }}})

    ## The callback funciton for OpenCLGA to notify state change.
    def _state_changed(self, state):
        self.__send({'type' : 'stateChanged',
                     'data' : { 'worker'    : self.uuid,
                                'state'     : state}})

    ## Create OpenCLGA instance with options
    #  @param options Algorithm setup information
    def __create_ocl_ga(self, options):
        options['cl_context'] = self.context
        options['generation_callback'] = self.__send_and_dump_info
        self.ocl_ga = OpenCLGA(options,
                               action_callbacks={ 'state' : self._state_changed })
        self.ocl_ga.prepare()
        self.info('Worker [{}]: oclGA prepared'.format(self.device.name))

    ## Receive raw data from server and take actions accordingly.
    #  @param data A string-like bytearray object which can be converted to
    #  dictionary.  Two keys should be included. 1) 'command' 2) 'data'
    def _process_data(self, data):
        msg = str(data, 'ASCII')
        dict_msg = eval(msg)
        cmd = dict_msg['command']
        payload = dict_msg['data']
        self.verbose('Worker [{}]: cmd received = {}'.format(self.device.name, cmd))

        if cmd in ['pause', 'stop', 'restore', 'best', 'save', 'statistics', 'elites'] and not self.ocl_ga:
            self.error('Cmd "{}" will only be processed if ocl_ga exists '.format(cmd))
            return
        try:
            if cmd == 'prepare':
                self.__create_ocl_ga(pickle.loads(payload))
            elif cmd == 'pause':
                self.ocl_ga.pause()
            elif cmd == 'stop':
                self.ocl_ga.stop()
            elif cmd == 'restore':
                self.ocl_ga.restore(payload)
            elif cmd == 'save':
                # NOTE : Need to think about this ... too large !
                # state_file = tempfile.NamedTemporaryFile(delete=False)
                self.ocl_ga.save(payload)
                # saved_filename  = state_file.name
                # with open(state_file.name, 'rb') as fd:
                self.__send({'type': 'save',
                             'result': None})
                # state_file.close()
            elif cmd == 'best':
                # TODO : A workaround to get best chromesome back for TSP
                #       May need to pickle this tuple as it contains specific data structure.
                best_chromosome, best_fitness, chromesome_kernel = self.ocl_ga.get_the_best()
                self.__send({'type': 'best',
                             'result': repr(best_chromosome)})
            elif cmd == 'statistics':
                self.__send({'type': 'statistics',
                             'result': self.ocl_ga.get_statistics()})
            elif cmd == 'run':
                prob_mutate, prob_cross = payload
                self.info('Worker [{}]: oclGA run with {}/{}'.format(self.device.name,
                                                                     prob_mutate, prob_cross))
                self.ocl_ga.run(prob_mutate, prob_cross)
            elif cmd == 'elites':
                self.ocl_ga.update_elites(pickle.loads(payload))
            elif cmd == 'exit':
                self.exit_evt.set()
            else:
                self.error('unknown command {}'.format(cmd))
        except:
            traceback.print_exc()

    ## Send data back to server
    #  @param data The msg to be sent.
    def __send(self, data):
        if self.client:
            self.client.send(repr(data))

    ## Called when the process is terminated or receives 'exit' command from
    #  server.
    #  Need to notify UI that the worker is lost and then socket client
    #  will be closed here.
    def __shutdown(self):
        self.info('Worker [{0}] is exiting ...'.format(self.device.name))
        try:
            if self.ocl_ga:
                self.ocl_ga.stop()
                self.ocl_ga = None
            self.__notify_client_offline()
        except:
            print('[OpenCLGAClient] Exception while notifying server ...')

        try:
            # NOTE : Make sure all message is sent from clients, so that UI could
            #        recieve the notification for client's offline.
            while not self.client.is_message_sent():
                time.sleep(0.1)
        except:
            pass
        if self.client:
            try:
                self.client.shutdown()
            except:
                print('[OpenCLGAClient] Exception while shutting down client socket ...')
        self.client = None
        self.running.value = 0

    ## Notify UI that client is connected.
    def __notify_client_online(self, client_ip):
        self.__send({'type' : 'workerConnected',
                     'data' : { 'type'         : cl.device_type.to_string(self.dev_type),
                                'platform'     : self.platform.name,
                                'name'         : self.device.name,
                                'ip'           : client_ip,
                                'worker'       : self.uuid}})

    ## Notify UI that client is lost.
    def __notify_client_offline(self):
        self.__send({'type' : 'workerLost',
                     'data' : { 'worker'       : self.uuid}})

## OpenCLGAClient is supposed to create as many worker processes as possible.
#  The number of workers should be the number of platforms on the machine
#  times the number of devices which is provided by each platform.
#  e.g. There're 2 devices for platform 1, 1 device for platform 2.
#       Finally, 3 worker processes will be created.
#  Since the computing power may vary among all devices, OpenCLGAClient will be
#  down until all workers are not alive.
class OpenCLGAClient(Logger):
    def __init__(self, ip, port):
        Logger.__init__(self)
        self.server_ip = ip
        self.server_port = port
        self.__workerProcesses = []
        self.__create_workers_for_devices()

    ## Start all worker processes, and setup a while-loop to monitor the status
    #  of each worker.
    #  Loop will be broken when all workers are all dead (either 1. have done
    #  their jobs or 2. are shut down by OpenCLGAServer 'exit' command) or
    #  a KeyboardInterrupt happens.
    def run_forever(self):
        try:
            self.__start_workers()
            while True:
                if not self.__is_alive():
                    self.info('[OpenCLGAClient] All workers are NOT alive, ByeBye !!')
                    break
                time.sleep(0.01)
        except KeyboardInterrupt:
            self.info('[OpenCLGAClient] KeyboardInterrupt, ByeBye !!')

    ## Stop all workers, and clean up variables.
    def shutdown(self):
        self.__stop_workers()
        self.__workerProcesses = []

    ## This is a workaround for Mac Intel Drivers. We will get an error:
    # pyopencl.cffi_cl.LogicError: clGetContextInfo failed: INVALID_CONTEXT
    # if we try to use get_devices() in this process. So, we create an extra
    # process to read all platforms and devices. After that, we can create
    # device and command queue without this error.
    def __create_workers_for_devices(self):
        p_p, c_p = Pipe()
        p = Process(target=query_devices, args=(c_p,))
        p.start()
        device_list = p_p.recv()
        p.join()
        for dev in device_list:
            self.__create_process(dev[0], dev[1])

    ## Create OpenCLGAWorker process according by platform and device.
    #  @param platform_index The index of platform
    #  @param device_index The index of device for certain platform.
    def __create_process(self, platform_index, device_index):
        process = OpenCLGAWorker(platform_index,
                                 device_index,
                                 self.server_ip,
                                 self.server_port)
        self.__workerProcesses.append(process)

    ## Start all worker processes
    def __start_workers(self):
        for worker in self.__workerProcesses:
            worker.start()

    ## Terminate all worker processes
    def __stop_workers(self):
        for worker in self.__workerProcesses:
            self.verbose('stop_workers ... {} is alive {}'.format(worker, worker.is_alive()))
            if worker.is_alive():
                worker.terminate()
                self.info('process {} is terminated.'.format(worker))

    ## OpenCLGAClient is only alive when all workers are alive.
    def __is_alive(self):
        alive = True
        for worker in self.__workerProcesses:
            alive = alive and worker.is_alive()
        return alive

## Start up a standalone OpenCLGAClient. It will be closed when all worker
#  process are dead. Also will be closed when receving KeyboardInterrupt (Ctrl+c).
#  @param server The IP of OpenCLGAServer.
#  @param port The port which is listened by OpenCLGAServer
def start_ocl_ga_client(server, port):
    global oclClient
    assert oclClient == None
    logger = Logger()
    oclClient = OpenCLGAClient(server, port)
    try:
        oclClient.run_forever()
    finally:
        oclClient.shutdown()
    oclClient = None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='OpenCLGA client help')
    parser.add_argument('server', metavar='ip', type=str,
                        help='the server ip, default : 127.0.0.1', default='127.0.0.1')
    parser.add_argument('port', metavar='port', type=int,
                        help='the server port, default : 12345', default=12345)
    args = parser.parse_args()
    start_ocl_ga_client(args.server, args.port)
