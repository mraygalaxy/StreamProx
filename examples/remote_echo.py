# Proxy the Websocket Echo test to a remote Kaazing server
#
# Sheffler 2012

import sys
import time
import os
import re

from twisted.internet import reactor
from twisted.internet.protocol import Protocol, Factory
from twisted.web import server, resource
from twisted.python import log

from streamprox.proxy import BufferingProxyFactory
from streamprox.packet_buffer import PacketBuffer
from streamprox.dispatcher import ExampleDispatcher

#
# This is an example websocket webpage taken from http://www.websocket.org/echo.html.
#

PAGETEXT = """

<!DOCTYPE html>
<meta charset="utf-8" />

<title>WebSocket Test</title>

<script language="javascript" type="text/javascript">
  // var wsUri = "ws://echo.websocket.org/";
  var wsUri = "ws://localhost:8080/";
  var output;

  function init() {
    output = document.getElementById("output");
    testWebSocket();
   }

  function testWebSocket() {
    websocket = new WebSocket(wsUri);
    websocket.onopen = function(evt) { onOpen(evt) };
    websocket.onclose = function(evt) { onClose(evt) };
    websocket.onmessage = function(evt) { onMessage(evt) };
    websocket.onerror = function(evt) { onError(evt) };
   }

  function onOpen(evt) {
    writeToScreen("CONNECTED");
    doSend("WebSocket rocks");
  }

  function onClose(evt) {
    writeToScreen("DISCONNECTED");
  }

  function onMessage(evt) {
    writeToScreen('<span style="color: blue;">RESPONSE: ' + evt.data+'</span>');
    websocket.close();
   }

  function onError(evt) {
    writeToScreen('<span style="color: red;">ERROR:</span> ' + evt.data);
  }

  function doSend(message) {
    writeToScreen("SENT: " + message);  websocket.send(message);
  }

  function writeToScreen(message) {
    var pre = document.createElement("p");
    pre.style.wordWrap = "break-word";
    pre.innerHTML = message; output.appendChild(pre);
   }

  window.addEventListener("load", init, false);
  </script>
  <h2>WebSocket Test</h2>  <div id="output"></div>

  </html>

"""

#
# The Demo resource simply renders the web page.
#

class DemoResource(resource.Resource):

    def render_GET(self, request):

        request.setHeader('content-type', "text/html")
        return PAGETEXT


#
# This dispatcher connects the path "/" to a remote client.  If the path is "/" it also modifies the outgoing
# data packets to correct the Host: header.
#

class RewritingExampleDispatcher(ExampleDispatcher):

    # Connect to the remote server

    def connectClient(self, clientCreator):
        log.msg("connectClient: %s/%s/%s" % (self.verb, self.path, self.version))
        
        if self.path == "/":
            log.msg("Contacting echo.websocket.org")
            reactor.connectTCP("echo.websocket.org", 80, clientCreator)
            return True

        return False


    # We have to rewrite the Host: header to match what echo.websocket.org expects

    def outgoingData(self):

        if self.path == "/":
            # Replace the Host: header
            x = re.sub(r'Host: (\S*)', 'Host: echo.websocket.org', self.bufdata[0])
            log.msg("replace:%s" % x)
            self.bufdata[0] = x

        return self.bufdata


# Open a browser to http://localhost:8080/demo
# It will render the local demo page and proxy a websocket to a remote host: echo.websocket.org

if __name__ == '__main__':
    log.startLogging(sys.stdout)

    # The local website serves the webpage
    root = resource.Resource()
    root.putChild("demo", DemoResource())
    site = server.Site(root)
    
    # Customize the default packet buffer class to look for the entire header chunk
    PacketBuffer.delimiter = "\r\n\r\n"

    # Construct our proxy and configure it
    factory = BufferingProxyFactory()
    factory.protocol.buffer_factory = PacketBuffer

    # Route /demo urls to our local website
    ExampleDispatcher.prefix1 = "/demo"
    ExampleDispatcher.site1 = site

    # Install our custom dispatcher to connect to the remote WebSocket server
    factory.protocol.dispatcher_factory = RewritingExampleDispatcher

    reactor.listenTCP(8080, factory)
    reactor.run()

