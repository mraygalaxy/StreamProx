
Inspecting Reverse Proxy Components in Twisted
============================================


StreamProx is a little toolkit for building server proxies in Twisted.
A server proxy (reverse proxy) is a piece of software that accepts an
incoming connection, examines the traffic on it and makes a decision
about where to route it.  The inspecting server proxy buffers the
first few packets of the connection to help it make its decision.  It
then initiates the proxied connection and forwards the buffered
packets.

StreamProx lets you organize a website as a collection of Protocol and
Client handlers, some of which are local, and somo of which may be
remote. 

