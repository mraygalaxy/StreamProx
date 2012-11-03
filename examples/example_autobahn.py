# Render a resource page that connects to an autobahn websocket
#
# Sheffler 2012

import sys
import time
import os
import binascii

from twisted.internet import reactor
from twisted.internet.protocol import Protocol, Factory
from twisted.web import server, resource
from twisted.python import log

from autobahn.websocket import WebSocketServerFactory, WebSocketServerProtocol

from streamprox.proxy import BufferingProxyFactory
from streamprox.packet_buffer import PacketBuffer
from streamprox.dispatcher import ExampleDispatcher


PAGETEXT = """
<html>
   <head>
      <script type="text/javascript">
         var webSocket = null;
         window.onload = function() {
 
            webSocket = new WebSocket("ws://localhost:8080");
 
            webSocket.onmessage = function(e) {
               console.log("Got echo: " + e.data);
            }
         }
      </script>
   </head>
   <body>
      <h1>WebSocket Echo Client</h1>
      <button onclick='webSocket.send("Hello, world!");'>
         Send Hello
      </button>
   </body>
</html>

"""

#
# This is a simple twisted resource that renders the demo web page
#

class DemoResource(resource.Resource):

    def render_GET(self, request):

        request.setHeader('content-type', "text/html")
        return PAGETEXT


 
#
# This is an Autobahn echo protocol
#
 
class EchoServerProtocol(WebSocketServerProtocol):
 
   def onMessage(self, msg, binary):
      self.sendMessage(msg, binary)
 
#
# To run the demo:
#
# Open a WebSocket-enabled browser to http://localhost:8080/demo
#   - open the Javascript console to see the echo text
#   - click the [Send] button
#
 
if __name__ == '__main__':
    log.startLogging(sys.stdout)

    # Set up an Autobahn echo server
    ws = WebSocketServerFactory("ws://localhost:8080", debug = True)
    ws.protocol = EchoServerProtocol

    root = resource.Resource()
    root.putChild("demo", DemoResource())
    site = server.Site(root)

    factory = BufferingProxyFactory()
    factory.protocol.buffer_Factory = PacketBuffer

    # Route /demo urls to our website
    ExampleDispatcher.prefix1 = "/demo"
    ExampleDispatcher.site1 = site

    # Route "/" to the Autobahn websocket server
    ExampleDispatcher.prefix2 = "/"
    ExampleDispatcher.site2 = ws

    factory.protocol.dispatcher_factory = ExampleDispatcher

    reactor.listenTCP(8080, factory)
    reactor.run()

