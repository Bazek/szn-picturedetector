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
        self.solver = SolverConfig(self.parser)
        self.deploy = DeployConfig(self.parser)
        self.train_val = TrainModelConfig(self.parser)
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
#endclass

class ClassifyConfig(object):
    """ Parse classify section """
    def __init__(self, parser, section='classify'):
        self.number_of_categories = parser.get(section, 'NumberOfCategories', 0)
    #enddef
#endclass

class SolverConfig(object):
    """ Parse solver section """
    def __init__(self, parser, section='solver'):
        self.base_path = parser.get(section, 'BasePath', '/www/picturedetector/caffe/solvers')
        self.file_prefix = parser.get(section, 'FilePrefix', 'solver_config_')
        self.file_extension = parser.get(section, 'FileExtension', '.prototxt')
    #enddef
#endclass

class DeployConfig(object):
    """ Parse deploy section """
    def __init__(self, parser, section='deploy'):
        self.base_path = parser.get(section, 'BasePath', '/www/picturedetector/caffe/deploys')
        self.file_prefix = parser.get(section, 'FilePrefix', 'deploy_')
        self.file_extension = parser.get(section, 'FileExtension', '.prototxt')
    #enddef
#endclass

class TrainModelConfig(object):
    """ Parse trainmodel section """
    def __init__(self, parser, section='trainmodel'):
        self.base_path = parser.get(section, 'BasePath', '/www/picturedetector/caffe/trainmodels')
        self.file_prefix = parser.get(section, 'FilePrefix', 'trainmodel_')
        self.file_extension = parser.get(section, 'FileExtension', '.prototxt')
    #enddef
#endclass