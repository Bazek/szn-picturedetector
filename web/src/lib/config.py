#!/usr/bin/env python
#
# FILE             $Id:  $
#
# DESCRIPTION
#
# PROJECT
#
# AUTHOR           Petr Bartunek <petr.bartunek@firma.seznam.cz>
#
# Copyright (C) Seznam.cz a.s. 2014
# All Rights Reserved
#


from wsgi_publisher import configutils
from wsgi_publisher.configbase import ConfigBase

from dbglog import dbg
import ConfigParser




class Config(configutils.Config):

    def __init__(self, configFile):
        super(Config, self).__init__(configFile)
        self.flask = ConfigBase(self.parser, "flask", {
            "DEBUG":        {"type": ConfigBase.T_STRING,   "name": "DEBUG"},
            "SECRET_KEY":   {"type": ConfigBase.T_STRING,   "name": "SECRET_KEY"},
        })
        self.backend = configutils.ConfigBox(self.parser, "backend")
    #enddef

#endclass Config
