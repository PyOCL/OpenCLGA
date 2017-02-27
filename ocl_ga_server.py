#!/usr/bin/python3
import sys
import time
import socket
import select
import threading
import traceback
from server_client import Server, OP_MSG_BEGIN, OP_MSG_END

class OpenCLGAServer():
    def __init__(self, options, port=12345):
        self.__paused = False
        self.__forceStop = False
        self.__options = options
        self.__callbacks = {
            "connected": [], # for notifying users that a client is connected
            "disconnected": [], # for notifying users that a client is disconnected
            "message": [] # for notifying users that a message is received from client
        }
        self.server = None
        self.__listen_at(port)

    def __listen_at(self, port):
        '''
        we should create a server socket and bind at all IP address with specified port.
        all commands are passed to client and wait for client's feedback.
        '''
        try:
            self.server = Server(ip = "0.0.0.0", port = port)
            self.server.setup_callbacks_info({ 0 : { "pre" : OP_MSG_BEGIN,
                                                     "post": OP_MSG_END,
                                                     "callback"  : self.__process_data}})
            self.server.run_server()
        except:
            traceback.print_exc()
            self.server = None
        pass

    def __send(self, command, data):
        '''
        Send method should send a dict with type property for command type and data property for
        command data. The whole payload should be translated into pickle structure.
        '''
        pass

    def __process_data(self, payload):
        '''
        Once we receive a payload dict which has a type property for command type and data property
        for command data.
        '''
        print("[Server] __process_data : %s"%(str(payload)))
        pass

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

    def prepare(self):
        pass

    def run(self, prob_mutate, prob_crossover):
        assert self.server != None
        pass

    def stop(self):
        assert self.server != None
        self.__forceStop = True
        self.server.send("stop")

    def pause(self):
        assert self.server != None
        self.__paused = True
        self.server.send("pause")

    def save(self, filename):
        assert self.server != None
        raise RuntimeError("OpenCL Server doesn't support save or restore")

    def restore(self, filename):
        raise RuntimeError("OpenCL Server doesn't support save or restore")

    def get_statistics(self):
        # think a good way to deal with asymmetric statistics
        pass

    def get_the_best(self):
        pass

    def shutdown(self):
        self.server.send("exit")
        # TODO : Go shutdown after checking all clients are dead.
        time.sleep(1)
        self.server.shutdown()
        self.server = None

if __name__ == "__main__":
    def get_input():
        data = None
        try:
            if sys.platform in ["linux", "darwin"]:
                import select
                time.sleep(0.1)
                if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
                    data = sys.stdin.readline().rstrip()
            elif sys.platform == "win32":
                import msvcrt
                time.sleep(0.1)
                if msvcrt.kbhit():
                    data = msvcrt.getch().decode("utf-8")
            else:
                pass
        except KeyboardInterrupt:
            data = "exit"
        return data

    try:
        oclGAServer = OpenCLGAServer("")
        print("Press r+<Enter> to run");
        print("Press p+<Enter> to pause")
        print("Press x+<Enter> to stop")
        print("Press s+<Enter> to save")
        print("Press ctrl+c to exit")

        while True:
            user_input = get_input()
            if "p" == user_input:
                oclGAServer.pause()
            elif "r" == user_input:
                oclGAServer.run(0.1, 0.3)
            elif "x" == user_input:
                oclGAServer.stop()
            elif "s" == user_input:
                oclGAServer.save("saved.pickle")
            elif "exit" == user_input:
                oclGAServer.shutdown()
                print("[OpenCLGAServer] Bye Bye !!")
                break
    except:
        traceback.print_exc()
