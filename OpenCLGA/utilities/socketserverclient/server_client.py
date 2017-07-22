import select
import socket
import sys
import threading
import time
import traceback

from ..generaltaskthread import TaskThread, Task

OP_MSG_BEGIN       = bytearray('OPMsgB', 'ASCII')
OP_MSG_END         = bytearray('OPMsgE', 'ASCII')

## A handler class to register target prefix / postfix / callback.
#  It will identify and extract real messages between prefix and postfix
#  and then deliver through callback function.
#  @var temp_data Temporary bytearray to store received data from socket
#  @var callbacks_info Information will be used when specific message is received.
#                      e.g.  { 'pre' : OP_HT_DATA_BEGIN,
#                              'post': OP_HT_DATA_END,
#                              'callback'  : callbak }
#                      Data in between 'pre' & 'post' is a pickled bitstream.
#                      'callback' is going to be invoked when complete message
#                      is received.
class RecvDataHandler(object):
    def __init__(self, callbacks_info):
        assert 'pre' in callbacks_info
        assert 'post' in callbacks_info
        assert 'callback' in callbacks_info and callable(callbacks_info['callback'])
        self.callbacks_info = callbacks_info
        self.temp_data = b''

    def _check_for_recv(self, s):
        # Receive data from socket
        try:
            data = s.recv(65536)
            if data and len(data):
                self.temp_data += data
                return True
        except:
            return False
        return False

    ## Extract message from temp_data according to prefix/postfix.
    #  Then callback to registrar.
    def _extract_specific_task(self):
        assert self.callbacks_info != {}
        # Check the completeness of received data, and callback if it's finished.
        prefix = self.callbacks_info['pre']
        postfix = self.callbacks_info['post']
        callback = self.callbacks_info['callback']

        # for info in self.callbacks_info.values():
        pre_idx = self.temp_data.find(prefix)
        post_idx = self.temp_data.find(postfix)
        if pre_idx >= 0 and post_idx >= 0:
            assert pre_idx == 0, 'pre_idx should be 0 !'
            # If the data is enclosed between 'pre' & 'post'
            msg = self.temp_data[pre_idx+len(prefix):post_idx]
            callback(msg)
            return True, post_idx, len(postfix)
        return False, -1, -1

    ## Once a complete message is sent, trail it.
    def _remove_temp_data(self, post_idx, len_of_post):
        # print('temp_data = {}'.format(self.temp_data))
        # print('length of temp_data = {}'.format(len(self.temp_data)))
        # print(' post_idx = {}, len_of_post = {}'.format(post_idx, len_of_post))
        if len(self.temp_data) > post_idx + len_of_post:
            self.temp_data = self.temp_data[post_idx + len_of_post:]
        else:
            self.temp_data = b''
        # print('after temp_data = {}'.format(self.temp_data))

## A handler class holds a data queue for messages to be sent in another thread.
class SendDataHandler(object):
    def __init__(self, data_prefix = '', data_postfix = ''):
        self.__q_lock = threading.Lock()
        self.__sendq = bytearray()
        self.__evt_wait_for_data = threading.Event()
        self.__evt_wait_for_data.clear()
        self.__evt_break_send = threading.Event()
        self.__evt_break_send.clear()
        self.__prefix = data_prefix
        self.__postfix = data_postfix

        self.thread_sender = TaskThread(name='msg_sender')
        if self.thread_sender and not self.thread_sender.is_alive():
            send_task = HandlerSendTask(self, self.__evt_break_send)
            self.thread_sender.start()
            self.thread_sender.addtask(send_task)

    def append_data_to_queue(self, msg):
        data = bytearray(msg, 'ASCII') if msg != None and type(msg) == str else msg
        # print('data:{} ,type:{}, current sendq:{}, type of sendq:{}'.format(data, type(data), self.__sendq, type(self.__sendq)))
        with self.__q_lock:
            self.__sendq += self.__prefix + data +  self.__postfix

        self.__evt_wait_for_data.set()

    def clone_data_queue(self):
        return self.__sendq[:]

    def clear_data_queue(self):
        with self.__q_lock:
            self.__sendq = bytearray()
        self.__evt_wait_for_data.clear()

    def wait(self):
        self.__evt_wait_for_data.wait()

    def has_pending_data(self):
        return len(self.__sendq) != 0

    def shutdown(self):
        if self.thread_sender:
            self.__evt_break_send.set()
            self.__evt_wait_for_data.set()
            self.thread_sender.stop()
            self.thread_sender = None

