# httpwebsockethandler
Python combines HTTP and WebSocketServer with SSL support

##command line options

```shell
#assume ExampleWSServer.py and HTTPWebSocketsHandler.py are in the current directory
nohup python ExampleWSServer.py 8000 secure username:mysecret >>ws.log&
```

This uses SSL/https. Change username:mysecret in a username:password chosen by yourself. The websserver uses port 8000 by default, and can be changed by an optional parameter:

`nohup python ExampleWSServer.py 8001 secure username:mysecret >>ws.log&`

Providing a user:password is optional, as well as using SSL/https. When the website is only accessible within your LAN, then the server can be used as plain http, by omitting the secure parameter. The following parameter formats are valid:

```shell
nohup python ExampleWSServer.py 8001 secure user:password >>ws.log&

#no username and password requested
nohup python ExampleWSServer.py 8000 secure >>ws.log&

#plain http, with optional port
nohup python ExampleWSServer.py 8002 >>ws.log&

#plain http, default port 8000
nohup python ExampleWSServer.py >>ws.log&
```
