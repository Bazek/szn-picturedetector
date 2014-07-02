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
        self.pictures = PicturesConfig(self.parser)
    #enddef
#endclass


class PicturesConfig(object):
    """ Parse pictures section """
    def __init__(self, parser, section='pictures'):
        self.base_path = parser.get(section, 'BasePath')
        self.learning_set_paths = {
            "training-true":    parser.get(section, 'TrainingTruePath'),
            "training-false":   parser.get(section, 'TrainingFalsePath'),
            "validation":       parser.get(section, 'ValidationPath'),
            "testing":          parser.get(section, 'TestingPath'),
        }
    #enddef
#endclass


class SomeConfig(object):
    """ Parse some section """
    def __init__(self, parser, section='some-section'):
        self.some_value = parser.get(section, 'SomeValue', "default")
    #enddef
#endclass