## A instance to encapsulate SendDataHandler/RecvDataHandler.
class MessageHandler(SendDataHandler, RecvDataHandler):
    def __init__(self, socket, callbacks_info, mh_creator = None, mh_remover = None):
        SendDataHandler.__init__(self,
                                 data_prefix = callbacks_info['pre'],
                                 data_postfix = callbacks_info['post'])
        RecvDataHandler.__init__(self, callbacks_info)
        assert socket != None
        self.socket = socket
        self.__is_done = False
        self.mh_creator = mh_creator
        self.mh_remover = mh_remover

    def wait_for_msg(self):
        self.wait()

    def clone_msg(self):
        return self.clone_data_queue()

    def clear_msg(self):
        self.clear_data_queue()

    def has_pending_msg(self):
        return self.has_pending_data()

    def shutdown(self):
        if self.__is_done: return
        try:
            SendDataHandler.shutdown(self)
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        except:
            pass
        finally:
            self.socket = None
            self.__is_done = True

    def send_msg(self, msg):
        if self.__is_done: return
        self.append_data_to_queue(msg)

def socket_send(skt, data):
    assert skt != None
    assert isinstance(data, bytearray)
    if data != None:
        totalsent = 0
        try:
            while totalsent < len(data):
                sent = skt.send(data[totalsent:])
                if sent == 0:
                    raise RuntimeError('socket connection broken')
                totalsent = totalsent + sent
            # print('%d bytes data has been sent successfully !'%(totalsent))
        except ConnectionResetError:
            print('ConnectionResetError : Connection reset by peer')
        except:
            traceback.print_exc()
            print('Error while sending data via socket ...')

def loop_for_connections(evt_break, server_mh = None, client_mh = None):
    clients = {}
    read_list = []
    error_list = []
    if server_mh:
        read_list.append(server_mh.socket)
        error_list.append(server_mh.socket)
    if client_mh:
        read_list.append(client_mh.socket)
        error_list.append(client_mh.socket)
        clients[client_mh] = ''

    time_out = 1.0
    try:
        while 1:
            read_list = [skt for skt in read_list if skt.fileno() >=0]
            error_list = [skt for skt in error_list if skt.fileno() >=0]
            readable, writable, errored = select.select(read_list, [], error_list, time_out)

            if evt_break.is_set():
                break

            # Data arrived.
            for s in readable:
                if server_mh and s is server_mh.socket:
                    # Accept connections from client's request.
                    connection, addr = s.accept()
                    mh = server_mh.mh_creator(connection, addr)
                    clients[mh] = addr
                    read_list.append(connection)
                    print('[%s] Connected !'%(str(addr)))
                else:
                    for mh, a in list(clients.items()):
                        if s is mh.socket:
                            # Collect & append data.
                            if mh._check_for_recv(s):
                                # Analyze if data is received completely
                                success = True
                                while success:
                                    # Handle multiple-commands in a single recv.
                                    success, post_idx, len_of_post = mh._extract_specific_task()
                                    if success:
                                        mh._remove_temp_data(post_idx, len_of_post)
                            else:
                                # A readable socket without any data indicates
                                # a disconnected socket.
                                read_list.remove(s)
                                clients.pop(mh)
                                if server_mh:
                                    server_mh.mh_remover(mh)
                                mh.shutdown()

    except:
        traceback.print_exc()
        print('[Exception] inside loop for connections.')
    finally:
        try:
            while len(clients) > 0:
                mh, a = clients.popitem()
                print('[loop] Closing clients [%s] ...'%(str(a)))
                mh.shutdown()
            if server_mh:
                print('[loop] Closing server_mh ...')
                server_mh.shutdown()
        except:
            traceback.print_exc()

## A task runs in server's or client's thread to receive data.
class HandlerTask(Task):
    def __init__(self, evt_break, server_mh = None, client_mh = None):
        Task.__init__(self)
        self.evt_break = evt_break
        self.server_mh = server_mh
        self.client_mh = client_mh

    def run(self):
        loop_for_connections(self.evt_break, self.server_mh, self.client_mh)

