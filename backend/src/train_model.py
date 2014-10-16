#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# DESCRIPTION
#   Modely pro uceni neuronovych siti
#

from rpc_backbone.decorators import rpcStatusDecorator, MySQL_master, MySQL_slave
from lib.backend import Backend
from picturedetector import util
from dbglog import dbg
import os.path
import fastrpc

class TrainModelBackend(Backend):
    @rpcStatusDecorator('train_model.get', 'S:i')
    @MySQL_slave
    def get(self, id):
        file_path = self.getPath(id, bypass_rpc_status_decorator=True)
        model = util.readProtoLayerFile(file_path)
        return fastrpc.Binary(model)
    #enddef
    
    @rpcStatusDecorator('train_model.getString', 'S:i')
    @MySQL_slave
    def getString(self, id):
        file_path = self.getPath(id, bypass_rpc_status_decorator=True)
        file = open(file_path, 'r')
        if not file:
            raise self.ProcessException("Nemuzu otevrit train model soubor (" + file_path + ")!")
        file_content = file.read()
        return file_content;
    #enddef

    @rpcStatusDecorator('train_model.save', 'S:s')
    @MySQL_master
    def save(self, id, file_content):
        file_path = self.getPath(id, bypass_rpc_status_decorator=True)
        file = open(file_path, 'w')
        if not file:
            raise self.ProcessException("Nemuzu vytvorit train model soubor (" + file_path + ")!")
        file.write(file_content)
        file.close()
        
        return True
    #enddef

    @rpcStatusDecorator('train_model.delete', 'S:i')
    @MySQL_master
    def delete(self, id):
        file_path = self.getPath(id, bypass_rpc_status_decorator=True)
        if os.path.isfile(file_path):
            os.remove(file_path)
        else:
            dbg.log("Train model soubor neexistuje (" + file_path +")", INFO=3)
            return False
        #endif
        
        return True
    #enddef
    
    @rpcStatusDecorator('train_model.getPath', 'S:i')
    @MySQL_master
    def getPath(self, id):
        base = self.config.trainmodel.base_path
        prefix = self.config.trainmodel.file_prefix
        extension = self.config.trainmodel.file_extension
        
        return os.path.join(base, prefix + str(id) + extension)
    #enddef
    
#endclass