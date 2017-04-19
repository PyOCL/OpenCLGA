#!/usr/bin/python3
import os
import sys
import ssl
import threading
from base64 import b64encode
from socketserver import ThreadingMixIn
from http.server import HTTPServer
from io import StringIO

from .utilities.generaltaskthread import TaskThread, Task, Logger
from .utilities.httpwebsocketserver import HTTPWebSocketsHandler

## A Handler class when the Http request is upgraded to websocket, the following
#  methods will be called accordingly.
class HttpWSMessageHandler(HTTPWebSocketsHandler):

    base_path = None
    cn_hdlr = None
    msg_hdlr = None
    dcn_hdlr = None
    def on_ws_message(self, message):
        if message is None:
            message = ''

        self.log_message('websocket received %s', str(message))
        if self.msg_hdlr:
            self.msg_hdlr(self.client_address, message)

    def on_ws_connected(self):
        self.log_message('%s','websocket connected')
        if self.cn_hdlr:
            self.cn_hdlr(self.client_address, self)

    def on_ws_closed(self):
        if self.dcn_hdlr:
            self.dcn_hdlr(self.client_address)
        self.log_message('%s','websocket closed')

## Handle requests in a separate thread.
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass

## A task class which intends to call HTTPServer's serve_forever in separated
#  thread.
#  @param server The Http Server instance
#  @param credentials The credentials to be wrapped if secure connection is required.
class HttpWSTask(Task):
    def __init__(self, server, credentials = ''):
        Task.__init__(self)
        self.logger_level = Logger.MSG_ALL ^ Logger.MSG_VERBOSE
        self.server = server
        self.server.daemon_threads = True
        self.server.auth = b64encode(credentials.encode('ascii'))
        if credentials:
            self.server.socket = ssl.wrap_socket(self.server.socket, certfile='./server.pem', server_side=True)
            self.info('Secure https server is created @ port {}.'.format(self.server.server_port))
        else:
            self.info('Http server is created @ port {}.'.format(self.server.server_port))

    def run(self):
        self.verbose('Http WS server is serving forever now !!')
        try:
            self.server.serve_forever()
        except:
            pass

## Create threaded http server which is able to upgrade HTTP request to websocket
#  @param ip IP for server.
#  @param port Listen on this port to accept connection.
#  @param credentials The credentials file if a secure connection is required.
#  @param connect_handler A handler function which is called when the http request
#  is upgraded to websocket.
#  @param message_handler A handler function which is called when there's any
#  message received by the websocket.
#  @param disconnect_handler A handler function which is called when the websocket
#  disconnects to server.
class OclGAWSServer(object):
    def __init__(self, ip, port, credentials = '', connect_handler = None,
                 message_handler = None, disconnect_handler = None,
                 base_path = None):
        HttpWSMessageHandler.cn_hdlr = connect_handler
        HttpWSMessageHandler.msg_hdlr = message_handler
        HttpWSMessageHandler.dcn_hdlr = disconnect_handler
        HttpWSMessageHandler.base_path = base_path
        self.httpwsserver = ThreadedHTTPServer((ip, port), HttpWSMessageHandler)
        self.httpwsserver_thread = TaskThread(name='httpwsserver')
        self.httpwsserver_thread.daemon = True
        self.credentials = credentials

    ## Run the http server's serve_forever function in a separated thread.
    def run_server(self):
        if self.httpwsserver_thread:
            self.httpwsserver_thread.start()
            task = HttpWSTask(self.httpwsserver, self.credentials)
            self.httpwsserver_thread.addtask(task)

    ## Shut down HttpServer and close the thread for it.
    def shutdown(self):
        if self.httpwsserver:
            self.httpwsserver.socket.close()
            self.httpwsserver.shutdown()
            self.httpwsserver = None
        if self.httpwsserver_thread:
            self.httpwsserver_thread.stop()
            self.httpwsserver_thread = None
