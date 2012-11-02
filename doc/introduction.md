
Streaming Server Proxy components in Twisted
============================================


StreamProx is a little toolkit for building server proxies in Twisted.
A server proxy is a piece of software that accepts an incoming
connection, examines the traffic on it and makes a decision about
where to route it to.  The inspecting server proxy buffers the first
few packets of the connection to help it make its decision.  It then
initiates the proxied connection and forwards the buffered packets.

![StreamProx Overview](streamprox-overview.png?raw=true)


# Why did I write this? #

I was experimenting with WebSockets protocols, and streaming media
protocols of my own design.  These experimental protocols were
changing quickly and were not necessarily stable.  I wanted to
construct a web site out of the proven Twisted Resource and Site
components for rendering the tranditional parts of the site, and
wanted to mount the streaming parts on their own protocol handlers.  I
wanted everything to run off of port 80.  I wanted the result to avoid
copying buffered data as much as possible.


# Quick Introduction #

StreamProx defines a Twisted Protocol named BufferingProxyServer.
This server listens for incoming connections.  When one arrives, it
starts buffering the arriving packets in a PacketBuffer until enough
packets have been received to make a decision.  For simple HTTP
protocols this is until one line was collected, or until all of the
HTTP headers had been collected.

Once these packets have been stored, a decision is made: should this
connection be connected to an in-process Protocol, or should this
connection be forwarded to an out-of-process server?

- If the destination is in-process, StreamProx creates an instance of
  the destination Protocol and replays the buffered packets.  It then
  connects the original client to the destination protocol and gets
  out of the way.

- If the destination is out-of-process, StreamProx creates a proxy
  client to connect to the remote service.  It then replays the
  buffered packets and enters a copy mode where it continually copies
  the packets back and forth between the original client and until the
  connections are dropped.


