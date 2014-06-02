#!/usr/bin/env python
# -*- coding: utf-8 -*-
#


from dbglog import dbg
from szn_utils.configutils import Config as BaseConfig


class Config(BaseConfig):
    """
    Object holding important attributes from config file
    """

    def __init__(self, configFile, passwdFile=None):
        super(Config, self).__init__(configFile, passwdFile)

        self.some_section = SomeConfig(self.parser)
    #enddef
#endclass


class SomeConfig(object):
    """ Parse some section """
    def __init__(self, parser, section='some-section'):
        self.some_value = parser.get(section, 'SomeValue', "default")
    #enddef
#endclass
