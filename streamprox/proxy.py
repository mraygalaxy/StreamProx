################################################################
#
# StreamProx
#
################################################################

# Twisted imports
from zope.interface import implements

from twisted.internet import protocol
from twisted.internet import reactor
from twisted.python import log

from packet_buffer import PacketBuffer
from router import BaseRouter

# A proxy forwards data written to it to its peer transport.

class Proxy(protocol.Protocol):

    peer = None
    debug = True

    def setPeer(self, peer):
        self.peer = peer

    def connectionLost(self, reason):
        if self.peer is not None:
            if self.debug:
                log.msg("loseConnection")
            self.peer.transport.loseConnection()
            self.peer = None
        else:
            if self.debug:
                log.msg("Unable to connect to peer: %s" % (reason,))

    def dataReceived(self, data):
        if self.debug:
            log.msg("<<< %s proxying:%d" % (self, len(data)))
            # log.msg("<<< %s" % data)
        self.peer.transport.write(data)


# A proxy client is an instance of a protocol that has had its peer
# set after creation.  When we get connected, we set the peer to
# ourselves.

class ProxyClient(Proxy):

    debug = True

    def connectionMade(self):
        if self.debug:
            log.msg("ProxyClient connectionMade: %s" % (self,))
        self.peer.setPeer(self)


# A replaying proxy client has also been initialized with buffer data
# to be shoved into the peer when the connection is made.

class ReplayingProxyClient(ProxyClient):

    bufdata = None

    def connectionMade(self):
        ProxyClient.connectionMade(self)

        # re-play the buffered data received
        if not self.bufdata:
            log.err("ReplayingProxyClient has no data")

        self.replay_and_continue(0, self.bufdata)

    # When one of us is built, our factory passes us the bufdata that
    # we will replay upon connection to a remote client by using this
    # method.

    def setBufdata(self, bufdata):
        self.bufdata = bufdata

    # The replay method plays catch-up by replaying the received data.
    # It inserts some 'slip' so the reactor can interleave other
    # operations.

    def replay_and_continue(self, index, bufdata):
        if self.debug:
            log.msg("ReplayingProxyClient: replay %d" % index)

        if index < len(bufdata):
            self.peer.dataReceived(bufdata[index])
            reactor.callLater(0.0, self.replay_and_continue, index+1, bufdata)

        else:
            if self.debug:
                log.msg("ReplayingProxyClient: replay done")

            # Wire this and the peer transport together to enable
            # flow control (this stops connections from filling
            # this proxy memory when one side produces data at a
            # higher rate than the other can consume).

            self.transport.registerProducer(self.peer.transport, True)
            self.peer.transport.registerProducer(self.transport, True)

            # We're connected, everybody can read to their hearts content.
            self.peer.transport.resumeProducing()


# A single instance of the proxy client factory is created for each
# connection that results in a remote client.  The "inWaiting" fields
# are data that are held by the factory and passed to the client at
# the appropriate time.

class ReplayingProxyClientFactory(protocol.ClientFactory):

    protocol = ReplayingProxyClient
    buildProtocolCounter = 0    # for the assertion
    debug = True

    # Hold onto the peer that the client will attach to
    def setPeerInWaiting(self, peer):
        self.peerInWaiting = peer

    # Hold onto the bufdata that will be fed into the client
    def setBufdataInWaiting(self, bufdata):
        self.bufdataInWaiting = bufdata

    def buildProtocol(self, *args, **kw):

        # This factory must only be used ONCE to create a protocol,
        # since it holds the 'peer' and 'bufdata' of that protocol in
        # waiting.  We enforce that assertion here.

        self.buildProtocolCounter += 1
        assert self.buildProtocolCounter == 1

        if self.debug:
            log.msg("%s buildProtocol" % (self,))

        # Invoke super, pass inWaiting params on to protocol instance, p
        p = protocol.ClientFactory.buildProtocol(self, *args, **kw)
        p.setPeer(self.peerInWaiting)
        p.setBufdata(self.bufdataInWaiting)
        return p

    def clientConnectionFailed(self, connector, reason):
        self.peerInWaiting.transport.loseConnection()


class BufferingProxyServer(Proxy):

    """This proxy server examines the first few packets it receives
    and then makes a decision about which client to hand the
    conversation off to."""

    debug = True
    buffer_factory = PacketBuffer
    router_factory = BaseRouter

    def connectionMade(self):
        addr = self.transport.getPeer()
        if self.debug:
            log.msg("%s connectionMade from %s" % (self, addr))

        # set initial buffering state
        self.pbuf = self.buffer_factory()
        self.copyMode = False   # after we buffer, we enter copyMode
        self.router = None

    # The proxy server buffers some amount of data, and then
    # asks the transport to pause while it sets up a client.

    def dataReceived(self, data):
        if self.debug:
            log.msg(">>> %s proxying %d" % (self, len(data)))
            # log.msg(">>> %s" % data)

        if self.copyMode:
            # copy mode occurs after the packet buffer is done examining the head
            self.peer.transport.write(data)

        else:
            self.pbuf.append(data)

            if self.pbuf.doneBuffering():
                self.copyMode = True
                self.transport.pauseProducing()

                # Initialize a router with the packets received so far
                self.router = self.router_factory(self.pbuf.bufdata)

                # Ask the router how to proceed
                if self.router.isLocal():
                    self.proceed_as_protocol_wrapper()
                else:
                    self.proceed_as_forwarder()

    # The desired location is a local (in-process) factory.  We will
    # create a protocol instance of that factory, replay the buffered
    # data into it, and then resume our transport producing into the
    # new protocol instance.

    def proceed_as_protocol_wrapper(self):
        # look up the factory that this connection should go to
        f = self.router.localFactory()

        if f == None:
            log.msg("Cannot connect to local factory:%s" % f)
            self.transport.loseConnection()
            return

        # construct a protocol instance
        addr = self.transport.getPeer()
        p = f.buildProtocol(addr)

        # connect our transport to the protocol instance
        self.transport.protocol = p
        p.makeConnection(self.transport) # TOM: this is basically "p.transport = self.transport"

        # replay buffered data into the protocol instance, then resume with our producer
        self.replay_and_continue(p, 0, self.router.outgoingData())

    # The desired location is a remote (out-of-process) socket.  Set
    # up a clientFactory that creates a ReplayingProxyClient connected
    # to the remote.

    def proceed_as_forwarder(self):
        # create a client proxy. It will create the protocol and replay the data
        self.client = ReplayingProxyClientFactory()
        self.client.setPeerInWaiting(self)
        self.client.setBufdataInWaiting(self.router.outgoingData())

        # connect the client to the remote service.  The bufdata will be replayed upon connect.
        success = self.router.connectClient(self.client)

        if not success:
            self.transport.loseConnection()


    # Replay the collected buffer data into the protocol instance p.
    # Then continue by making our transport's producer, the protocol's
    # transport and resume producing.

    def replay_and_continue(self, p, index, bufdata):
        if index < len(bufdata):
            p.dataReceived(bufdata[index])
            reactor.callLater(0.0, self.replay_and_continue, p, index+1, bufdata)
            # self.replay_and_continue(p, index+1, bufdata)

        else:
            # TOM: 2012-09-07: unnecessary
            # self.transport.registerProducer(p.transport, True)
            self.transport.resumeProducing()


class BufferingProxyFactory(protocol.Factory):
    """Factory for port forwarder."""

    protocol = BufferingProxyServer


