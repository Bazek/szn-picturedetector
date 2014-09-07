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
import signal
import subprocess
import shutil
import re
import caffe
from caffe.proto import caffe_pb2

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
            self.create_mean_file_script = parser.get(section, "CreateMeanFileScript")
            self.save_file_path = parser.get(section, "SaveFilePath")
            self.image_file_path = parser.get(section, "ImageFilePath")
            self.image_file_prefix = parser.get(section, "ImageFilePrefix")
            self.image_learn_file_suffix = parser.get(section, "ImageLearnFileSuffix")
            self.image_validate_file_suffix = parser.get(section, "ImageValidateFileSuffix")
            self.learn_output_path = parser.get(section, "LearnOutputPath")
            self.learn_outout_prefix = parser.get(section, "LearnOutputPrefix")
            self.mean_file_path = parser.get(section, "MeanFilePath")
            self.mean_file_prefix = parser.get(section, "MeanFilePrefix")
            self.mean_learn_file_suffix = parser.get(section, "MeanLearnFileSuffix")
            self.mean_validate_file_suffix = parser.get(section, "MeanValidateFileSuffix")
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
    
    # caffe vklada tuto constantu pri ukladani stavu uceni
    SAVE_FILE_PREFIX = '_iter_'
    
    # koncovka souboru s konfiguraci solveru
    SOLVER_EXT = '.solverstate'
    
    # koncovka mean file souboru
    MEAN_FILE_EXT = '.binaryproto'
    
    # Konstanty, ktere slouzi jako klice do pole se statistikami uceni
    ACCURACY = 'accuracy'
    LOSS = 'loss'
    SNAPSHOT = 'snapshot'
    
    # Signal, ktery se posle podprocesu v pripade ze daemon dostal signal pro ukonceni
    KILL_SIGNAL = signal.SIGTERM

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
        dbg.log("Start learning network with id " + str(queue_info['neural_network_id']), INFO=3)
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
        os.kill(pid, self.KILL_SIGNAL)
        
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

    def _startCaffeLearning(self, neural_network_id, picture_set, startIteration = 0):
        learn_script = self.config.caffe.learn_script
        create_imagenet_script = self.config.caffe.create_imagenet_script
        create_mean_file_script = self.config.caffe.create_mean_file_script
                
        # Ziskat picture set a vygenerovat soubory s cestami k obrazkum (validacni a ucici)
        picture_files = self._createFilesWithImages(picture_set)
        
        # Nacteni informaci o neuronvoe siti
        #network = server.globals.rpcObjects['neural_network'].get(neural_network, bypass_rpc_status_decorator=True)
        network = self.neural_network_get(neural_network_id)
        
        # Vymazat stare uloznene obrazky pokud existuji
        if os.path.exists(network['train_db_path']):
            shutil.rmtree(network['train_db_path'])
        #endif
            
        if os.path.exists(network['validate_db_path']):
            shutil.rmtree(network['validate_db_path'])
        #endif
        
        # Otevreni souboru pro zapis 
        learn_log_path = self._getLearnLogPath(network['id'])
        if startIteration == 0:
            file_mode = 'w'
        else:
            file_mode = 'a'
        #endif
                
        dbg.log('Learning log: ' + learn_log_path, INFO=3)
        learn_log = open(learn_log_path, file_mode)
        if not learn_log:
            raise self.ProcessException("Nemuzu vytvorit soubor s logem uceni (" + learn_log_path + ")!")
        #endif
        
        # Vytvoreni argumentu pro spusteni skriptu pro vytvoreni databaze obrazku. Prvni parametr je cesta ke skriptu
        create_args = []
        create_args.append(create_imagenet_script)
        create_args.append(picture_files[self.TRAIN])
        create_args.append(picture_files[self.VALIDATE])
        create_args.append(network['train_db_path'])
        create_args.append(network['validate_db_path'])
        
        # Vytvorit imagenet pomoci souboru s obrazky a zadanych cest kde se maji vytvorit
        subprocess.call(create_args)
        
        # Vytvoreni argumentu pro spusteni skriptu pro vytvoreni mean souboru obrazku pro trenovaci obrazky
        mean_learn_file_suffix = self.config.caffe.mean_learn_file_suffix
        mean_train_file_path = self._createMeanFileName(network['id'], mean_learn_file_suffix)
        create_mean_file_args = []
        create_mean_file_args.append(create_mean_file_script)
        create_mean_file_args.append(network['train_db_path'])
        create_mean_file_args.append(mean_train_file_path)
        
        # Vytvorit mean file pro trenovaci obrazky
        subprocess.call(create_mean_file_args)
        
        # Vytvoreni argumentu pro spusteni skriptu pro vytvoreni mean souboru obrazku pro validacni obrazky
        mean_validate_file_suffix = self.config.caffe.mean_validate_file_suffix
        mean_validate_file_path = self._createMeanFileName(network['id'], mean_validate_file_suffix)
        create_mean_file_args = []
        create_mean_file_args.append(create_mean_file_script)
        create_mean_file_args.append(network['validate_db_path'])
        create_mean_file_args.append(mean_validate_file_path)
        
        # Vytvorit mean file pro validacni obrazky
        subprocess.call(create_mean_file_args)

        # Vytvoreni argumentu pro spusteni skriptu pro uceni neuronove site. Prvni parametr je cesta ke skriptu
        learn_args = []
        learn_args.append(learn_script)
        learn_args.append(network['solver_config_path'])
        
        if startIteration:
            save_file_path = self.config.caffe.save_file_path
            #TODO zjistit jak precist hodnoty z prototxt souboru
            #solver_config = self._readProtoSolverFile(network['solver_config_path'])
            #dbg.log(str(solver_config), INFO=3)
            config = self._getPrototxtConfigValue(network['solver_config_path'], 'snapshot_prefix')
            
            if not config['snapshot_prefix']:
                raise self.ProcessException("Nepodarilo se precist prefix nazvu souboru s ulozenym ucenim (" + network['solver_config_path'] + ")!")
            #endif
            
            dbg.log("Prefix souboru s ulozenym ucenim: " + config['snapshot_prefix'], INFO=3)
            
            saved_file_path = os.path.join(save_file_path, config['snapshot_prefix'] + self.SAVE_FILE_PREFIX + str(startIteration) + self.SOLVER_EXT)
            learn_args.append(saved_file_path)
        #endif
        
        p = subprocess.Popen(learn_args, stderr=learn_log)
        if p:
            return p.pid
        #endif
        
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
            #TODO delete
            dbg.log(str(self._learningStatus(queue_info['neural_network_id'])), INFO=3)
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
        #endif
        
        dir = os.path.dirname(validate_file)
        if not os.path.exists(dir):
            os.makedirs(dir)
        #endif
        
        # Otevrit soubory pro zapis
        f_learn = open(learn_file, 'w')
        if not f_learn:
            raise self.ProcessException("Nemuzu vytvorit databazi s obrazky (" + learn_file + ")!")
        #endif
        
        f_validate = open(validate_file, 'w')
        if not f_validate:
            raise self.ProcessException("Nemuzu vytvorit databazi s obrazky (" + validate_file + ")!")
        #endif
        
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
        filename = os.path.join(path, prefix + str(picture_set) + suffix)
        return filename
    #enddef
    
    def _createMeanFileName(self, picture_set, suffix = ""):
        path = self.config.caffe.mean_file_path
        prefix = self.config.caffe.mean_file_prefix
        filename = os.path.join(path, prefix + str(picture_set) + suffix + self.MEAN_FILE_EXT)
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
                    integer model_id                model id
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
    
    def _getPrototxtConfigValue(self, filepath, variables):
        # Prevedeni jednoho prvku na pole
        if not isinstance(variables, list):
            variables = [variables]
        #endif
        
        # Priprava navratove hodnoty
        results = {}
        for var in variables:
            results[var] = False
        
        # Otevreni konfiguracniho souboru
        file = open(filepath, 'r')
        if not file:
            raise self.ProcessException("Soubor s konfiguraci neexistuje (" + filepath + ")!")
        #endif
        
        # Cteni konfiguracniho souboru
        for line in file:
            for var in variables:
                m = re.match(r"(" + var + "\s*):\s*(?:(?:[\"'](.*)[\"'])|([^\"'].*))\s*", line, flags=re.IGNORECASE)
                if m:
                    results[m.group(1)] = m.group(2)
                    
        file.close()
        return results
    #enddef
    
    def _readProtoLayerFile(self, filepath):
        #TODO pujde pouzit tato  konstanta na zavolani tridy? caffe_pb2
        #self.config.caffe.proto_config_class
        layers_config = caffe.proto.caffe_pb2.NetParameter
        return self._readProtoFile(filepath, layers_config)
    #enddef
    
    def _readProtoSolverFile(self, filepath):
        solver_config = caffe.proto.caffe_pb2.SolverParameter()
        #TODO how to read proto file?
        #caffe.ReadProtoFromTextFile(filepath, data)
        return self._readProtoFile(filepath, solver_config)
    #enddef
    
    def _readProtoFile(self, filepath, parser_object):
        file = open(filepath, "rb")
        if not file:
            raise self.ProcessException("Soubor s konfiguraci vrstev neuronove site neexistuje (" + filepath + ")!")
        
        parser_object.ParseFromString(file.read())
        file.close()
        
        return parser_object
    #enddef
    
    def _learningStatus(self, neural_network_id):
        log_path = self._getLearnLogPath(neural_network_id)
        dbg.log(log_path, INFO=3)
        # Otevreni souboru s logem uceni
        file = open(log_path, 'r')
        if not file:
            raise self.ProcessException("Logovaci soubor uceni neexistuje (" + log_path + ")!")
        #endif
        
        # Priprava navratove hodnoty
        results = {}
        act_iteration = False
        has_snapshot = False
        
        # Cteni konfiguracniho souboru
        for line in file:
            # V souboru jsme nasli ze byl vytvoreny snapshot (plati pro cislo iterace uvedene pod nim)
            m_snapshot = re.search("Snapshotting\s+solver\s+state\s+to", line, flags=re.IGNORECASE)
            if m_snapshot:
                has_snapshot = True
            #endif
            
            # V souboru jsme nasli cislo testovane iterace
            m_iter = re.search("Iteration\s+(\d+),\s+Testing\s+net", line, flags=re.IGNORECASE)
            if m_iter:
                act_iteration = int(m_iter.group(1))
                results[act_iteration] = {
                    self.ACCURACY: 0.0,
                    self.LOSS: 0.0,
                    self.SNAPSHOT: has_snapshot
                }
                
                has_snapshot = False
            #endif
            
            # V souboru jsme nasli vysledky pro testovanou iteraci
            m_result = re.search("Test\s+score\s+#(\d+):\s*((?:(?:[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)|nan))", line, flags=re.IGNORECASE)
            if m_result:
                value = m_result.group(2)
                if value == 'nan':
                    value = 0
                #endif
                
                value = float(value)
                
                if act_iteration:
                    if m_result.group(1) == '0':
                        results[act_iteration][self.ACCURACY] = value
                    elif m_result.group(1) == '1':
                        results[act_iteration][self.LOSS] = value
                    #endif
                #endif
            #endif
            
        file.close()
        return results
    #enddef
    
    def _getLearnLogPath(self, neural_network_id):
        log_path = os.path.join(self.config.caffe.learn_output_path, self.config.caffe.learn_outout_prefix + str(neural_network_id))
        return log_path
#endclass



def main():
    config = PicturedetectorDaemonConfig('/www/picturedetector/daemon/conf/daemon.conf', '/www/picturedetector/daemon/conf/daemon.db.conf')
    daemon = PicturedetectorDaemon(config)
    daemon.process()
#enddef


if __name__ == '__main__':
    main()
#endif

