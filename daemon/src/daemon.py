#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# AUTHOR           Petr Bartunek <petr.bartunek@firma.seznam.cz>
#
# Copyright (c) 2014 Seznam.cz, a.s.
# All rights reserved.
#


import sys
sys.path.insert(0, '/www/picturedetector/common/module/')

from szn_utils.configutils import ConfigBox
from szn_utils.daemon import DaemonConfig, Daemon
from dbglog import dbg

import psutil
import os.path
import signal
import subprocess
import shutil
import re

from caffe.proto import caffe_pb2
from google.protobuf import text_format
from google.protobuf import descriptor

class PicturedetectorDaemonConfig(DaemonConfig):

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
            self.solver_file_path = parser.get(section, "SolverFilePath")
            self.solver_file_prefix = parser.get(section, "SolverFilePrefix")           
        #enddef
    #endclass


    def reload(self):
        super(PicturedetectorDaemonConfig, self).reload()
        self.backend = ConfigBox(self.parser, "backend")
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
    
    # caffe vklada tuto konstantu pri ukladani stavu uceni
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
    KILL_SIGNAL = signal.SIGINT

    # Konstanty, ktere urcuji nactene cesty ze souboru imagenet_train_val.prototxt
    SOURCE = 'source'
    MEAN_FILE = 'mean_file'

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
        result = self.config.backend.proxy.neural_network.getNextLearningNetwork()
        dbg.log(str(result), INFO=3)
        return result['data']
    #enddef
    
    def __startLearningProcess(self, queue_info):
        dbg.log("Start learning network with id " + str(queue_info['neural_network_id']), INFO=3)

        # Aktualizujeme zaznam v databazi        
        self.config.backend.proxy.neural_network.setLearningNetwork(queue_info['neural_network_id'])
        
        pid = self._startCaffeLearning(queue_info['neural_network_id'], queue_info['picture_set_id'], queue_info['start_iteration'])
        if pid:
            self._savePid(pid)
            return True
        #endif

        return False
    #enddef
    
    def __stopLearningProcess(self):
        dbg.log("STOP LEARNING!", INFO=3)
        
        # Zastavime ucici proces
        if not self.__learningInProgress():
            dbg.log("Learning NOT in progress", WARN=2)
            return False
        #endif
        
        pid = self._readPid()

        # Odstraneni zaznamu v databazi
        self.config.backend.proxy.neural_network.deleteLearningNetwork()
            
        # Odstraneni souboru s bezicim PID
        pid_file = self.config.caffe.pid_file
        if os.path.isfile(pid_file):
            os.remove(pid_file)
        else:
            dbg.log('PID soubor uceni neexistuje', INFO=3)
            return False
        #endif
        
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
        save_file_path = self.config.caffe.save_file_path
        
        # Nacteni informaci o neuronove siti
        result = self.config.backend.proxy.neural_network.get(neural_network_id)
        network = result['data']
        
        # Cteni konfigurace solveru z databaze
        result = self.config.backend.proxy.solver_config.get(network['id'])
        solver_config = result['data']
        
        #TODO fix calling
        solver_config_path = self._getSolverPath(network['id'])
        
        # Parsovani cest ze souboru imagenet_train_val.prototxt
        layer_config = self._readProtoLayerFile(solver_config['net'])
        layer_paths = self._parseLayerPaths(layer_config)
        dbg.log("PARSE PATHS: " + str(layer_paths), INFO=3)
        # Ziskat picture set a vygenerovat soubory s cestami k obrazkum (validacni a ucici)
        picture_files = self._createFilesWithImages(picture_set)
        
        # Vymazat stare uloznene obrazky pokud existuji
        if os.path.exists(layer_paths[self.TRAIN][self.SOURCE]):
            shutil.rmtree(layer_paths[self.TRAIN][self.SOURCE])
        #endif
            
        if os.path.exists(layer_paths[self.VALIDATE][self.SOURCE]):
            shutil.rmtree(layer_paths[self.VALIDATE][self.SOURCE])
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
        create_args.append(layer_paths[self.TRAIN][self.SOURCE])
        create_args.append(layer_paths[self.VALIDATE][self.SOURCE])
        
        # Vytvorit imagenet pomoci souboru s obrazky a zadanych cest kde se maji vytvorit
        subprocess.call(create_args)
        
        # Vytvoreni argumentu pro spusteni skriptu pro vytvoreni mean souboru obrazku pro trenovaci obrazky
        create_mean_file_args = []
        create_mean_file_args.append(create_mean_file_script)
        create_mean_file_args.append(layer_paths[self.TRAIN][self.SOURCE])
        create_mean_file_args.append(layer_paths[self.TRAIN][self.MEAN_FILE])
        
        # Vytvorit mean file pro trenovaci obrazky
        subprocess.call(create_mean_file_args)
        
        # Vytvoreni argumentu pro spusteni skriptu pro vytvoreni mean souboru obrazku pro validacni obrazky
        create_mean_file_args = []
        create_mean_file_args.append(create_mean_file_script)
        create_mean_file_args.append(layer_paths[self.VALIDATE][self.SOURCE])
        create_mean_file_args.append(layer_paths[self.VALIDATE][self.MEAN_FILE])
        
        # Vytvorit mean file pro validacni obrazky
        subprocess.call(create_mean_file_args)
        
        # Vytvoreni solver souboru pro uceni
        self._generateSolverFile(solver_config_path, network['id'])
        
        # Vytvoreni argumentu pro spusteni skriptu pro uceni neuronove site. Prvni parametr je cesta ke skriptu
        learn_args = []
        learn_args.append(learn_script)
        learn_args.append('train')
        learn_args.append('-solver=' + solver_config_path)
        
        if startIteration:
            if not solver_config['snapshot_prefix']:
                raise self.ProcessException("Nepodarilo se precist prefix nazvu souboru s ulozenym ucenim (" + solver_config['snapshot_prefix'] + ")!")
            #endif

            dbg.log("Prefix souboru s ulozenym ucenim: " + solver_config['snapshot_prefix'], INFO=3)
            
            saved_file_path = os.path.join(save_file_path, solver_config['snapshot_prefix'] + self.SAVE_FILE_PREFIX + str(startIteration) + self.SOLVER_EXT)
            learn_args.append('-snapshot=' + saved_file_path)
        #endif
        
        p = subprocess.Popen(learn_args, stderr=learn_log, stdout=learn_log)
        if p:
            return p.pid
        #endif
        
        return False
    #enddef
        
    def _processIteration(self):
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
        result = self.config.backend.proxy.picture.list(picture_set)
        pictures = result['data']

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

    def _generateSolverFile(self, filepath, neural_network_id):
        # Cteni konfigurace solveru z databaze
        result = self.config.backend.proxy.solver_config.get(neural_network_id)
        config = result['data']
        
        solver_proto = caffe_pb2.SolverParameter()
        
        # Mapovani z property SolverParameter tridy na nazev databazoveho sloupecku
        # V zasade jsou nazvy stejne, ale to se muze casem zmenit (zmena definice v caffe)
        solver_db_mapping = {
            'net': 'net',
            'test_iter': 'test_iter',
            'test_interval': 'test_interval',
            'test_compute_loss': 'test_compute_loss',
            'base_lr': 'base_lr',
            'display': 'display',
            'max_iter': 'max_iter',
            'lr_policy': 'lr_policy',
            'gamma': 'gamma',
            'power': 'power',
            'momentum': 'momentum',
            'weight_decay': 'weight_decay',
            'stepsize': 'stepsize',
            'snapshot': 'snapshot',
            'snapshot_prefix': 'snapshot_prefix',
            'snapshot_diff': 'snapshot_diff',
            'snapshot_after_train': 'snapshot_after_train',
            'solver_mode': 'solver_mode',
            'device_id': 'device_id',
            'random_seed': 'random_seed',
            'debug_info': 'debug_info',
        }
        
        message_descriptor = solver_proto.DESCRIPTOR 
        for solver_property in solver_db_mapping:
            db_field = solver_db_mapping[solver_property]
            value = config[db_field]
            if value:
                field = message_descriptor.fields_by_name.get(solver_property, None)
                if field:
                    # prevedeni enum value z retezce na int
                    if field.type == descriptor.FieldDescriptor.TYPE_ENUM:
                        value = field.containing_type.enum_values_by_name[value].number
                        dbg.log(str(value), INFO=3)
                        
                    if field.label == descriptor.FieldDescriptor.LABEL_REPEATED: 
                        property = getattr(solver_proto, solver_property)
                        property.append(value)
                    else: 
                        setattr(solver_proto, solver_property, value)
                    #endif
                #endif
            #endif
        #endfor

        file_content = text_format.MessageToString(solver_proto, as_utf8=True)
        dbg.log(str(file_content), INFO=3)
        file = open(filepath, 'w')
        if not file:
            raise self.ProcessException("Nemuzu vytvorit solver soubor (" + filepath + ")!")
        file.write(file_content)
        file.close()
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
    #enddef

