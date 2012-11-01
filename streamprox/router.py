################################################################
#
# StreamProx
#
################################################################

import re

from twisted.python import log
from twisted.internet import reactor

# A router examines a finalized packet buffer and makes the decision about
# whether to hand the connection off to a Local Factory or a Remote Service.

class BaseRouter:

    # Save, and possibly examine, the packet buffer
    def __init__(self, bufdata):
        self.bufdata = bufdata

    # Is this a local (in-process) service?
    def isLocal(self):
        pass

    # Return the local factory for the new connection
    def localFactory(self):
        pass

    # Connect the client up to a remote service
    def connectClient(self, clientCreator):
        # clientCreator: a twisted.internet.protocol.ClientFactory instance
        pass

    # Hand off the outgoing data to be sent to the factory or remote service
    def outgoingData(self):
        return self.bufdata



class ExampleRouter(BaseRouter):

    prefix1 = "/foo"
    site1 = None                # class constant: local site to route to

    prefix2 = "/bar"
    site2 = None

    def __init__(self, bufdata):
        BaseRouter.__init__(self, bufdata)

        # Parse the packet buffer and save the important components
        verb, path, version = parse_bufdata(self.bufdata)
        self.verb = verb
        self.path = path
        self.version = version
        

    def isLocal(self):
        
        if self.path.startswith(self.prefix1):
            return True
        elif self.path.startswith(self.prefix2):
            return True
        else:
            return False

    def localFactory(self):
        
        if self.path.startswith(self.prefix1):
            return self.site1
        elif self.path.startswith(self.prefix2):
            return self.site2
        else:
            return None

    def connectClient(self, clientCreator):
        # clientCreator: a twisted.internet.protocol.ClientFactory instance
        
        log.msg("connectClient: %s/%s/%s" % (self.verb, self.path, self.version))

        if re.match("/google", self.path):
            reactor.connectTCP("www.google.com", 80, clientCreator)
            return True

        return False


#
# Utility: Split an array-of-strings (buffer data) into
# VERB/PATH/VERSION components, ala HTTP first line.
#
        
def parse_bufdata(bufdata):
    verb = ""
    path = ""
    version = ""

    import re

    if bufdata == None:
        raise "empty buffer data handed to parse_bufdata"

    prefix, rest = "".join(bufdata).split('\r\n', 1)

    # log.msg("router: prefix:%s" % prefix)

    prefix = prefix.strip().rstrip()
    if prefix != "":
        verb, pathversion = prefix.split(" ", 1)
        pathversion = pathversion.strip().rstrip()
        if pathversion != "":
            path, version = pathversion.split(" ", 1)
    
        log.msg("router: verb/path/version::%s:%s:%s" % (verb, path, version))

        return verb, path, version
