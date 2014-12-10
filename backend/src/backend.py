#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
sys.path.insert(0, '/www/picturedetector/common/module/')

import metaserver.fastrpc as server

from rpc_backbone.wrappers import RpcServerWrapper
from rpc_backbone.utils import MySqlProxy
from szn_utils.configutils import DatetimeBuilder

from lib.config import Config
from lib.backend import Backend
from neural_network import NeuralNetworkBackend
from picture import PictureSetBackend, PictureBackend
from classify import ClassifyBackend
from learning_queue import LearningQueueBackend

def init(cfg):
    # Nacitani konfigurace
    server.globals.rawConfig = cfg
    CONFIG_PATH = '/www/picturedetector/backend/conf/'
    BACKEND_CONF = CONFIG_PATH + "backend.conf"
    BACKEND_DB_CONF = CONFIG_PATH + "backend.db.conf"
    server.globals.config = Config(BACKEND_CONF, BACKEND_DB_CONF)

    # Registrace vsech backendovych trid
    server.globals.rpcObjects = {
        'backend': Backend(server),
        'neural_network': NeuralNetworkBackend(server),
        'picture_set': PictureSetBackend(server),
        'picture': PictureBackend(server),
        'classify': ClassifyBackend(server),
        'learning_queue': LearningQueueBackend(server),
    }
    # Monitorovaci metoda
    server.registerHEADMethod(head)

    frpcCtrl = server.getFastrpcControl()
    #frpcCtrl.nativeBoolean = True
    frpcCtrl.datetimeBuilder = DatetimeBuilder()

    serverWrapper = RpcServerWrapper(server)
    serverWrapper.registerMethodsWithRPCDecorator(server.globals.rpcObjects.values())
#enddef


def childInit():
    server.globals.mysql = MySqlProxy(server.globals.rawConfig, "mysql-master", "mysql-slave")
    
    # Inicializace neuronovych siti
    server.globals.neuralNetworks = {}
    initNeuralNetworks()
#enddef


def destroy():
    pass
#enddef


def childDestroy():
    pass
#enddef


def logRotate():
    pass
#enddef


def head():
    return server.globals.rpcObjects['backend'].ping()
#enddef

def initNeuralNetworks():
    if server.globals.config.caffe.init_networks_on_start:
        neural_networks = server.globals.rpcObjects['neural_network'].list(bypass_rpc_status_decorator=True)
        for neural_network in neural_networks:
            if neural_network['auto_init']:
                neural_network_id = neural_network['id']
                classifier = server.globals.rpcObjects['classify'].createClassifier(neural_network_id)
                if 'data' in classifier:
                    server.globals.neuralNetworks[neural_network_id] = classifier['data']
                #endif
            #endif
        #endfor
    #endif
#enddef


