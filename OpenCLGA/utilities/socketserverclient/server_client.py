import time
import select
import socket
import threading
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
class ReceiveDataHandler(object):
    def __init__(self, callbacks_info):
        assert 'pre' in callbacks_info
        assert 'post' in callbacks_info
        assert 'callback' in callbacks_info and callable(callbacks_info['callback'])
        self.callbacks_info = callbacks_info
        self.temp_data = b''

    def _check_for_recv(self, s):
        # Receive data from socket
        data = s.recv(2048)
        if data and len(data):
            self.temp_data += data
            return True
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

## A instance to encapsulate ReceiveDataHandler and hold a data queue for
#  messages to be sent.
class MessageHandler(ReceiveDataHandler):
    def __init__(self, socket, callbacks_info):
        ReceiveDataHandler.__init__(self, callbacks_info)
        assert socket != None
        self.socket = socket
        self.sendq = bytearray()
        self.__is_done = False
        self.__prefix = callbacks_info['pre']
        self.__postfix = callbacks_info['post']

    def shutdown(self):
        if self.__is_done:
            return
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
        except:
            traceback.print_exc()
        finally:
            self.socket.close()
            self.socket = None
            self.__is_done = True

    def send(self, msg):
        assert not self.__is_done
        data = bytearray(msg, 'ASCII') if msg != None and type(msg) == str else msg
        # print('data:{} ,type:{}, current sendq:{}, type of sendq:{}'.format(data, type(data), self.sendq, type(self.sendq)))
        self.sendq += self.__prefix + data +  self.__postfix

def socket_send(socket, data):
    assert (socket != None)
    assert type(data) == bytearray
    if data != None:
        totalsent = 0
        try:
            while totalsent < len(data):
                sent = socket.send(data[totalsent:])
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
    try:
        while 1:
            if evt_break.is_set():
                break
            readable, writable, errored = select.select(read_list, [], error_list, 0)

            # If server has queued data, send it to all clients.
            if server_mh and server_mh.sendq and clients:
                for mh, a in list(clients.items()):
                    socket_send(mh.socket, server_mh.sendq)
                server_mh.sendq = bytearray()
            # If client has queued data, send it to server.
            if client_mh and client_mh.sendq:
                socket_send(client_mh.socket, client_mh.sendq)
                client_mh.sendq = bytearray()

            # Data arrived.
            for s in readable:
                if server_mh and s is server_mh.socket:
                    # Accept connections from client's request.
                    connection, addr = s.accept()
                    mh = MessageHandler(connection, server_mh.callbacks_info)
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
                                mh.shutdown()
            time.sleep(0.001)
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

## A task runs in server's or client's thread to handle send/recv.
class HandlerTask(Task):
    def __init__(self, evt_break, server_mh = None, client_mh = None):
        Task.__init__(self)
        self.evt_break = evt_break
        self.server_mh = server_mh
        self.client_mh = client_mh

    def run(self):
        loop_for_connections(self.evt_break, self.server_mh, self.client_mh)

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
        self.thread = TaskThread(name='client_loop')
        self.thread.daemon = True
        self.thread.start()
        self.thread.addtask(task)

    def get_address(self):
        return self.__ip

    def shutdown(self):
        try:
            self.msg_handler.shutdown()
            self.evt_break.set()
            self.thread.stop()
            print(' Client goes down ... ')
        except:
            pass
        finally:
            self.thread = None
            self.msg_handler = None

    def send(self, msg):
        # Sample data to be sent !
        self.msg_handler.send(msg)

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
        skt.bind((ip, port))
        skt.listen(max_client)
        self.msg_handler = MessageHandler(skt, callbacks_info)

        self.thread = TaskThread(name='server_loop')
        self.thread.daemon = True
        self.evt_break = threading.Event()
        self.evt_break.clear()

    def send(self, msg):
        self.msg_handler.send(msg)

    def shutdown(self):
        print('[Server] Shutting down ...')
        if self.msg_handler:
            self.msg_handler.shutdown()
            self.msg_handler = None
        if self.thread:
            self.evt_break.set()
            self.thread.stop()
            self.thread = None
        print('[Server] Shutting down ... end')

    def get_connected_lists(self):
        # TODO : Get connected clients from Server MessageHandler
        return []

    ## Non-blocking, execute a task in thread which monitors the socket in/out.
    def run_server(self):
        assert (self.thread != None)
        print('Start the server ...')
        if self.thread and not self.thread.is_alive():
            task = HandlerTask(self.evt_break, server_mh = self.msg_handler)
            self.thread.start()
            self.thread.addtask(task)
