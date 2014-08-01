#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# DESCRIPTION
#   Backend for picturedetector
#


from dbglog import dbg
from datetime import datetime
from rpc_backbone.decorators import MySQL_master


class BackendException(Exception):
    pass
#endclass


class Backend(object):
    """
    Bazova trida pro praci s backendem
    """

    def __init__(self, server):
        # Config object holding all information
        self.server = server
        self.config = server.globals.config
    #enddef

    def _getFilter(self, filterDict, valuesDict, prefix="WHERE", separator=" AND ", empty=True):
        """ Pomocna funkce pro sestavovani klauzuli pomoci parametru """
        values = []
        for key, val in valuesDict.items():
            if key in filterDict:
                value = filterDict[key]
                values.append(value)
            else:
                status, statusMessage = 300, "Unknown value %s" % key
                raise BackendException(status, statusMessage)
            #endif
        #endfor

        FILTER = separator.join(values)
        if not FILTER and not empty:
            status, statusMessage = 300, "No data"
            raise BackendException(status, statusMessage)
        elif FILTER:
            FILTER = "%s %s" % (prefix, FILTER)
        #endif
        return FILTER
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

