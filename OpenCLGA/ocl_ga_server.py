#!/usr/bin/python3
import json
import queue
import socket
import sys
import threading
import time
import traceback

from .utilities.socketserverclient import Server, OP_MSG_BEGIN, OP_MSG_END
from .ocl_ga_wsserver import OclGAWSServer

class OpenCLGAServer(object):
    def __init__(self, options=None, port=12345):
        self.__paused = False
        self.__forceStop = False
        self.__callbacks = {
            "connected": [], # for notifying users that a client is connected
            "disconnected": [], # for notifying users that a client is disconnected
            "message": [] # for notifying users that a message is received from client
        }
        self.__serialized_options = options
        self.__q_kb = ""
        self.__q_ws = queue.Queue()
        self.server_ip = "0.0.0.0"

        self.socket_server = None
        self.socket_server_port = port
        self._start_socket_server()

        self.websockets = {}
        self.httpws_server = None
        self.httpws_server_port = 8000
        self._start_http_websocket_server()

    def _handle_keyboard_message(self):
        data = None
        if sys.platform in ["linux", "darwin"]:
            import select
            if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
                data = sys.stdin.readline().rstrip()
        elif sys.platform == "win32":
            import msvcrt
            if msvcrt.kbhit():
                data = msvcrt.getch().decode("utf-8")
                if data == "\r":
                    # Enter is pressed
                    data = self.__q_kb
                    self.__q_kb = ""
                else:
                    self.__q_kb += data
                    print(data)
                    data = None
        else:
            pass
        return data

    def __get_ws_input(self):
        inputs = None
        try:
            inputs = self.__q_ws.get_nowait()
        except queue.Empty:
            pass
        return inputs

    def __adjust_kb_inputs(self, inputs):
        dict_inputs = {"command" : inputs} if inputs else {}
        return dict_inputs

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

    def handle_message(self, msg):
        assert type(msg) == dict

        if 'command' not in msg:
            return True
        cmd = msg['command']
        print('process command {}'.format(cmd))

        if cmd == 'prepare':
            # TODO : A workaround to make UI can run TaiwanTravel example by
            #        provide inforamtion from self.__serialized_options.
            payload = self.__serialized_options if self.__serialized_options else msg.get('payload', {})
            print('prepare with args: {}'.format(payload))
            self.prepare(payload)
        elif cmd == "pause":
            self.pause()
        elif cmd == "run":
            if 'payload' in msg:
                self.run(msg['payload']['prob_mutation'], msg['payload']['prob_crossover'])
            else:
                self.run()
        elif cmd == "stop":
            self.stop()
        elif cmd == "save":
            self.save()
        elif cmd == "get_st":
            self.get_statistics()
        elif cmd == "get_best":
            self.get_the_best()
        elif cmd == "restore":
            self.restore()
        elif cmd == "exit":
            self.shutdown()
            return False
        return True

    def _queue_ws_inputs(self, client_addr, wshandler, byte_message):
        # Handle messages from WebSocket.
        if client_addr not in self.websockets:
            self.websockets[client_addr] = wshandler

        try:
            str_msg = str(byte_message, "utf-8")
            self.__q_ws.put(json.loads(str_msg))
        except Exception as e:
            print("[Exception] WS client: {} sends message format: {}".format(client_addr, byte_message))

    def _start_http_websocket_server(self):
        self.httpws_server = OclGAWSServer(self.server_ip, self.httpws_server_port, handler = self._queue_ws_inputs)
        self.httpws_server.run_server()

    def _start_socket_server(self):
        '''
        we should create a server socket and bind at all IP address with specified port.
        all commands are passed to client and wait for client's feedback.
        '''
        try:
            self.socket_server = Server(self.server_ip, self.socket_server_port,
                                        {0 : {"pre" : OP_MSG_BEGIN,
                                              "post": OP_MSG_END,
                                              "callback"  : self.__process_data}})
            self.socket_server.run_server()
        except:
            traceback.print_exc()
            self.socket_server = None

    def __send(self, command, data):
        '''
        Send method should send a dict with type property for command type and data property for
        command data. The whole payload should be translated into pickle structure.
        '''
        pass

    def __process_data(self, data):
        '''
        Once we receive a payload dict which has a type property for command type and data property
        for command data.
        '''
        try:
            # Conver bytearray "data" to string-like object
            msg = str(data, 'ASCII')
            dict_msg = eval(msg)
            result_type = dict_msg["type"]
            print("[Server] __process_data from client, type = %s "%(result_type))

            if dict_msg["type"] == "statistics":
                st = dict_msg["result"]
                self.__notify("message", {"statistics" : st})
            elif dict_msg["type"] == "best":
                best_chromosome = eval(dict_msg["result"])
                self.__notify("message", {"best" : best_chromosome})
            elif dict_msg["type"] == "save":
                saved_filename = dict_msg["result"]

            # TODO : A temporary place to send message back to web page via websockets
            for wsClient in list(self.websockets.values()):
                wsClient.send_message(repr(result_type))
        except:
            traceback.print_exc()

    def __notify(self, name, data):
        if name not in self.__callbacks:
            return

        for func in self.__callbacks[name]:
            try:
                func(data)
            except Exception as e:
                print("exception while execution %s callback"%(name))
                print(traceback.format_exc())

    # public APIs
    @property
    def paused(self):
        return self.__paused

    @property
    def elapsed_time(self):
        return self.__elapsed_time

    def on(self, name, func):
        if name in self.__callbacks:
            self.__callbacks[name].append(func)

    def off(self, name, func):
        if (name in self.__callbacks):
            self.__callbacks[name].remove(func)

    def prepare(self, s_info):
        data = {"command" : "prepare", "data" : s_info}
        self.socket_server.send(repr(data))

    def run(self, prob_mutate = 0, prob_crossover = 0):
        assert self.socket_server != None
        data = {"command" : "run", "data" : (prob_mutate, prob_crossover)}
        self.socket_server.send(repr(data))

    def stop(self):
        assert self.socket_server != None
        self.__forceStop = True
        data = {"command" : "stop", "data" : None}
        self.socket_server.send(repr(data))

    def pause(self):
        assert self.socket_server != None
        self.__paused = True
        data = {"command" : "pause", "data" : None}
        self.socket_server.send(repr(data))

    def save(self, filename = None):
        assert self.socket_server != None
        data = {"command" : "save", "data" : filename}
        self.socket_server.send(repr(data))

    def restore(self, filename = None):
        assert self.socket_server != None
        data = {"command" : "restore", "data" : filename}
        self.socket_server.send(repr(data))

    def get_statistics(self):
        assert self.socket_server != None
        data = {"command" : "statistics", "data" : None}
        self.socket_server.send(repr(data))

    def get_the_best(self):
        assert self.socket_server != None
        data = {"command" : "best", "data" : None}
        self.socket_server.send(repr(data))

    def shutdown(self):
        assert self.socket_server != None
        data = {"command" : "exit", "data" : None}
        self.socket_server.send(repr(data))

        # TODO : check if there's no existing clients
        count = 0
        while count < 10:
            time.sleep(0.1)
            count += 1
        self.socket_server.shutdown()
        self.socket_server = None

def start_ocl_ga_server(serialized_info, callbacks = {}):
    try:
        oclGAServer = OpenCLGAServer(options=serialized_info)
        for name, callback in list(callbacks.items()):
            oclGAServer.on(name, callback)
        time.sleep(0.5)
        print("Press prepare    + <Enter> to prepare")
        print("Press run        + <Enter> to run");
        print("Press restore    + <Enter> to restore");
        print("Press pause      + <Enter> to pause")
        print("Press save       + <Enter> to save (filename:test%d%d.pickle)")
        print("Press stop       + <Enter> to stop")
        print("Press get_st     + <Enter> to get statistics")
        print("Press get_best   + <Enter> to get best")
        print("Press ctrl       + c       to exit")

        while True:
            user_input = oclGAServer.get_input()
            if not oclGAServer.handle_message(user_input):
                print("[OpenCLGAServer] Bye Bye !!")
                break
    except:
        traceback.print_exc()

if __name__ == "__main__":
    # NOTE : NOT support executing ocl_ga_server.py directly.
    #        Please call start_ocl_ga_server from each example.
    assert False, "NOT support executing ocl_ga_client.py directly. "\
                  "Please call start_ocl_ga_server in each example."
