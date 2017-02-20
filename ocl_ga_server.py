#!/usr/bin/python3
import traceback

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
        self.__listen_at(port)

    def __listen_at(self, port):
        '''
        we should create a server socket and bind at all IP address with specified port.
        all commands are passed to client and wait for client's feedback.
        '''
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
        pass

    def stop(self):
        self.__forceStop = True

    def pause(self):
        self.__paused = True

    def save(self, filename):
        raise RuntimeError("OpenCL Server doesn't support save or restore")

    def restore(self, filename):
        raise RuntimeError("OpenCL Server doesn't support save or restore")

    def get_statistics(self):
        # think a good way to deal with asymmetric statistics
        pass

    def get_the_best(self):
        pass
