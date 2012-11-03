################################################################
#
# StreamProx
#
# Stream a series of JPG images over a websocket to a client.
#
################################################################

import sys
import time
import os
import binascii

from twisted.internet import reactor
from twisted.internet.protocol import Protocol, Factory
from twisted.web import server, resource
from twisted.python import log
from twisted.python.filepath import FilePath

from streamprox.proxy import BufferingProxyFactory
from streamprox.packet_buffer import PacketBuffer
from streamprox.dispatcher import ExampleDispatcher


PAGETEXT = """

<html>


<script>

function main() {

  timestamp = document.getElementById("timestamp");
  liveimage = document.getElementById("liveimage");

  ws = new WebSocket("ws://" + document.location.hostname + ":8080/websocketdemo");

  ws.onmessage = function(evt) {
    // Parse the return JSON data
    jdata = JSON.parse(evt.data);
    console.log("JDATA");
    console.log(jdata);

    // Update the HTML elements with the JSON data
    timestamp.innerHTML = jdata.timestamp;
    liveimage.src = "data:image/jpeg;base64," + jdata.imgdata;
  };

  ws.onopen = function() {
    ws.send("get it started");
  }
}

window.onload = main;

</script>

<body>

   <br>

<div>
  <img id="liveimage" src="" width="320" height="240" border="1">
  <div style="position:absolute; left: 20px; top:240px;">
    <span id="timestamp" style="font-family:Arial; font-weight:Bold; font-size:20px; color:white; text-shadow:0 0 2px #777;">0000</span>
  </div>
</div>

</body>

</html>

"""

class DemoResource(resource.Resource):

    def render_GET(self, request):

        request.setHeader('content-type', "text/html")
        return PAGETEXT


class JPGPipeProtocol(Protocol):

    debug = True

    def connectionMade(self):
        self.isconnected = True
        if self.debug:
            log.msg("connectionMade")
        Protocol.connectionMade(self)

    def connectionLost(self, reason):
        self.isconnected = False
        if self.debug:
            log.msg("connectionLost")
        Protocol.connectionLost(self, reason)

    def sendLine(self, line):
        if self.debug:
            log.msg("sendLine")
        self.transport.write(line)

    def dataReceived(self, bytes):
        if self.debug:
            log.msg("dataReceived")
        # initiate the never ending loop
        self.dateloop()

    def dateloop(self):
        imgdir = FilePath("images")
        imgs = imgdir.globChildren("*.jpg")  # open/read
        i = 0

        def emit(i):
            index = i % len(imgs)
            data = imgs[index].open().read()
            data = binascii.b2a_base64(data).strip()
            timestamp = time.strftime("%D %H:%M:%S")

            jdata = '{"timestamp" : "%s", "imgdata" : "%s" }' % (timestamp, data)

            if self.isconnected:
                self.sendLine(jdata)
                reactor.callLater(1.0, emit, i+1)

        emit(i)


class JPGPipeFactory(Factory):

    def __init__(self):
        self.protocol = JPGPipeProtocol



if __name__ == '__main__':
    log.startLogging(sys.stdout)

    from txws import WebSocketFactory
    ws = WebSocketFactory(JPGPipeFactory())

    root = resource.Resource()
    root.putChild("demo", DemoResource())
    site = server.Site(root)

    factory = BufferingProxyFactory()
    factory.protocol.buffer_factory = PacketBuffer

    # Route /demo urls to our website
    ExampleDispatcher.prefix1 = "/demo"
    ExampleDispatcher.site1 = site

    # Route /demowebsocket urls to the websocket handler
    ExampleDispatcher.prefix2 = "/websocketdemo"
    ExampleDispatcher.site2 = ws

    factory.protocol.dispatcher_factory = ExampleDispatcher

    reactor.listenTCP(8080, factory)
    reactor.run()

