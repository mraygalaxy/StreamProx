
Streaming Inspecting Server Proxy in Twisted
============================================


StreamProx is a little toolkit for building server proxies in Twisted.
A server proxy (reverse proxy) is a piece of software that accepts an
incoming connection, examines the traffic on it and makes a decision
about where to route it.  The inspecting server proxy buffers the
first few packets of the connection to help it make its decision.  It
then initiates the proxied connection and forwards the buffered
packets.

![StreamProx Overview](/doc/streamprox-local.png?raw=true)


# Why did I write this? #

I was experimenting with WebSockets protocols, and streaming media
protocols of my own design.  These experimental protocols were
changing quickly and were not necessarily stable.  I wanted to
construct a web site out of the proven Twisted Resource and Site
components for rendering the traditional parts of the site, and wanted
to mount the streaming parts on their own protocol handlers.  I wanted
everything to run off of port 80.  I wanted the code to copy data only
as much as necessary.

I didn't find anything that did what I wanted.


# Quick Introduction #

StreamProx defines a Twisted Protocol named BufferingProxyServer.
This server listens for incoming connections.  When one arrives, it
starts buffering the arriving packets in a PacketBuffer until enough
packets have been received to make a decision.  For simple HTTP
protocols this is either until one line is collected, or until all of
the HTTP headers have been been collected.

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
  the packets back and forth between the original client and
  destination until the connections are closed.
  
![StreamProx Overview](/doc/streamprox-remote.png?raw=true)

# Websockets #

The examples in this repo show how to use txWS or Autobahn alongside
twisted.web.resource.  StreamProx makes it possible to map your
WebSockets to the same URL space as your Resources by reserving a
prefix of the URL tree for your Websockets connections.  StreamProx
also allows you to map a remote Websockets resource into your URL
space.


# Inspirations #
  
Twisted ships with two standard components that are related to this
project.

- PortForward listens on a local port for an incoming connection and
  connects it to a remote service.  It does not examine the contents
  of the packets, nor does it make a make a dispatching decision
  amongst multiple destinations.

- Twisted.web.proxy has a number of components for forward and reverse
  proxying of HTTP requests.  As of this writing, I do not believe
  these components can bi-directionally proxy streaming protocols.
  
