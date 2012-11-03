#!/usr/bin/env python
################################################################
#
# StreamProx
#
################################################################

import sys
import re
import time

# Twisted imports
from zope.interface import implements

from twisted.internet import protocol
from twisted.python import log

from twisted.web import server, resource
from twisted.web.server import NOT_DONE_YET
from twisted.web.static import File
from twisted.internet import reactor
from twisted.application import internet
from twisted.python import log

################################################################

from twisted.cred import portal
from twisted.cred import checkers
from twisted.web.guard import BasicCredentialFactory
from twisted.web.guard import HTTPAuthSessionWrapper
from twisted.cred import portal
from twisted.web.resource import IResource

from streamprox.proxy import BufferingProxyFactory
from streamprox.packet_buffer import PacketBuffer
from streamprox.dispatcher import ExampleDispatcher

class FooResource(resource.Resource):

    def render_GET(self, request):

        log.msg("render ME!")
        log.msg(str(request))
        # tell the client to close the connection after this request
        request.setHeader("Connection", "close")
        request.write("FOO!")
        request.finish()
        return True


class BarResource(resource.Resource):

    def render_GET(self, request):

        log.msg("render ME!")
        log.msg(str(request))
        # tell the client to close the connection after this request
        request.setHeader("Connection", "close")
        request.write("BAR!")
        request.finish()
        return True


class HttpPasswordRealm(object):

    implements(portal.IRealm)

    def __init__(self, myresource):
        self.myresource = myresource
    
    def requestAvatar(self, user, mind, *interfaces):
        if IResource in interfaces:
            # myresource is passed on regardless of user
            return (IResource, self.myresource, lambda: None)
        raise NotImplementedError()


# Example that routes to two internal and one external service:
#
# 1) curl -u tom:tom http://localhost:8080/foo
# 2) curl http://localhost:8080/bar
# 3) curl http://localhost:8080/google/blech

def main():

    # The 'foo' site is protected by a password
    foo_root = resource.Resource()
    foo_root.putChild("foo", FooResource())

    realm = HttpPasswordRealm(foo_root)
    checker = checkers.InMemoryUsernamePasswordDatabaseDontUse()
    checker.addUser("tom", "tom")
    my_portal = portal.Portal(realm, [checker])
    credentialFactory = BasicCredentialFactory("StreamProx")
    protected_foo_root = HTTPAuthSessionWrapper(my_portal, [credentialFactory])

    # The 'bar' site is unprotected
    bar_root = resource.Resource()
    bar_root.putChild("bar", BarResource())

    # Create two web sites
    site1 = server.Site(protected_foo_root)
    site2 = server.Site(bar_root)

    # Create a StreamProx server.  Customize its packet buffer and dispatcher.
    factory = BufferingProxyFactory()
    factory.buffer_factory = PacketBuffer
    ExampleDispatcher.site1 = site1
    ExampleDispatcher.site2 = site2
    factory.dispatcher_factory = ExampleDispatcher

    reactor.listenTCP(8080, factory)
    
    log.startLogging(sys.stdout)
    reactor.run()

if __name__ == "__main__":
    main()
    
