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

        self.classify = ClassifyConfig(self.parser)
        self.pictures = PicturesConfig(self.parser)
        self.caffe = CaffeConfig(self.parser)
    #enddef
#endclass


class PicturesConfig(object):
    """ Parse pictures section """
    def __init__(self, parser, section='pictures'):
        self.base_path = parser.get(section, 'BasePath')
        self.training_path = parser.get(section, 'TrainingPath')
        self.validation_path = parser.get(section, 'ValidationPath')
        self.testing_path = parser.get(section, 'TestingPath')
        self.LEARNING_SETS = (self.training_path, self.validation_path, self.testing_path)
    #enddef
#endclass

class CaffeConfig(object):
    """ Parse caffe section """
    def __init__(self, parser, section='caffe'):
        self.gpu_mode = parser.get(section, 'GpuMode', 1)
    #enddef

class ClassifyConfig(object):
    """ Parse classify section """
    def __init__(self, parser, section='classify'):
        self.number_of_categories = parser.get(section, 'NumberOfCategories', 0)
    #enddef
#endclass
