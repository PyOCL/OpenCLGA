#main program and imports for standalone purpose
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

from HTTPWebSocketsHandler import HTTPWebSocketsHandler

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

class WSSimpleEcho(HTTPWebSocketsHandler):
    def on_ws_message(self, message):
        if message is None:
            message = ''
        # echo message back to client
        self.send_message(message)
        self.log_message('websocket received "%s"',str(message))

    def on_ws_connected(self):
        self.log_message('%s','websocket connected')

    def on_ws_closed(self):
        self.log_message('%s','websocket closed')

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

def _ws_main():
    try:
        #Replace WSSimpleEcho with your own subclass of HTTPWebSocketHandler
        server = ThreadedHTTPServer(('', port), WSSimpleEcho)
        server.daemon_threads = True
        server.auth = b64encode(credentials.encode("ascii"))
        if secure:
            server.socket = ssl.wrap_socket (server.socket, certfile='./server.pem', server_side=True)
            print('started secure https server at port %d' % (port,))
        else:
            print('started http server at port %d' % (port,))
        server.serve_forever()
    except KeyboardInterrupt:
        print('^C received, shutting down server')
        server.socket.close()

if __name__ == '__main__':
    _ws_main()