#
#
#
#TODO DELETE
# vvvvvvvv
#
#
    
    def _readProtoLayerFile(self, filepath):
        layers_config = caffe_pb2.NetParameter()
        return self._readProtoFile(filepath, layers_config)
    #enddef

    def _readProtoSolverFile(self, filepath):
        solver_config = caffe_pb2.SolverParameter()
        return self._readProtoFile(filepath, solver_config)
    #enddef

    def _readProtoFile(self, filepath, parser_object):
        file = open(filepath, "r")
        if not file:
            raise self.ProcessException("Soubor s konfiguraci vrstev neuronove site neexistuje (" + filepath + ")!")

        text_format.Merge(str(file.read()), parser_object)
        file.close()
        return parser_object
    #enddef

    def _getSolverPath(self, neural_network_id):
        solver_path = os.path.join(self.config.caffe.solver_file_path, self.config.caffe.solver_file_prefix + str(neural_network_id))
        return solver_path
    #enddef

    def _parseLayerPaths(self, proto):
        results = {}

        results[self.TRAIN] = {
            self.SOURCE: '',
            self.MEAN_FILE: ''
        }

        results[self.VALIDATE] = {
            self.SOURCE: '',
            self.MEAN_FILE: ''
        }

        for layer in proto.layers:
            if layer.type == caffe_pb2.LayerParameter.LayerType.Value('DATA'):
                include_name = False
                for include in layer.include:
                    if include.phase == caffe_pb2.Phase.Value('TRAIN'):
                        include_name = self.TRAIN
                    elif include.phase == caffe_pb2.Phase.Value('TEST'):
                        include_name = self.VALIDATE
                    #endif
                #endfor

                if not include_name or (include_name == self.TRAIN):
                    if layer.data_param.source:
                        results[self.TRAIN][self.SOURCE] = layer.data_param.source
                    #endif

                    if layer.data_param.mean_file:
                        results[self.TRAIN][self.MEAN_FILE] = layer.data_param.mean_file
                    #endif
                #endif

                if not include_name or (include_name == self.VALIDATE):
                    if layer.data_param.source:
                        results[self.VALIDATE][self.SOURCE] = layer.data_param.source
                    #endif

                    if layer.data_param.mean_file:
                        results[self.VALIDATE][self.MEAN_FILE] = layer.data_param.mean_file
                    #endif
                #endif
            #endif
        #endfor

        return results
#
# ^^^^^^^^
# END DELETE
#

#endclass



def main():
    config = PicturedetectorDaemonConfig('/www/picturedetector/daemon/conf/daemon.conf')
    daemon = PicturedetectorDaemon(config)
    daemon.process()
#enddef


if __name__ == '__main__':
    main()
#endif

