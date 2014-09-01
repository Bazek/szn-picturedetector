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
import psutil
import os.path


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
            self.pid_file = parser.get(section, "PidFile")
            self.learn_script = parser.get(section, "LearnScript")
            self.create_imagenet_script = parser.get(section, "CreateImagenetScript")
            self.save_file_prefix = parser.get(section, "SaveFilePrefix")
            self.image_file_path = parser.get(section, "ImageFilePath")
            self.image_file_prefix = parser.get(section, "ImageFilePrefix")
            self.image_learn_file_suffix = parser.get(section, "ImageLearnFileSuffix")
            self.image_validate_file_suffix = parser.get(section, "ImageValidateFileSuffix")      
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
    # Konstanty pro rozliseni souboru pro uceni a validaci
    TRAIN = 'train'
    VALIDATE = 'validate'
    
    # Konstanty, ktere odpovidaji enum hodnotam v tabulce picture
    DB_TRAINING = 'training'
    DB_VALIDATION = 'validation'
    DB_TESTING = 'testing'
    
    def __learningInProgress(self):
        pid = self._readPid()
        if pid:
            # Pokud existuje soubor s PID, zkontrolujeme, ze dany proces bezi
            if psutil.pid_exists(pid):
                # Pokud proces bezi, vratime True
                return True
            else:
                # Pokud proces nebezi, vyhodime vyjimku: raise self.ProcessException("Ucici proces nebezi!")
                raise self.ProcessException("Ucici proces nebezi!")
        #endif
        
        # Pokud pidfile neexistuje, nebo je prazdny, vratime False
        return False
    #enddef
    
    def __getNextNeuralNetwork(self):
        # Precteme z databaze dalsi neuronovou sit pripravenou ve fronte k uceni
        cursor = self.config.db.cursor(MySQLdb.cursors.DictCursor)
        query = "SELECT neural_network FROM learning_queue WHERE status = 'waiting'"
        cursor.execute(query)
        neural_network = cursor.fetchone()
        cursor.close()
        return neural_network
    #enddef
    
    def __startLearningProcess(self, neural_network, picture_set):
        # Aktualizujeme zaznam v databazi
        query = "UPDATE learning_queue SET status = 'learning' WHERE status = 'waiting'";
        self.cursor.execute(query)
        
        pid = self._startCaffeLearning(neural_network, picture_set, startIteration)
        if pid:
            self._savePid(pid)
            return True
        #endif
        
        return False
    #enddef
    
    def __stopLearningProcess(self):
        # Zastavime ucici proces
        if not self.__learningInProgress():
            dbg.log("Learning NOT in progress", WARN=2)
            return False
        #endif
        
        # Zastaveni processu
        pid = self._readPid()
        os.kill(pid, signal.SIGQUIT)
        
        # Odstraneni zaznamu v databazi
        query = "DELETE FROM learning_queue WHERE status = 'learning'";
        self.cursor.execute(query)
        
        # Odstraneni souboru s bezicim PID
        pid_file = self.config.caffe.pid_file
        os.remove(pid_file)
        
        return True
    #enddef
    
    def _postUsr1(self, signum, frame):
        # Dostali jsme signal SIGUSR1, zastavime ucici proces
        self.__stopLearningProcess()
    #enddef

    def _readPid(self):
        pid_file = self.config.caffe.pid_file
        
        if os.path.isfile(pid_file):
            f = open(pid_file, 'r')
            
            # Cteni PID ze souboru
            pid = f.read()
            pid = int(pid)
            return pid
            
        return False
    #enddef
    
    def _savePid(self, pid):
        pid_file = self.config.caffe.pid_file
        f = open(pid_file, 'w')
        if not f:
            raise self.ProcessException("Nemuzu vytvorit PID soubor (" + pid_file + ")!")
        f.write(pid)
        f.close()

    def _startCaffeLearning(self, neural_network, picture_set, startIteration = 0):
        learn_script = self.config.caffe.learn_script
        create_script = self.config.caffe.create_script
                
        # Ziskat picture set a vygenerovat soubory s cestami k obrazkum (validacni a ucici)
        picture_files = self._createFilesWithImages(picture_set)
        
        # Nacteni informaci o neuronvoe siti
        network = server.globals.rpcObjects['neural_network'].get(neural_network, bypass_rpc_status_decorator=True)
        
        # Vymazat stare uloznene obrazky pokud existuji
        if os.path.exists(network['train_db_path']):
            os.rmdir(network['train_db_path'])
            
        if os.path.exists(network['validate_db_path']):
            os.rmdir(network['validate_db_path'])
            
        # Vytvorit imagenet pomoci souboru s obrazky a zadanych cest kde se maji vytvorit
        subprocess.call(create_script, picture_files[self.TRAIN], picture_files[self.VALIDATE], network['train_db_path'], network['validate_db_path'])
        
        learn_args = []
        learn_args.append(network['model_config_path'])
        
        if startIteration:
            saveFilePrefix = self.config.caffe.save_file_prefix
            learn_args.append(saveFilePrefix+startIteration)
        
        p = subprocess.Popen(learn_script, learn_args)
        if p:
            return p.pid
        
        return False
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

    def _createFilesWithImages(self, picture_set):
        image_learn_file_suffix = self.config.caffe.image_learn_file_suffix
        image_validate_file_suffix = self.config.caffe.image_validate_file_suffix
        learn_file = self._createImageFileName(picture_set, image_learn_file_suffix)
        validate_file = self._createImageFileName(picture_set, image_validate_file_suffix)
        
        # Otevrit soubory pro zapis
        f_learn = fopen(learn_file, 'w')
        if not f:
            raise self.ProcessException("Nemuzu vytvorit soubor s obrazky (" + learn_file + ")!")
        
        f_validate = fopen(validate_file, 'w')
        if not f:
            raise self.ProcessException("Nemuzu vytvorit soubor s obrazky (" + validate_file + ")!")
        
        createdFiles = {
            self.TRAIN: learn_file,
            self.VALIDATE: validate_file
        }
        
        # nacist obrazky z picture setu
        pictures = server.globals.rpcObjects['picture'].list(picture_set, bypass_rpc_status_decorator=True)
        
        # prochazeni obrazku a ukladani do prislusnych souboru
        for picture in pictures:
            if picture['learning_set'] == self.DB_TRAINING:
                file = f_learn
            elif picture['learning_set'] == self.DB_VALIDATION:
                file = f_validate
            elif picture['learning_set'] == self.DB_TESTING:
                continue
            #endif

            line = picture['hash'] + ' ' + picture['learning_subset']
            file.write(line)
        
        # uzavreni souboru
        f_learn.close()
        f_validate.close()
        
        return createdFiles
    #enddef
    
    def _createImageFileName(self, picture_set, suffix = ""):
        path = self.config.caffe.image_file_path
        prefix = self.config.caffe.image_file_prefix
        
        filename = path + prefix + picture_set + suffix
        
        return filename
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

