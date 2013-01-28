################################################################
# Copyright 2012 Sheffler
################################################################

try:
    import pkg_resources
    version = pkg_resources.require("StreamProx")[0].version
except:
    ## i.e. no setuptools or no package installed ...
    version = "?.?.?"


import packet_buffer
import dispatcher
import proxy
