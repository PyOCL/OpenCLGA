#!/usr/bin/python3
import os
import sys
import threading
import ssl
from base64 import b64encode

VER = sys.version_info[0]
if VER >= 3:
    from socketserver import ThreadingMixIn
    from http.server import HTTPServer
    from io import StringIO
else:
    from SocketServer import ThreadingMixIn
    from BaseHTTPServer import HTTPServer
    from StringIO import StringIO

print(__name__)
if __name__ == "ocl_ga_wsserver":
    from utilities.generaltaskthread import TaskThread, Task
    from utilities.httpwebsocketserver import HTTPWebSocketsHandler
else:
    from .utilities.generaltaskthread import TaskThread, Task
    from .utilities.httpwebsocketserver import HTTPWebSocketsHandler

if len(sys.argv) > 1:
    port = int(sys.argv[1])
else:
    port = 8000
if len(sys.argv) > 2:
    secure = str(sys.argv[2]).lower()=="secure"
else:
    secure = False
if len(sys.argv) > 3:
    credentials = str(sys.argv[3])
else:
    credentials = ""

class HttpWSMessageHandler(HTTPWebSocketsHandler):
    oclGAHandler = None
    def on_ws_message(self, message):
        if message is None:
            message = ''

        self.log_message('websocket received "%s"',str(message))
        if self.oclGAHandler:
            self.oclGAHandler(self.address_string(), self, message)

    def on_ws_connected(self):
        self.log_message('%s','websocket connected')

    def on_ws_closed(self):
        self.log_message('%s','websocket closed')

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

class HttpWSTask(Task):
    def __init__(self, server, credentials = ""):
        Task.__init__(self)
        self.server = server
        self.server.daemon_threads = True
        self.server.auth = b64encode(credentials.encode("ascii"))
        if credentials:
            self.server.socket = ssl.wrap_socket (self.server.socket, certfile='./server.pem', server_side=True)
            print("created secure https server @ port {}.".format(self.server.server_port))
        else:
            print("created http server @ port {}.".format(self.server.server_port))

    def run(self):
        print("start http ws server !!")
        self.server.serve_forever()

class OclGAWSServer(object):
    def __init__(self, ip, port, credentials = "", handler = None):
        # Create threaded http server
        HttpWSMessageHandler.oclGAHandler = handler
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
