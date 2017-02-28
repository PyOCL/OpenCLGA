import time
import select
import socket
import threading
import traceback

OP_MSG_BEGIN       = bytearray("OPMsgB", "ASCII")
OP_MSG_END         = bytearray("OPMsgE", "ASCII")

class SrvClient(object):
    def __init__(self, socket):
        assert socket != None
        self.socket = socket

    def shutdown(self):
        try:
            print(" SrvClient(%s) goes down ... "%(str(self.socket.getpeername())))
            self.socket.shutdown(socket.SHUT_RDWR)
        except:
            traceback.print_exc()
        finally:
            self.socket.close()
            self.socket = None

    def send(self, msg):
        # TODO : Concatenate these byte array
        self.__send(OP_MSG_BEGIN)
        self.__send(msg)
        self.__send(OP_MSG_END)

    def __send(self, msg):
        assert (self.socket != None)
        data = bytearray(msg, "ASCII") if msg != None and type(msg) == str else msg
        if data != None:
            totalsent = 0
            while totalsent < len(data):
                sent = self.socket.send(data[totalsent:])
                if sent == 0:
                    raise RuntimeError("socket connection broken")
                totalsent = totalsent + sent
            print("%d bytes data has been sent successfully !"%(totalsent))

class ReceiveDataHandler(object):
    def __init__(self):
        self.temp_data = {}
        self.callbacks_info = {}

    def setup_callbacks_info(self, callbacks_info):
        # Register the callback function when specific message is received.
        # e.g.
        # { 0 : { "pre" : OP_HT_DATA_BEGIN,
        #         "post": OP_HT_DATA_END,
        #         "mid" : OP_HT_DATA_MID,
        #         "callback"  : callbak }}
        #
        # Data in between "pre" & "mid" is a repr form of ip-ports information dictionary.
        # e.g.         ip_port_pairs = { "host_ip"     : string of IP,
        #                                "host_port"   : int of PORT,
        #                                "sender_ip"   : string of IP,
        #                                "sender_port" : int of PORT}
        #
        # Data in between "mid" & "post" is a pickled bitstream.
        #
        # "callback" is going to be invoked when a *complete* message is received.
        # *complete* - enclosed by "pre" & "post"

        for v in callbacks_info.values():
            assert "pre" in v and "post" in v and "callback" in v and callable(v["callback"])
        self.callbacks_info = callbacks_info

    def _check_for_recv(self, s, a):
        key = (s, a)
        # Receive data from socket
        data = s.recv(2048)
        if data and len(data):
            self.temp_data[key] = self.temp_data.get(key, b"") + data
            return True
        return False

    def _extract_specific_task(self, s, a):
        assert self.callbacks_info != {}
        # Check the completeness of received data, and callback if it's finished.
        data = self.temp_data.get((s, a), b"")
        for info in self.callbacks_info.values():
            pre_idx = data.find(info["pre"])
            post_idx = data.find(info["post"])
            if pre_idx >= 0 and post_idx >= 0:
                # If the data is in the format pre + XXX + mid + XXX + post
                # TODO : We don't have this case now
                if info.get("mid", "") and data.find(info["mid"]) >= 0:
                    mid_idx = data.find(info["mid"])
                    ipport = data[pre_idx+len(info["pre"]):mid_idx]
                    msg = data[mid_idx+len(info["mid"]):post_idx]
                    info["callback"](ipport, msg)
                    return True
                else:
                    # If the data is enclosed between "pre" & "post"
                    msg = data[pre_idx+len(info["pre"]):post_idx]
                    info["callback"](msg)
                    return True
        return False

    def _remove_temp_data(self, s, a):
        self.temp_data.pop((s, a))