## A task runs in server's or client's thread to send data.
class HandlerSendTask(Task):
    def __init__(self, mh, evt_break):
        Task.__init__(self)
        self.evt_break = evt_break
        self.mh = mh

    def run(self):
        while 1:
            if self.evt_break.is_set():
                break
            if not self.mh.has_pending_msg():
                self.mh.wait_for_msg()
            cloned_data = self.mh.clone_msg()
            socket_send(self.mh.socket, cloned_data)
            self.mh.clear_msg()

## A socket client which will connect to target ip/port
#  @param server_ip Server's IP
#  @param server_port Server's Port
#  @param callbacks_info Predefined target prefix/postfix to find our the exact
#                        messages and return these messages back through
#                        callback function.
class Client(object):
    def __init__(self, server_ip, server_port, callbacks_info):
        skt = socket.socket()
        skt.connect((server_ip, server_port))
        self.__ip = skt.getsockname()[0]
        self.msg_handler = MessageHandler(skt, callbacks_info)

        self.evt_break = threading.Event()
        self.evt_break.clear()
        task = HandlerTask(self.evt_break, client_mh = self.msg_handler)
        self.thread = TaskThread(name='client_recv_loop')
        self.thread.daemon = True
        self.thread.start()
        self.thread.addtask(task)

    def is_message_sent(self):
        if self.msg_handler:
            return not self.msg_handler.has_pending_msg()
        return True

    def get_address(self):
        return self.__ip

    def shutdown(self):
        try:
            print(' Client is shutting down ...')
            self.msg_handler.shutdown()
            self.evt_break.set()
            self.thread.stop()
            print(' Client is down ...')
        except:
            pass
        finally:
            self.msg_handler = None
            self.thread = None

    def send(self, msg):
        # Sample data to be sent !
        self.msg_handler.send_msg(msg)

## A socker server which is able to return received messages through the
#  callbacks_info and is able to send messages to clients
#  @param ip Server's IP
#  @param port Server's listening port
#  @param callbacks_info Predefined target prefix/postfix to find our the exact
#                        messages and return these messages back through
#                        callback function.
#  @param max_client The maximum number of connections
class Server(object):
    def __init__(self, ip, port, callbacks_info, max_client = 50):
        assert (ip != '')
        skt = socket.socket()
        # Avoid 'Address already in use' error when trying to lanch server
        # again right after shutting it down.
        skt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        skt.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        if sys.platform == 'linux':
            skt.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 60)
            skt.setsockopt(socket.SOL_TCP, socket.TCP_KEEPCNT, 4)
            skt.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 15)
        skt.bind((ip, port))
        skt.listen(max_client)
        self.connections = []
        self.clients = {}
        self.msg_handler = MessageHandler(skt, callbacks_info,
                                          mh_creator = self.client_mh_creator,
                                          mh_remover = self.client_mh_remover)
        self.thread = TaskThread(name='server_recv_loop')
        self.thread.daemon = True

        self.evt_break = threading.Event()
        self.evt_break.clear()

    def client_mh_creator(self, connection, addr):
        mh = MessageHandler(connection, self.msg_handler.callbacks_info)
        self.clients[mh] = addr
        return mh

    def client_mh_remover(self, connection):
        self.clients.pop(connection, None)
        pass

    def send(self, msg):
        for mh in self.clients.keys():
            mh.send_msg(msg)

    def shutdown(self):
        print('[Server] Shutting down ...')
        assert len(self.connections) == 0, 'All connections should be closed !!'
        while self.clients:
            mh, addr = self.clients.popitem()
            mh.shutdown()
        if self.msg_handler:
            self.msg_handler.shutdown()
            self.msg_handler = None
        if self.thread:
            self.evt_break.set()
            self.thread.stop()
            self.thread = None
        print('[Server] Shutting down ... end')

    def get_connected_lists(self):
        return list(self.clients.values())

    ## Non-blocking, execute a task in thread which monitors the socket in/out.
    def run_server(self):
        assert (self.thread != None)
        print('Start the server ...')
        if self.thread and not self.thread.is_alive():
            task = HandlerTask(self.evt_break,
                               server_mh = self.msg_handler)
            self.thread.start()
            self.thread.addtask(task)
