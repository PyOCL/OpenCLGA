#!/usr/bin/python3
import json
import os
import pickle
import queue
import socket
import sys
import time
import traceback
from .utils import get_local_IP
from .utilities.generaltaskthread import Logger
from .utilities.socketserverclient import Server, OP_MSG_BEGIN, OP_MSG_END
from .ocl_ga_wsserver import OclGAWSServer

## OpenCLGAServer is responsible for
#  1) Launch a http server and handle websocket connections.
#     Controller is the first connected websocket owner with the ability to
#     operate clients on other machines.
#     Viewers are the following connected websocket owners, they are only able to
#     receive status information.
#  2) Launch a socket server for all clients and then deliver commands & results
#     between UI and clients.
#  @param oprtions Configuration parameters for OpenCLGA
#  @param port Listening port for Server.
#  @var __options Stores all configuration parameters for OpenCLGA. These
#                 parameters should include Genes, Chromosomes, generations,
#                 fitness function...etc, for specific problem.
#  @var __q_kb Queue the input character from keyboard.
#  @var __q_ws Queue the input character from websocket connection.
#  @var __callbacks Store the correpsonding callback functions and notify repopulate_diff
#                   information back to registrar.
#  @var __ip The IP of OpenCLGAServer. We use '0.0.0.0' as the server's IP to bind
#            all IPv4 addresses on this local machine.
#  @var socket_server The socket server which delivers commands from UI to clients
#                     and receives results from clients.
#  @var socket_server_port The listneing port of socket server.
#  @var websockets Contain 'controller' & 'viewers', controller is the first
#                  connecter who is allowed to send commands from UI for
#                  controlling the whole operation ; viewers are only allowed
#                  to receive results.
#  @var elitism_round How many times that server received elites.
#  @var elitism_pick The number of elites what we need to keep and sort.
#  @var elitism_limit If elitism_round hits the limit, it's time for server
#                     to send elites back to ocl_ga
#  @var elites The list to store elites
class OpenCLGAServer(Logger):
    def __init__(self, options, port, base_path):
        Logger.__init__(self)
        self.logger_level = Logger.MSG_ALL ^ Logger.MSG_VERBOSE
        self.__paused = False
        self.__forceStop = False
        self.__callbacks = {
            'connected': [],    # for notifying users that a client is connected
            'disconnected': [], # for notifying users that a client is disconnected
            'message': []       # for notifying users that a message is received from client
        }

        self.__options = options
        self.__q_kb = ''
        self.__q_ws = queue.Queue()
        self.__ip = self.__get_host_ip()

        self.socket_server = None
        self.socket_server_port = port
        self._start_socket_server()

        elitism_info = options.get('elitism_mode', {})
        self.elitism_round = 0
        self.elitism_top = elitism_info.get('top', 0)
        self.elitism_every = elitism_info.get('every', 0)
        self.is_elitism_mode = all([self.elitism_top, self.elitism_every])
        self.elites = []
        self.optimized_for_max = options.get('opt_for_max', 'max') == 'max'

        self.client_workers = {}
        self.websockets = {'controller' : {}, 'viewers' : []}
        self.httpws_server = None
        self.httpws_server_port = 8000
        self.base_path = base_path
        self._start_http_websocket_server()

    def __get_host_ip(self, use_all=True):
        ip = '0.0.0.0' if use_all else get_local_IP()
        return ip

    ## Handle keyboard input on different platform
    def _handle_keyboard_message(self):
        data = None
        if sys.platform in ['linux', 'darwin']:
            import select
            if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
                data = sys.stdin.readline().rstrip()
        elif sys.platform == 'win32':
            import msvcrt
            if msvcrt.kbhit():
                data = msvcrt.getch().decode('utf-8')
                if data == '\r':
                    # Enter is pressed
                    data = self.__q_kb
                    self.__q_kb = ''
                else:
                    print(data)
                    self.__q_kb += data
                    data = None
        else:
            pass
        return data

    ## Get the data message which was queued earlier.
    def __get_ws_input(self):
        inputs = None
        try:
            inputs = self.__q_ws.get_nowait()
        except queue.Empty:
            pass
        return inputs

    ## Inputs from keyboard are raw command, i.e. 'run' / 'prepare' ...etc.
    #  we need to wrap it into a dictionary for following usage.
    def __adjust_kb_inputs(self, inputs):
        dict_inputs = {'command' : inputs} if inputs else {}
        return dict_inputs

    ## A while loop will keep call this method for inputs
    def get_input(self):
        try:
            time.sleep(0.01)
            kb_msg = self.__adjust_kb_inputs(self._handle_keyboard_message())
            if kb_msg:
                return kb_msg
            ws_msg = self.__get_ws_input()
            if ws_msg:
                return ws_msg
        except KeyboardInterrupt:
            return {'command' : 'exit'}
        return {}

    def __update_members(self, payload):
        self.__options.update(payload)
        self.elitism_top = self.__options.get('top', 10)
        self.elitism_every = self.__options.get('every', 100)
        print(self.elitism_top, self.elitism_every)
        self.optimized_for_max = self.__options['opt_for_max'] == 'max'
        self.verbose('prepare with args: {}'.format(self.__options))

    ## All input message will be handled here.
    def handle_message(self, msg):
        assert type(msg) == dict

        if 'command' not in msg:
            return True
        cmd = msg['command']
        self.info('process command {}'.format(cmd))

        if cmd == 'prepare':
            payload = msg.get('payload', {})
            if not payload:
                self.warning('Getting nothing in payload from UI to prepare. Use default configuration.')
            self.__update_members(payload)
            packed = pickle.dumps(self.__options)
            self.__prepare(packed)
        elif cmd == 'pause':
            self.__pause()
        elif cmd == 'run':
            if 'payload' in msg:
                self.__run(msg['payload']['prob_mutation'], msg['payload']['prob_crossover'])
            else:
                self.__run()
        elif cmd == 'stop':
            self.__stop()
        elif cmd == 'save':
            self.__save()
        elif cmd == 'get_st':
            self.__get_statistics()
        elif cmd == 'get_best':
            self.__get_the_best()
        elif cmd == 'restore':
            self.__restore()
        elif cmd == 'exit':
            self.__shutdown()
            return False
        return True

    ## A callback function to notify OpenCLGAServer the connection of websocket
    def _ws_connected(self, client_addr, wshandler):
        viewers_addr = [addr for addr, handler in self.websockets['viewers']]
        if not self.websockets['controller']:
            self.websockets['controller'] = (client_addr, wshandler)
            self.info('WS Controller {} is on !! '.format(client_addr))
        elif client_addr not in viewers_addr:
            self.websockets['viewers'].append((client_addr, wshandler))

        # Send current connected clients information to a UI new comer.
        for worker_id, msg in self.client_workers.items():
            self.__send_message_to_WSs(msg)

    ## A callback function to notify OpenCLGAServer the disconnection of websocket
    def _ws_disconnected(self, client_addr):
        viewers_addr = [addr for addr, handler in self.websockets['viewers']]
        if client_addr in viewers_addr:
            self.websockets['viewers'] = [ws for ws in self.websockets['viewers'] if ws[0] != client_addr]
        if self.websockets['controller'] and client_addr == self.websockets['controller'][0]:
            self.info('WS Controller is off, clean up all websockets !! ')
            self.websockets['controller'] = None
            self.websockets['viewers'] = []

    ## A callback function to notify OpenCLGAServer the message received from
    #  websocket. These message will be queued into __q_ws and be processed later.
    def _ws_queue_inputs(self, client_addr, byte_message):
        # Handle messages from WebSocket.
        if self.websockets['controller'] and client_addr != self.websockets['controller'][0]:
            self.verbose('WS client: {} message is ignored (Not controller !!)'.format(client_addr))
            return

        try:
            str_msg = str(byte_message, 'utf-8')
            self.__q_ws.put(json.loads(str_msg))
        except Exception as e:
            self.error('[Exception] WS client: {} sends message format: {}'.format(client_addr, byte_message))

    ## Create http server which is able to handle websocket connections.
    def _start_http_websocket_server(self):
        # Provide credentials if a secure server is expected.
        self.httpws_server = OclGAWSServer(self.__ip, self.httpws_server_port,
                                           connect_handler = self._ws_connected,
                                           message_handler = self._ws_queue_inputs,
                                           disconnect_handler = self._ws_disconnected,
                                           base_path = self.base_path)
        self.httpws_server.run_server()

    ## Create a socket server and bind at all IP address with specified port.
    #  Then all commands from UI are delivered to client and then wait for client's feedback.
    def _start_socket_server(self):
        try:
            self.socket_server = Server(self.__ip, self.socket_server_port,
                                        {'pre' : OP_MSG_BEGIN,
                                         'post': OP_MSG_END,
                                         'callback'  : self.__process_data })
            self.socket_server.run_server()
        except:
            traceback.print_exc()
            self.socket_server = None

    ## Process the received results from Clients and send to UI.
    def __process_data(self, data):
        try:
            # Conver bytearray 'data' to string-like object
            msg = str(data, 'ASCII')
            dict_msg = eval(msg)
            result_type = dict_msg['type']
            self.verbose('[Server] __process_data from client, type = %s '%(result_type))

            if dict_msg['type'] == 'workerConnected':
                worker_id = dict_msg['data']['worker']
                self.client_workers[worker_id] = dict_msg
            elif dict_msg['type'] == 'workerLost':
                worker_id = dict_msg['data']['worker']
                self.client_workers.pop(worker_id, None)
            elif dict_msg['type'] == 'statistics':
                st = dict_msg['result']
                self.__notify('message', {'statistics' : st})
            elif dict_msg['type'] == 'best':
                best_chromosome = eval(dict_msg['result'])
                self.__notify('message', {'best' : best_chromosome})
            elif dict_msg['type'] == 'save':
                saved_filename = dict_msg['result']
            elif dict_msg['type'] == 'generationResult':
                serialized_best_result = dict_msg['data']['result'].pop('best_result', None)
                worker_id = dict_msg['data']['worker']
                best_fitness = dict_msg['data']['result'].get('best_fitness', 0.0)
                if self.is_elitism_mode:
                    best_result = pickle.loads(serialized_best_result)
                    elites = best_result['elites']
                    elite_fitnesses = best_result['fitnesses']
                    elite_size = best_result['dna_size']
                    assert len(elite_fitnesses) == self.elitism_top, 'len(elite_fitnesses)={}, self.elitism_top={}'.format(len(elite_fitnesses), self.elitism_top)
                    assert len(elites) == elite_size * self.elitism_top

                    # append each elite from single worker to a single list.
                    for idx, fitness in enumerate(elite_fitnesses):
                        self.elites.append((fitness, elites[idx*elite_size:(idx+1)*elite_size], worker_id))

                    self.elitism_round += 1
                    if self.elitism_round >= self.elitism_every:
                        # sort the list, the fronter the better.
                        self.elites.sort(key=lambda item : item[0], reverse=self.optimized_for_max)
                        if len(self.elites) >= self.elitism_top:
                            self.elites = self.elites[:self.elitism_top]
                        self.__update_elites(pickle.dumps(self.elites))
                        self.elitism_round = 0

            self.__send_message_to_WSs(dict_msg)
        except:
            traceback.print_exc()

    ## Send message to UI through websockets
    def __send_message_to_WSs(self, msg):
        contoller = self.websockets.get('controller', None)
        jmsg = json.dumps(msg)
        if contoller:
            self.info('Send to Controller : {}'.format(msg))
            contoller[1].send_message(jmsg)
        viewers = self.websockets.get('viewers', [])
        for viewer in viewers:
            self.info('Send to Viewer : {}'.format(msg))
            viewer[1].send_message(jmsg)

    ## Notify correpsonding information back to the registrar.
    def __notify(self, name, data):
        if name not in self.__callbacks:
            return

        for func in self.__callbacks[name]:
            try:
                func(data)
            except Exception as e:
                self.error('exception while execution %s callback'%(name))
                traceback.print_exc()

    ## Register the callback function with speicif name.
    #  Right now only 'statistics', 'best' information will be sent back via
    #  these callback mechanism.
    def on(self, name, func):
        assert name in self.__callbacks
        if name in self.__callbacks:
            self.__callbacks[name].append(func)

    ## Unregister the callback function with speicif name.
    def off(self, name, func):
        assert name in self.__callbacks
        if (name in self.__callbacks):
            self.__callbacks[name].remove(func)

    def __prepare(self, s_info):
        data = {'command' : 'prepare', 'data' : s_info}
        self.socket_server.send(repr(data))

    def __run(self, prob_mutate = 0, prob_crossover = 0):
        assert self.socket_server != None
        data = {'command' : 'run', 'data' : (prob_mutate, prob_crossover)}
        self.socket_server.send(repr(data))

    def __stop(self):
        assert self.socket_server != None
        self.__forceStop = True
        data = {'command' : 'stop', 'data' : None}
        self.socket_server.send(repr(data))

    def __pause(self):
        assert self.socket_server != None
        self.__paused = True
        data = {'command' : 'pause', 'data' : None}
        self.socket_server.send(repr(data))

    def __save(self, filename = None):
        assert self.socket_server != None
        data = {'command' : 'save', 'data' : filename}
        self.socket_server.send(repr(data))

    def __restore(self, filename = None):
        assert self.socket_server != None
        data = {'command' : 'restore', 'data' : filename}
        self.socket_server.send(repr(data))

    def __get_statistics(self):
        assert self.socket_server != None
        data = {'command' : 'statistics', 'data' : None}
        self.socket_server.send(repr(data))

    def __get_the_best(self):
        assert self.socket_server != None
        data = {'command' : 'best', 'data' : None}
        self.socket_server.send(repr(data))

    def __update_elites(self, elites):
        assert self.socket_server != None
        data = {'command' : 'elites', 'data' : elites}
        self.socket_server.send(repr(data))

    ## Shut down all servers and correpsonding clients when receives
    # 'exit' command or KeyboardInterrupt.
    def __shutdown(self):
        assert self.socket_server != None
        data = {'command' : 'exit', 'data' : None}
        self.socket_server.send(repr(data))

        # TODO : check if there's no existing clients
        try:
            count = 0
            while count < 10:
                time.sleep(0.1)
                count += 1
        except:
            pass
        try:
            self.socket_server.shutdown()
        except:
            print("[OpenCLGAServer] exception while shutting down socket server ...")
            traceback.print_exc()
        finally:
            self.socket_server = None
        if self.httpws_server:
            try:
                self.httpws_server.shutdown()
            except:
                print("[OpenCLGAServer] exception while shutting down http web socket server ...")
                traceback.print_exc()
            finally:
                self.httpws_server = None
        self.client_workers = {}
        self.websockets = {}