class Client(ReceiveDataHandler):
    def __init__(self, server_ip, server_port):
        ReceiveDataHandler.__init__(self)

        self.socket = socket.socket()
        self.socket.connect((server_ip, server_port))
        self.evt_break = threading.Event()
        self.evt_break.clear()
        self.recv_thread = threading.Thread(target=self.__loop_for_connections)
        self.recv_thread.start()

    def __loop_for_connections(self):
        read_list = [self.socket]
        try:
            while 1:
                if self.evt_break.is_set():
                    break
                readable, writable, errored = select.select(read_list, [], [], 0)
                # Data arrived.
                for s in readable:
                    if s is self.socket:
                        addr = ""
                        # Collect & append data.
                        self._check_for_recv(s, addr)
                        # Analyze if data is received completely
                        if self._extract_specific_task(s, addr):
                            self._remove_temp_data(s, addr)
                    else:
                        assert False
                time.sleep(0.01)
        except:
            traceback.print_exc()
            print("[Exception] during server's loop for connections.")
        finally:
            pass

    def shutdown(self):
        try:
            self.evt_break.set()
            self.recv_thread.join()
            print(" Client goes down ... ")
            self.socket.shutdown(socket.SHUT_RDWR)
        except:
            pass
        finally:
            self.socket.close()
            self.socket = None

    def send(self, msg):
        # Sample data to be sent !
        self.__send(OP_MSG_BEGIN)
        self.__send(msg)
        self.__send(OP_MSG_END)

    def __send(self, msg):
        assert (self.socket != None)
        data = bytearray(msg, "ASCII") if msg != None and type(msg) == str else msg
        if data != None:
            totalsent = 0
            while totalsent < len(data):
                sent = self.socket.send(data[totalsent:])
                if sent == 0:
                    raise RuntimeError("socket connection broken")
                totalsent = totalsent + sent
            print("%d bytes data has been sent successfully !"%(totalsent))

class Server(ReceiveDataHandler):
    def __init__(self, ip = "", port = 5000, max_client = 10):
        ReceiveDataHandler.__init__(self)
        assert (ip != "")
        self.socket = socket.socket()
        self.socket.bind((ip, port))
        self.socket.listen(max_client)
        self.srv_clients = {}
        self.thread = threading.Thread(target=self.__loop_for_connections)
        self.thread.daemon = True
        self.evt_break = threading.Event()
        self.evt_break.clear()

    def __close_connections(self):
        try:
            while len(self.srv_clients) > 0:
                sc, a = self.srv_clients.popitem()
                print("Closing connection [%s] ..."%(str(a)))
                sc.shutdown()
            if self.socket:
                self.socket.close()
        except:
            traceback.print_exc()

    def send(self, msg):
        for sc in self.srv_clients.keys():
            sc.send(msg)

    def shutdown(self):
        print("[Server] Shutting down ...")
        self.__close_connections()
        if self.thread:
            self.evt_break.set()
            self.thread.join()
            self.thread = None
        print("[Server] Shutting down ... end")

    def get_connected_lists(self):
        names = [str(sc.socket.getpeername()) for sc in list(self.srv_clients.keys())]
        return names

    def __loop_for_connections(self):
        read_list = [self.socket]
        try:
            while 1:
                if self.evt_break.is_set():
                    break
                readable, writable, errored = select.select(read_list, [], [], 0)
                # Data arrived.
                for s in readable:
                    if s is self.socket:
                        # Accept connections from client's request.
                        client, addr = self.socket.accept()
                        sC = SrvClient(client)
                        self.srv_clients[sC] = addr
                        read_list.append(client)
                        print("[%s] Connected !"%(str(addr)))
                    else:
                        for sc, a in list(self.srv_clients.items()):
                            # Collect & append data.
                            if s is sc.socket:
                                if self._check_for_recv(s, a):
                                    # Analyze if data is received completely
                                    if self._extract_specific_task(s, a):
                                        self._remove_temp_data(s, a)
                                else:
                                    # A readable socket without any data indicates
                                    # a disconnected socket.
                                    read_list.remove(s)
                                    self.srv_clients.pop(sc)
                                    sc.shutdown()
                time.sleep(0.01)
        except:
            traceback.print_exc()
            print("[Exception] during server's loop for connections.")
        finally:
            self.__close_connections()

    def run_server(self):
        assert (self.thread != None)
        print("Start the server ...")
        if self.thread and not self.thread.is_alive():
            self.thread.start()
