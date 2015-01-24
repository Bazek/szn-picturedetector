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
        self.neural_networks = NeuralNetworkConfig(self.parser)
        self.test = TestConfig(self.parser)
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
        self.init_networks_on_start = parser.get(section, 'InitNetworksOnStart', 0)
        self.keep_networks = parser.get(section, 'KeepNetworks', 1)
        self.caffe_snapshot_const = parser.get(section, 'CaffeSnapshotConst', '')
        self.caffe_snapshot_ext = parser.get(section, 'CaffeSnapshotExt', '.caffemodel')
        self.caffe_snapshot_state_ext = parser.get(section, 'CaffeSnapshotStateExt', '.solverstate')
    #enddef
#endclass

class ClassifyConfig(object):
    """ Parse classify section """
    def __init__(self, parser, section='classify'):
        self.number_of_categories = parser.get(section, 'NumberOfCategories', 0)
    #enddef
#endclass

class NeuralNetworkConfig(object):
    """ Parse neural networks section """
    def __init__(self, parser, section='neural-networks'):
        self.base_path = parser.get(section, 'BasePath', '/www/picturedetector/backend/data/neural-networks')
        self.temp_folder = parser.get(section, 'TempFolder', '/www/picturedetector/backend/data/temp')
        self.solver_file = parser.get(section, 'SolverFile', 'solver.prototxt')
        self.deploy_file = parser.get(section, 'DeployFile', 'deploy.prototxt')
        self.trainmodel_file = parser.get(section, 'TrainmodelFile', 'trainmodel.prototxt')
        self.classify_mean_file = parser.get(section, 'ClassifyMeanFile', 'meanfile.npy')
        self.logs_folder = parser.get(section, 'LogsFolder', 'logs')
        self.logs_name = parser.get(section, 'LogsName', 'log')
        self.log_timestamp_format = parser.get(section, 'LogTimestampFormat', '%Y%m%d_%H%M%S')
        self.log_extension = parser.get(section, 'LogExtension', '.log')
        self.snapshots_folder = parser.get(section, 'SnapshotsFolder', 'snapshots')
        self.snapshots_name = parser.get(section, 'SnapshotsName', 'snapshot')
        self.train_db_folder = parser.get(section, 'TrainDbFolder', 'imagenet_train_db')
        self.validation_db_folder = parser.get(section, 'ValidationDbFolder', 'imagenet_val_db')
        self.train_mean_file = parser.get(section, 'TrainMeanFile', 'mean_file_train.binaryproto')
        self.validation_mean_file = parser.get(section, 'ValidationMeanFile', 'mean_file_val.binaryproto')
    #enddef
#endclass

class TestConfig(object):
    """ Parse test section """
    def __init__(self, parser, section='test'):
        self.max_images = parser.get(section, 'MaxImages', 50)
    #enddef
#endclass

#endclass