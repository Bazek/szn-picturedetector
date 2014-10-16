#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# DESCRIPTION
#   Modely pro klasifikaci pomoci neuoronove site
#

from rpc_backbone.decorators import rpcStatusDecorator, MySQL_master, MySQL_slave
from lib.backend import Backend
from picturedetector import util
from dbglog import dbg
import os.path
import fastrpc

class ModelBackend(Backend):
    @rpcStatusDecorator('model.get', 'S:i')
    @MySQL_slave
    def get(self, id):
        file_path = self.getPath(id, bypass_rpc_status_decorator=True)
        model = util.readProtoLayerFile(file_path)
        return fastrpc.Binary(model)
    #enddef
    
    @rpcStatusDecorator('model.getString', 'S:i')
    @MySQL_slave
    def getString(self, id):
        file_path = self.getPath(id, bypass_rpc_status_decorator=True)
        file = open(file_path, 'r')
        if not file:
            raise self.ProcessException("Nemuzu otevrit deploy soubor (" + file_path + ")!")
        file_content = file.read()
        return file_content;
    #enddef

    @rpcStatusDecorator('model.save', 'S:s')
    @MySQL_master
    def save(self, id, file_content):
        file_path = self.getPath(id, bypass_rpc_status_decorator=True)
        dbg.log("MODEL PATH>> " + file_path, INFO=3)
        file = open(file_path, 'wb')
        if not file:
            raise self.ProcessException("Nemuzu vytvorit deploy soubor (" + file_path + ")!")
        file.write(file_content)
        file.close()
        
        return True
    #enddef

    @rpcStatusDecorator('model.delete', 'S:i')
    @MySQL_master
    def delete(self, id):
        file_path = self.getPath(id, bypass_rpc_status_decorator=True)
        if os.path.isfile(file_path):
            os.remove(file_path)
        else:
            dbg.log("Deploy soubor neexistuje (" + file_path +")", INFO=3)
            return False
        #endif
        
        return True
    #enddef
    
    @rpcStatusDecorator('model.getPath', 'S:i')
    @MySQL_master
    def getPath(self, id):
        base = self.config.deploy.base_path
        prefix = self.config.deploy.file_prefix
        extension = self.config.deploy.file_extension
        
        return os.path.join(base, prefix + str(id) + extension)
    #enddef
    
#endclass