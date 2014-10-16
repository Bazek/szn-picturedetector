#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# DESCRIPTION
#   Konfigurace pro trenovani neuronovych siti
#

from rpc_backbone.decorators import rpcStatusDecorator, MySQL_master, MySQL_slave
from lib.backend import Backend
from picturedetector import util
from dbglog import dbg
import os.path
import fastrpc

class SolverConfigBackend(Backend):
    @rpcStatusDecorator('solver_config.get', 'S:i')
    @MySQL_slave
    def get(self, id):
        file_path = self.getPath(id, bypass_rpc_status_decorator=True)
        solver_config = util.readProtoSolverFile(file_path)
        return fastrpc.Binary(str(solver_config))
    #enddef
    
    @rpcStatusDecorator('solver_config.getString', 'S:i')
    @MySQL_slave
    def getString(self, id):
        file_path = self.getPath(id, bypass_rpc_status_decorator=True)
        file = open(file_path, 'r')
        if not file:
            raise self.ProcessException("Nemuzu otevrit solver soubor (" + file_path + ")!")
        file_content = file.read()
        return file_content;
    #enddef

    @rpcStatusDecorator('solver_config.save', 'S:s')
    @MySQL_master
    def save(self, id, file_content):
        file_path = self.getPath(id, bypass_rpc_status_decorator=True)
        file = open(file_path, 'w')
        if not file:
            raise self.ProcessException("Nemuzu vytvorit solver soubor (" + file_path + ")!")
        file.write(file_content)
        file.close()
        
        return True
    #enddef

    @rpcStatusDecorator('solver_config.delete', 'S:i')
    @MySQL_master
    def delete(self, id):
        file_path = self.getPath(id, bypass_rpc_status_decorator=True)
        if os.path.isfile(file_path):
            os.remove(file_path)
        else:
            dbg.log("Solver config soubor neexistuje (" + file_path +")", INFO=3)
            return False
        #endif
        
        return True
    #enddef
    
    @rpcStatusDecorator('solver_config.getPath', 'S:i')
    @MySQL_master
    def getPath(self, id):
        base = self.config.solver.base_path
        prefix = self.config.solver.file_prefix
        extension = self.config.solver.file_extension
        
        return os.path.join(base, prefix + str(id) + extension)
    #enddef
    
#endclass