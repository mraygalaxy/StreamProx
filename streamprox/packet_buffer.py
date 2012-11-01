################################################################
#
# StreamProx
#
################################################################

# The packet buffer stores, examines, and optionally re-writes itself
# prior to forwarding.  If too many packets are received, or the
# examination length is exceeded, an exception is thrown upon
# appending.
#
# Methods that parse the Packet Buffer ...

from twisted.python import log
import re

class PacketBuffer:

    MAXPACKETS = 5              # maximum number of packets to examine
    MAXBYTES = 9999             # maximum amount of data to examine
    delimiter = "\r\n"          # buffer until we find this
    debug = True                # make me verbose

    def __init__(self):
        self.bufdata = [ ]

    # Append data to the buffer.

    def append(self, data):
        self.bufdata.append(data)

    # We buffer until we find the first delimiter, or until we exceed
    # MAXPACKETS or MAXDATA.

    def doneBuffering(self):
        # see if we've buffered too many packets
        if len(self.bufdata) > self.MAXPACKETS:
            if self.debug:
                log.msg("done buffering because MAXPACKETS:%d" % len(self.bufdata))
            return True

        # see if we've buffered too many bytes
        totalbytes = 0
        for data in self.bufdata:
            totalbytes += len(data)

        if totalbytes > self.MAXBYTES:
            if self.debug:
                log.msg("done buffering because MAXBYTES:%d" % totalbytes)
            return True

        # see if we've encountered the delimiter
        data = "".join(self.bufdata)
        if data.find(self.delimiter) != -1:
            if self.debug:
                log.msg("found delimiter")
            return True
        else:
            return False


        
        
