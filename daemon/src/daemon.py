#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# AUTHOR           Petr Bartunek <petr.bartunek@firma.seznam.cz>
#
# Copyright (c) 2014 Seznam.cz, a.s.
# All rights reserved.
#


from szn_utils.daemon import DaemonConfig, Daemon
from dbglog import dbg

import MySQLdb.cursors
import MySQLdb.connections




class PicturedetectorDaemonConfig(DaemonConfig):

    class DbConnection(MySQLdb.connections.Connection):
        def __init__(self, parser, section="mysql-master"):
            super(PicturedetectorDaemonConfig.DbConnection, self).__init__(
                unix_socket = parser.get(section, "Socket"),
                host = parser.get(section, "Host"),
                user = parser.get(section, "User"),
                port = parser.getint(section, "Port"),
                passwd = parser.get(section, "Password"),
                db = parser.get(section, "Database"),
            )
        #enddef
    #endclass

    class CaffeConfig(object):
        """ Parse caffe section """
        def __init__(self, parser, section="caffe"):
            self.pidFile = parser.get(section, "PidFile")
        #enddef
    #endclass


    def reload(self):
        super(PicturedetectorDaemonConfig, self).reload()
        self.db = self.DbConnection(self.parser, "mysql-master")
        self.caffe = self.CaffeConfig(self.parser, "caffe")
    #enddef

#endclass




class PicturedetectorDaemon(Daemon):
    """ PicturedetectorDaemon Process """
    
    def __learningInProgress(self):
        # Zkontrolovat pidfile uciciho procesu
        # Pokud pidfile neexistuje, nebo je prazdny, vratime False
        # Pokud existuje, zkontrolujeme, ze dany proces bezi
        # Pokud proces nebezi, vyhodime vyjimku: raise self.ProcessException("Ucici proces nebezi!")
        # Pokud proces bezi, vratime True
        return None
    #enddef
    
    def __getNextNeuralNetwork(self):
        # Precteme z databaze dalsi neuronovou sit pripravenou ve fronte k uceni
        cursor = self.config.db.cursor(MySQLdb.cursors.DictCursor)
        query = "SELECT 1 FROM neural_network"
        cursor.execute(query)
        neural_network = cursor.fetchone()
        cursor.close()
        return None
    #enddef
    
    def __startLearningProcess(self, neural_network):
        # Nastartujeme ucici proces
        return None
    #enddef
    
    def __stopLearningProcess(self):
        # Zastavime ucici proces
        if not self.__learningInProgress():
            dbg.log("Learning NOT in progress", WARN=2)
            return
        #endif
        return None
    #enddef
    

    def _postUsr1(self, signum, frame):
        # Dostali jsme signal SIGUSR1, zastavime ucici proces
        self.__stopLearningProcess()
    #enddef


    def _processIteration(self):
        if self.__learningInProgress():
            dbg.log("Learning still in progress", INFO=2)
            return
        #endif
        neural_network = self.__getNextNeuralNetwork()
        if neural_network:
            self.__startLearningProcess(neural_network)
        #endif
    #enddef

#endclass




def main():
    config = PicturedetectorDaemonConfig('/www/picturedetector/daemon/conf/daemon.conf', '/www/picturedetector/daemon/conf/daemon.db.conf')
    daemon = PicturedetectorDaemon(config)
    daemon.process()
#enddef


if __name__ == '__main__':
    main()
#endif

