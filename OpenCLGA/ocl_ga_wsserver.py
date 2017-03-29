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

class HttpWSMessageHandler(HTTPWebSocketsHandler):
    cn_hdlr = None
    msg_hdlr = None
    dcn_hdlr = None
    def on_ws_message(self, message):
        if message is None:
            message = ''

        self.log_message('websocket received "%s"',str(message))
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

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

class HttpWSTask(Task):
    def __init__(self, server, credentials = ""):
        Task.__init__(self)
        self.logger_level = Logger.MSG_ALL ^ Logger.MSG_VERBOSE
        self.server = server
        self.server.daemon_threads = True
        self.server.auth = b64encode(credentials.encode("ascii"))
        if credentials:
            self.server.socket = ssl.wrap_socket (self.server.socket, certfile='./server.pem', server_side=True)
            self.info("Secure https server is created @ port {}.".format(self.server.server_port))
        else:
            self.info("Http server is created @ port {}.".format(self.server.server_port))

    def run(self):
        self.verbose("Http WS server is serving forever now !!")
        self.server.serve_forever()

class OclGAWSServer(object):
    def __init__(self, ip, port, credentials = "", connect_handler = None,
                 message_handler = None, disconnect_handler = None):
        # Create threaded http server
        HttpWSMessageHandler.cn_hdlr = connect_handler
        HttpWSMessageHandler.msg_hdlr = message_handler
        HttpWSMessageHandler.dcn_hdlr = disconnect_handler
        self.httpwsserver = ThreadedHTTPServer((ip, port), HttpWSMessageHandler)
        self.httpwsserver_thread = TaskThread(name="httpwsserver")
        self.httpwsserver_thread.daemon = True
        self.credentials = credentials

    def run_server(self):
        # Run the http server in a separated thread.
        if self.httpwsserver_thread:
            self.httpwsserver_thread.start()
            task = HttpWSTask(self.httpwsserver, self.credentials)
            self.httpwsserver_thread.addtask(task)

    def shutdown(self):
        if self.httpwsserver:
            self.httpwsserver.socket.close()
            self.httpwsserver.shutdown()
            self.httpwsserver = None
        if self.httpwsserver_thread:
            self.httpwsserver_thread.stop()
            self.httpwsserver_thread = None
