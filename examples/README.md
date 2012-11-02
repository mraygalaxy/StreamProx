
StreamProx Examples
===================

This directory contains just a few examples that exercise the
StreamProx toolkit basic functionality.


# example4.py #

This example maps the URL space into three components.

    /foo - a twisted.web server
    /bar - a twisted.web server
    /google - a connection to a remote service
    
The "/foo" space is HTTPBasicAuthentication password protected.  The
user and password are "tom" and "tom".  The "/bar" space is handled by
a different server.  It is not password protected.  Any URL that
starts with "/google" is connected to google.

Using CURL, you can verify that the three different sites are
dispatched to as you expect.

    curl -u tom:tom http://localhost:8080/foo
    curl http://localhost:8080/bar
    curl http://localhost:8080/google/blech
    
Using a web-browser you can observe some interesting effects.  If you access
the URL "http://localhost:8080/foo", you will be challenged to enter
the username and password for this web site.  This is an example of a
bi-directional communication through the proxy between the "/foo" site
and your browser.

If you access a URL beginning with "/google", your browser will remain
connected to google.  Your browser is using HTTP/1.1, which will keep
a TCP connection open to handle multiple requests.  Notice that if you
visit a "/google" URL and then visit the "/bar" URL, you will remain
connected to Google.  This may or may not be what you expect.

StreamProx manages connections and not HTTP requests.


# tom2.py - txWS and Resource together #

This example shows how to mount a txWS websocket handler and a
traditional twisted.web.resource.  The URL space is divided into these
components.

    /demo  - a twisted.web server
    /websocketdemo - a txWS websocket server
    
The "/demo" server contains a single page of HTML.  It sets up a
connection to our websocket server.  The websocket application serves
a stream of JPGs to the browser along with a timestamp.  The browser
renders the JPGs and timestamp.

This is basically a demonstration of motion-JPEG over websockets.


# echo.py - Remote websocket at echo.websocket.org (Kaazing) #

This example shows how to forward a local websocket request to a
remote server.  The URL space is divided into these components.

    /demo  - a local twisted.web server
    /      - a remote connection to echo.websocket.org

The "/demo" server contains a single page of HTML.  It reproduces the
example page at http://www.websocket.org/echo.html.

This demonstration illustrates an interesting capability of the
StreamProx dispatcher framework.  The outgoing buffered packets are
modified prior to be forwarded to echo.websocket.org.  The server at
echo.websocket.org requires the Host: header to match:

    Host: echo.websocket.org
    
However, when we point our websocket-enabled browser to
http://localhost:8080/demo, it will initiate a websocket connection
with the Host header set this way.

    Host: localhost:8080
    
The echo demo defines a rewriting dispatcher that fixes up the Host:
header.



