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
import subprocess
import shutil

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
        query = "SELECT neural_network_id, picture_set_id, start_iteration FROM learning_queue WHERE status = 'waiting'"
        cursor.execute(query)
        queue_info = cursor.fetchone()
        cursor.close()
        return queue_info
    #enddef
    
    def __startLearningProcess(self, queue_info):
        dbg.log("Start learning network with id " + queue_info['neural_network_id'], INFO=3)
        cursor = self.config.db.cursor(MySQLdb.cursors.DictCursor)
        
        # Aktualizujeme zaznam v databazi
        query = "UPDATE learning_queue SET status = 'learning' WHERE neural_network_id = %s";
        cursor.execute(query, queue_info['neural_network_id'])
        self.config.db.commit()
        cursor.close()
        
        pid = self._startCaffeLearning(queue_info['neural_network_id'], queue_info['picture_set_id'], queue_info['start_iteration'])
        if pid:
            self._savePid(pid)
            return True
        #endif

        return False
    #enddef
    
    def __stopLearningProcess(self):
        cursor = self.config.db.cursor(MySQLdb.cursors.DictCursor)
        
        # Zastavime ucici proces
        if not self.__learningInProgress():
            dbg.log("Learning NOT in progress", WARN=2)
            return False
        #endif
        
        pid = self._readPid()

        # Odstraneni zaznamu v databazi
        query = "DELETE FROM learning_queue WHERE status = 'learning'";
        cursor.execute(query)
        self.config.db.commit()
        cursor.close()
        
        # Odstraneni souboru s bezicim PID
        pid_file = self.config.caffe.pid_file
        os.remove(pid_file)
        
        # Zastaveni processu
        os.kill(pid, signal.SIGQUIT)
        
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
            if pid:
                pid = int(pid)
                return pid
            
        return False
    #enddef
    
    def _savePid(self, pid):
        pid_file = self.config.caffe.pid_file
        f = open(pid_file, 'w')
        if not f:
            raise self.ProcessException("Nemuzu vytvorit PID soubor (" + pid_file + ")!")
        f.write(str(pid))
        f.close()

    def _startCaffeLearning(self, neural_network, picture_set, startIteration = 0):
        learn_script = self.config.caffe.learn_script
        create_imagenet_script = self.config.caffe.create_imagenet_script
                
        # Ziskat picture set a vygenerovat soubory s cestami k obrazkum (validacni a ucici)
        picture_files = self._createFilesWithImages(picture_set)
        
        # Nacteni informaci o neuronvoe siti
        #network = server.globals.rpcObjects['neural_network'].get(neural_network, bypass_rpc_status_decorator=True)
        network = self.neural_network_get(neural_network)
        
        # Vymazat stare uloznene obrazky pokud existuji
        if os.path.exists(network['train_db_path']):
            shutil.rmtree(network['train_db_path'])
            
        if os.path.exists(network['validate_db_path']):
            shutil.rmtree(network['validate_db_path'])
        
        # Vytvoreni argumentu pro spusteni skriptu pro vytvoreni databaze obrazku. Prvni parametr je cesta ke skriptu
        create_args = []
        create_args.append(create_imagenet_script)
        create_args.append(picture_files[self.TRAIN])
        create_args.append(picture_files[self.VALIDATE])
        create_args.append(network['train_db_path'])
        create_args.append(network['validate_db_path'])

        # Vytvorit imagenet pomoci souboru s obrazky a zadanych cest kde se maji vytvorit
        subprocess.call(create_args)
        
        # Vytvoreni argumentu pro spusteni skriptu pro uceni neuronove site. Prvni parametr je cesta ke skriptu
        learn_args = []
        learn_args.append(learn_script)
        learn_args.append(network['solver_config_path'])
        
        if startIteration:
            saveFilePrefix = self.config.caffe.save_file_prefix
            learn_args.append(saveFilePrefix+startIteration)
        
        p = subprocess.Popen(learn_args)
        if p:
            return p.pid
        
        return False
    #enddef
        
    def _processIteration(self):
        #TODO proc potrebuje databaze obnovovat, aby se nacetly aktualni data???
        self.config.reload()
        if self.__learningInProgress():
            dbg.log("Learning still in progress", INFO=2)
            return
        #endif
        queue_info = self.__getNextNeuralNetwork()

        if queue_info:
            self.__startLearningProcess(queue_info)
        #endif
    #enddef

    def _createFilesWithImages(self, picture_set):
        image_learn_file_suffix = self.config.caffe.image_learn_file_suffix
        image_validate_file_suffix = self.config.caffe.image_validate_file_suffix
        learn_file = self._createImageFileName(picture_set, image_learn_file_suffix)
        validate_file = self._createImageFileName(picture_set, image_validate_file_suffix)
        
        # Vytvoreni potrebnych adresaru dle konfigurace
        dir = os.path.dirname(learn_file)
        if not os.path.exists(dir):
            os.makedirs(dir)
            
        dir = os.path.dirname(validate_file)
        if not os.path.exists(dir):
            os.makedirs(dir)
            
        # Otevrit soubory pro zapis
        f_learn = open(learn_file, 'w')
        if not f_learn:
            raise self.ProcessException("Nemuzu vytvorit soubor s obrazky (" + learn_file + ")!")
        
        f_validate = open(validate_file, 'w')
        if not f_validate:
            raise self.ProcessException("Nemuzu vytvorit soubor s obrazky (" + validate_file + ")!")
        
        createdFiles = {
            self.TRAIN: learn_file,
            self.VALIDATE: validate_file
        }
        
        # nacist obrazky z picture setu
        pictures = self.picture_list(picture_set)

        # prochazeni obrazku a ukladani do prislusnych souboru
        for picture in pictures:
            if picture['learning_set'] == self.DB_TRAINING:
                file = f_learn
            elif picture['learning_set'] == self.DB_VALIDATION:
                file = f_validate
            elif picture['learning_set'] == self.DB_TESTING:
                continue
            #endif

            line = picture['hash'] + ' ' + str(picture['learning_subset']) + "\n"
            file.write(line)
        
        # uzavreni souboru
        f_learn.close()
        f_validate.close()
        
        return createdFiles
    #enddef
    
    def _createImageFileName(self, picture_set, suffix = ""):
        path = self.config.caffe.image_file_path
        prefix = self.config.caffe.image_file_prefix
        
        filename = path + '/' + prefix + str(picture_set) + suffix
        
        return filename
    #enddef
    
    def picture_list(self, picture_set_id, params={}):
        cursor = self.config.db.cursor(MySQLdb.cursors.DictCursor)
        
        # Kontrola parametru
        if "learning_set" in params and params["learning_set"] not in self.config.pictures.learning_set_paths:
            raise Exception(402, "Unknown learning_set: %s" % params["learning_set"])
        #endif
        if "learning_subset" in params and params["learning_subset"] not in ("true", "false"):
            raise Exception(402, "Unknown learning_subset: %s" % params["learning_subset"])
        #endif

        filterDict = {
            "picture_set_id":   "picture_set_id = %(picture_set_id)s",
            "learning_set":     "learning_set = %(learning_set)s",
            "learning_subset":  "learning_subset = %(learning_subset)s",
        }
        
        params["picture_set_id"] = picture_set_id
        WHERE = self._getFilter(filterDict, params)

        query = """
            SELECT `id`, `picture_set_id`, `learning_set`, `learning_subset`, `hash`
            FROM picture
            """ + WHERE + """
            ORDER BY id ASC
        """

        cursor.execute(query, params)
        pictures = cursor.fetchall()
        cursor.close()

        return pictures
    #enddef
    
    def neural_network_get(self, id):
        """
        Funkce pro precteni dat o neuronove siti dle zadaneho ID neuronove site

        Signature:
            neural_network.get(integer id)

        @id                 neural_network_id

        Returns:
            struct {
                int status                          200 = OK
                string statusMessage                Textovy popis stavu
                struct data {
                    integer id                      neural network id
                    integer model_id                 model id
                    string description              description
                    string pretrained_model_path    cesta k predtrenovanemu modelu
                    string mean_file_path           cesta k mean file souboru
                    string train_db_path            cesta k slozce s trenovacimi obrazky
                    string validate_db_path         cesta k slozce s validovanymi obrazky
                    string model_config_path        cesta k souboru s konfiguraci modelu
                    string solver_config_path       cesta k souboru s konfiguraci pro uceni
                }
            }
        """

        cursor = self.config.db.cursor(MySQLdb.cursors.DictCursor)
        query = """
            SELECT neural_network.id, neural_network.model_id, neural_network.description, neural_network.pretrained_model_path, neural_network.mean_file_path, neural_network.train_db_path, neural_network.validate_db_path, model.model_config_path, model.solver_config_path
            FROM neural_network
            JOIN model ON neural_network.model_id = model.id
            WHERE neural_network.id = %s
        """
        cursor.execute(query, id)
        neural_network = cursor.fetchone()
        cursor.close()
        
        if not neural_network:
            raise Exception(404, "Neural network not found")
        #endif
        
        return neural_network
    #enddef
    
    def _getFilter(self, filterDict, valuesDict, prefix="WHERE", separator=" AND ", empty=True):
        """ Pomocna funkce pro sestavovani klauzuli pomoci parametru """
        values = []
        for key, val in valuesDict.items():
            if key in filterDict:
                value = filterDict[key]
                values.append(value)
            else:
                status, statusMessage = 300, "Unknown value %s" % key
                raise BackendException(status, statusMessage)
            #endif
        #endfor

        FILTER = separator.join(values)
        if not FILTER and not empty:
            status, statusMessage = 300, "No data"
            raise BackendException(status, statusMessage)
        elif FILTER:
            FILTER = "%s %s" % (prefix, FILTER)
        #endif
        return FILTER
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