def start_ocl_ga_server(info, port, callbacks = {}, base_path = None):
    try:
        if base_path is None:
            base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     'ui')
        oclGAServer = OpenCLGAServer(info, port, base_path)
        for name, callback in list(callbacks.items()):
            oclGAServer.on(name, callback)
        time.sleep(0.5)
        print('Press prepare    + <Enter> to prepare')
        print('Press run        + <Enter> to run');
        print('Press restore    + <Enter> to restore');
        print('Press pause      + <Enter> to pause')
        print('Press save       + <Enter> to save (filename:test%d%d.pickle)')
        print('Press stop       + <Enter> to stop')
        print('Press get_st     + <Enter> to get statistics')
        print('Press get_best   + <Enter> to get best')
        print('Press ctrl       + c       to exit')

        while True:
            user_input = oclGAServer.get_input()
            if not oclGAServer.handle_message(user_input):
                print('[OpenCLGAServer] Bye Bye !!')
                break
    except:
        traceback.print_exc()

if __name__ == '__main__':
    # NOTE : NOT support executing ocl_ga_server.py directly.
    #        Please call start_ocl_ga_server from each example.
    #        Configuration options for OpenCLGA should be provided.
    assert False, 'NOT support executing ocl_ga_client.py directly. '\
                  'Please call start_ocl_ga_server in each example.'
