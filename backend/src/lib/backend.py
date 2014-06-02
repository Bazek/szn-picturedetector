#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# DESCRIPTION
#   Backend for picturedetector
#


from dbglog import dbg
from datetime import datetime
from rpc_backbone.decorators import MySQL_master


class Backend(object):
    """
    Bazova trida pro praci s backendem
    """

    def __init__(self, server):
        # Config object holding all information
        self.server = server
        self.config = server.globals.config
    #enddef

    def get_scheme(self):
        header = self.server.getInHeadersFor('X-Scheme')
        dbg.log('Header: %s', header, DBG=1)
        scheme = header[0][1].lower() if header else None
        if scheme not in ('http', 'https'):
            scheme = 'http'
        #endif
        return scheme
    #enddef

    @MySQL_master
    def ping(self):
        """
        Check response of simple query in master db
        """
        try:
            return self.session.execute('SELECT 0')[0]
        except:
            return 1
        #endtry
    #enddef
#endclass

