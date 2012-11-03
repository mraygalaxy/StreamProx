# I'm going to try to build a websocket server for simple stupid data
#
# 12-14-2011: finally a websocket demo in Twisted.
# A fixed subdirectory of images (images/*.jpg) is rendered one-per-second
# over a websocket along with a timestamp
#
# 10-31-2012: copied file "git/txWS/tom2.py" to StreamProx and began to modify.
# It formerly mounted a resource on 8082 and a websocket on 8080.  Lets see
# if they can both live on the same port.
#
# 10-31-2012: this basically worked!  And it seems to have some
# beneficial properties.  The browser opens up two persisitent
# connections: one for the http: scheme, and another for the ws:
# scheme.
# 

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

class TomResource(resource.Resource):

    def render_GET(self, request):

        request.setHeader('content-type', "text/html")
        return PAGETEXT


class TomProtocol(Protocol):

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


class TomFactory(Factory):

    def __init__(self):
        self.protocol = TomProtocol



if __name__ == '__main__':
    log.startLogging(sys.stdout)

    from txws import WebSocketFactory
    ws = WebSocketFactory(TomFactory())

    root = resource.Resource()
    root.putChild("demo", TomResource())
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

