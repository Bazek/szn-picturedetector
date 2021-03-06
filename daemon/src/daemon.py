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
from picturedetector import util

import psutil
import os.path
import signal
import subprocess
import shutil
import re
from random import shuffle
import numpy as np
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
            self.image_file_prefix = parser.get(section, "ImageFilePrefix")
            self.image_learn_file_suffix = parser.get(section, "ImageLearnFileSuffix")
            self.image_validate_file_suffix = parser.get(section, "ImageValidateFileSuffix")
        #enddef
    #endclass
    
    class NeuralNetworkConfig(object):
        """ Parse solver section """
        def __init__(self, parser, section='neural-networks'):
            pass
        #enddef
    #endclass


    def reload(self):
        super(PicturedetectorDaemonConfig, self).reload()
        self.backend = ConfigBox(self.parser, "backend")
        self.caffe = self.CaffeConfig(self.parser, "caffe")
        self.neural_networks = self.NeuralNetworkConfig(self.parser, "neural-networks")
    #enddef

#endclass




class PicturedetectorDaemon(Daemon):
    """ PicturedetectorDaemon Process """

    # Konstanty, ktere odpovidaji enum hodnotam v tabulce picture
    DB_TRAINING = 'training'
    DB_VALIDATION = 'validation'
    DB_TESTING = 'testing'
    
    # Konstanty, ktere slouzi jako klice do pole se statistikami uceni
    ACCURACY = 'accuracy'
    LOSS = 'loss'
    SNAPSHOT = 'snapshot'
    
    # Signal, ktery se posle podprocesu v pripade ze daemon dostal signal pro ukonceni
    KILL_SIGNAL = signal.SIGINT

    def __learningInProgress(self):
        """
        Interní metoda Daemona, která zjišťuje jestli právě probíhá nějaké učení.
        Metoda nevyžaduje žádné parametry a vrací hodnotu typu boolean konkrétně
        hodnotu True pokud nějaké učení právě probíhá.
        Metoda funguje tak, že pokud existuje soubor s uloženým PID, tak jej načte
        a následně zkontroluje jestli v systému běží proces se zadaným PID. Pokud
        neběží, tak vypíše do logu chybu, že daný proces neběžel a vrátí False,
        čímž dá najevo, že žádné aktuální učení neprobíhá. 
        """
        pid = self._readPid()
        if pid:
            # Pokud existuje soubor s PID, zkontrolujeme, ze dany proces bezi
            if psutil.pid_exists(pid):
                # Pokud proces bezi, vratime True
                return True
            else:
                dbg.log("Ucici proces nebezi!", INFO=3)
                #self.__stopLearningProcess()
        #endif
        
        # Pokud pidfile neexistuje, nebo je prazdny, vratime False
        return False
    #enddef
    
    def __getNextNeuralNetwork(self):
        """
        Další interní metoda Daemona, která nevyžaduje žádné vstupní parametry.
        Jedná se o metodu, která zastřešuje komunikaci s Backendem díky které 
        zjišťuje jestli existuje ve frontě pro učení neuronových sítí záznam,
        který je ve stavu waiting a tudíž čeká na naučení.
        """
        # Precteme z databaze dalsi neuronovou sit pripravenou ve fronte k uceni
        result = self.config.backend.proxy.learning_queue.getNext()
        dbg.log(str(result), INFO=3)
        return result['data']
    #enddef
    
    def __startLearningProcess(self, queue_info):
        """
        Interní metoda, která zajišťuje započatí učení neuronové sítě na frameworku
        Caffe. Vstupním parametrem
        je pole, které obsahuje načtené informace z databáze o neuronové síti
        a databázi fotografií na kterých se má učení provádět.
        """
        dbg.log("Start learning network with id " + str(queue_info['neural_network_id']), INFO=3)

        pid = self._startCaffeLearning(queue_info['neural_network_id'], queue_info['picture_set_id'], queue_info['start_iteration'])
        if pid:
            self._savePid(pid)
            return True
        #endif

        return False
    #enddef
    
    def __stopLearningProcess(self):
        """
        Zastavení učícího procesu. Tato interní metoda je zavolána pokud Daemon dostane
        systémový signál SIGABRT. Po přijetí tohoto signálu dojde ke kontrole jestli
        nějaké učení běží a pokud ano, tak bude následně ukončeno. V dalším cyklu
        Daemona pak může započíst učení nové.
        """
        dbg.log("STOP LEARNING!", INFO=3)
        
        # Zastavime ucici proces
        if not self.__learningInProgress():
            dbg.log("Learning NOT in progress", WARN=2)
            return False
        #endif
        
        pid = self._readPid()

        # Odstraneni zaznamu v databazi
        self.config.backend.proxy.learning_queue.deleteLearning()
            
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
    
    def _postAbrt(self, signum, frame):
        """
        Metoda obsluhující systémový signál SIGABRT. Po jeho přijetí se provede kontrola
        jestli běží učení a pokud ano, tak bude toto učení ukončeno, ale proces Daemona
        bude běžet dále (nebude ukončen).
        """
        # Dostali jsme signal SIGABRT, zastavime ucici proces
        self.__stopLearningProcess()
    #enddef

    def _readPid(self):
        """
        Pomocná metoda pro načtení PID procesu, který učí neuronovou síť.
        Pokud soubor s PID neexistuje nebo je prázdný, protože žádné učení neprobíhá.
        Tak bude vrácena hodnota False. V jiném případě bude vrácena číselná hodnota
        PID procesu.
        """
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
        """
        Uložení PID do specifikovaného souboru v konfiguraci Daemona. Metoda očekává
        parametr, který udává hodnotu PID, která se má uložit.
        """
        pid_file = self.config.caffe.pid_file
        f = open(pid_file, 'w')
        if not f:
            raise self.ProcessException("Nemuzu vytvorit PID soubor (" + pid_file + ")!")
        f.write(str(pid))
        f.close()

    def _startCaffeLearning(self, neural_network_id, picture_set, start_iteration = 0):
        """
        Pomocná metoda, která zastřešuje započatí učení nad Frameworkem Caffe.
        V této metodě se volají veškeré pomocné skripty, které jsou potřeba, aby
        mohlo započít učení. Metoda očekává tři
        parametry kterými jsou identifikátor neuronové sítě, identifikátor databáze
        fotografií a volitelný parametr, který udává číslo iterace od kterého se má
        učení spustit. Tento parametr se využívá, pokud již klasifikátor naučený byl
        a chceme v učení pokračovat. Pokud se tento parametr nevyplní, tak se jako výchozí
        hodnota nastaví hodnota 0, tudíž bude klasifikátor učen od začátku.
        """
        learn_script = self.config.caffe.learn_script
        create_imagenet_script = self.config.caffe.create_imagenet_script
        create_mean_file_script = self.config.caffe.create_mean_file_script
        
        # Cteni konfigurace solveru z databaze
        solver_config_path = self._getPath(neural_network_id, 'solver')
        solver_config = util.readProtoSolverFile(solver_config_path)
        
        # Parsovani cest ze souboru imagenet_train_val.prototxt
        layer_config = util.readProtoLayerFile(solver_config.net)
        layer_paths = util.parseLayerPaths(layer_config)

        # Ziskat picture set a vygenerovat soubory s cestami k obrazkum (validacni a ucici)
        picture_files = self._createFilesWithImages(neural_network_id, picture_set)

        # Otevreni souboru pro zapis 
        learn_log_path = self._getPath(neural_network_id, 'new_log')
        
        dir = os.path.dirname(learn_log_path)
        if not os.path.exists(dir):
            os.makedirs(dir)
        #endif
        
        dbg.log('Learning log: ' + learn_log_path, INFO=3)
        learn_log = open(learn_log_path, 'w')
        if not learn_log:
            raise self.ProcessException("Nemuzu vytvorit soubor s logem uceni (" + learn_log_path + ")!")
        #endif
        
        # Vymazat stare uloznene obrazky pokud existuji
        if os.path.exists(layer_paths[util.TRAIN][util.SOURCE]):
            shutil.rmtree(layer_paths[util.TRAIN][util.SOURCE])
        endif
        
        if os.path.exists(layer_paths[util.VALIDATE][util.SOURCE]):
            shutil.rmtree(layer_paths[util.VALIDATE][util.SOURCE])
        endif
        
        # Vytvoreni argumentu pro spusteni skriptu pro vytvoreni databaze obrazku. Prvni parametr je cesta ke skriptu
        create_args = []
        create_args.append(create_imagenet_script)
        create_args.append(picture_files[util.TRAIN])
        create_args.append(picture_files[util.VALIDATE])
        create_args.append(layer_paths[util.TRAIN][util.SOURCE])
        create_args.append(layer_paths[util.VALIDATE][util.SOURCE])
        dbg.log("create_args " + str(create_args), INFO=3)
        # Vytvorit imagenet pomoci souboru s obrazky a zadanych cest kde se maji vytvorit
        subprocess.call(create_args)
        
        # Vytvoreni argumentu pro spusteni skriptu pro vytvoreni mean souboru obrazku pro trenovaci obrazky
        create_mean_file_args = []
        create_mean_file_args.append(create_mean_file_script)
        create_mean_file_args.append(layer_paths[util.TRAIN][util.SOURCE])
        create_mean_file_args.append(layer_paths[util.TRAIN][util.MEAN_FILE])
        dbg.log("create_mean_file_args " + str(create_mean_file_args), INFO=3)

        # Vytvorit mean file pro trenovaci obrazky
        subprocess.call(create_mean_file_args)
        
        # Vygenerovani cesty pro mean file soubor pro klasifikaci
        mean_file_path = self._getPath(neural_network_id, 'mean_file')
        
        dir = os.path.dirname(mean_file_path)
        if not os.path.exists(dir):
            os.makedirs(dir)
        #endif
        
        # Vytvoreni binarniho souboru, ktery dokaze nacist numpy.
        # Tento soubor je potreba pro klasifikaci obrazku, vyse vytvoreny mean file se pouziva pro trenovani site.
        self._createClassifyMeanFile(layer_paths[util.TRAIN][util.MEAN_FILE], mean_file_path)
        
        # Vytvoreni argumentu pro spusteni skriptu pro vytvoreni mean souboru obrazku pro validacni obrazky
        create_mean_file_args = []
        create_mean_file_args.append(create_mean_file_script)
        create_mean_file_args.append(layer_paths[util.VALIDATE][util.SOURCE])
        create_mean_file_args.append(layer_paths[util.VALIDATE][util.MEAN_FILE])
        
        # Vytvorit mean file pro validacni obrazky
        subprocess.call(create_mean_file_args)
        
        # Vytvoreni solver souboru pro uceni
        self._generateSolverFile(solver_config_path, network['id'])
        
        # Vytvoreni argumentu pro spusteni skriptu pro uceni neuronove site. Prvni parametr je cesta ke skriptu
        learn_args = []
        learn_args.append(learn_script)
        learn_args.append('train')
        learn_args.append('-solver=' + solver_config_path)
        
        if start_iteration:
            if not solver_config.snapshot_prefix:
                raise self.ProcessException("Nepodarilo se precist prefix nazvu souboru s ulozenym ucenim (" + solver_config.snapshot_prefix + ")!")
            #endif

            dbg.log("Prefix souboru s ulozenym ucenim: " + solver_config.snapshot_prefix, INFO=3)
            
            result = self.config.backend.proxy.neural_network.getSnapshotStatePath(neural_network_id, start_iteration)
            saved_file_path = result['data']
            learn_args.append('-snapshot=' + saved_file_path)
        #endif
        dbg.log(str(learn_args), INFO=3)
        p = subprocess.Popen(learn_args, stderr=learn_log, stdout=learn_log)
        if p:
            return p.pid
        #endif
        
        return False
    #enddef
        
    def _processIteration(self):
        """
        Hlavní cyklus Daemona. Zde probíhá všechna logika Daemona, který zde
        kontroluje jestli aktuálně běží učení a pokud ne, tak jestli existuje
        neuronová síť, která čeká na učení.
        """

        if self.__learningInProgress():
            dbg.log("Learning still in progress", INFO=2)
            return
        #endif
        queue_info = self.__getNextNeuralNetwork()

        if queue_info:
            try:
                self.__startLearningProcess(queue_info)
            except Exception, e:
                dbg.log('Exception occured during starting learning process')
                self.__stopLearningProcess()
                raise
        #endif
    #enddef

    def _createFilesWithImages(self, neural_network_id, picture_set):
        """
        Pomocná metoda, která obstarává vytvoření vstupních souborů pro framework Caffe,
        který vyžaduje načtení specifického textového souboru z kterého bude poté
        vytvořena LMDB databáze fotografií, které umí Caffe zpracovat. Tento vstupní soubor
        má následující formát. Každá fotografie je vypsán na zvláštním řádku, kde na začátku
        řádku se nachází cesta k fotografii, poté následuje znak mezery a za ní následuje
        identifikátor kategorie, do které fotografie patří. Pro úspěšné učení klasifikátoru
        je potřeba vytvořit tyto soubory dva a to konkrétně pro fotografie ze sekcí
        learning a validation. Parametry metody jsou dva a to identifikátor
        neuronové sítě a identifikátor databáze fotografií.
        """
        # @todo change loeading of fielpaths
        image_learn_file_suffix = self.config.caffe.image_learn_file_suffix
        image_validate_file_suffix = self.config.caffe.image_validate_file_suffix
        learn_file = self._createImageFileName(neural_network_id, picture_set, image_learn_file_suffix)
        validate_file = self._createImageFileName(neural_network_id, picture_set, image_validate_file_suffix)
        
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
            util.TRAIN: learn_file,
            util.VALIDATE: validate_file
        }
        
        # nacist obrazky z picture setu
        result = self.config.backend.proxy.picture.listSimple(picture_set)
        pictures = result['data']
        
        # zamichani obrazku, je potreba pro lepsi uceni s mensim poctem vzorku v jedne iteraci (u grafickych karet s mensi pameti)
        shuffle(pictures)

        # prochazeni obrazku a ukladani do prislusnych souboru
        for picture in pictures:
            if picture['learning_set'] == self.DB_TRAINING:
                file = f_learn
            elif picture['learning_set'] == self.DB_VALIDATION:
                file = f_validate
            elif picture['learning_set'] == self.DB_TESTING:
                continue
            else:
                continue;
            #endif

            # escapovani znaku " a ' v nazvech souboru
            picture_path = picture['hash'].replace('"', '\\"').replace("'", "\\'");
            
            # nutna dekrementace ID hodnot (v DB jsou hodnoty od 1), ale caffe pocita skupiny od 0
            line = picture_path + ' ' + str(picture['learning_subset_id'] - 1) + "\n"
            file.write(line.encode('utf-8'))
        
        # uzavreni souboru
        f_learn.close()
        f_validate.close()
        
        return createdFiles
    #enddef
    
    def _createImageFileName(self, neural_network_id, picture_set, suffix = ""):
        """
        Další pomocná metoda, která zastřešuje komunikaci s Backendem. Tato metoda komunikuje
        s Backendem a zjišťuje, cestu k adresáři pro dočasné soubory dané neuronové sítě,
        kde může vytvořit soubory s vygenerovanými cestami k fotografiím.
        Tyto soubory framework Caffe potřebuje k učení klasifikátorů. Metoda má tři vstupní
        parametry, kde první parametr je identifikátor neuronové sítě, druhý parametr
        je identifikátor databáze fotografií a třetím parametrem je přípona, která se má
        souborům nastavit. Třetí parametr je zde proto, aby bylo možné metodu využít v kódu
        na více místech.
        """
        path = self._getPath(neural_network_id, 'temp_dir')
        prefix = self.config.caffe.image_file_prefix
        filename = os.path.join(path, prefix + str(picture_set) + suffix)
        return filename
    #enddef

    #todo DELETE (NOT USED)
    def _generateSolverFile(self, filepath, neural_network_id):
        """
        Metoda určena pro generování konfigurace solveru, která zajistí doplnění
        hodnot s cestami k souborům v solver konfiguraci. Administrátor by takto nemusel
        doplňovat ručně konkrétní správné hodnoty a byly by cesty za něj doplněny automaticky.
        Nevýhodou je, že administrátor nemůže ovlivnit jaká cesta se zde vloží a nemá příležitost
        nastavit si libovolnou cestu například k datům z jiné neuronové sítě, protože budou vždy
        automaticky přepsány. Proto se tato metoda v aktuálním kódu nevyužívá a společnost
        Seznam.cz rozhodla, že pro lepší kontrolu nad obsahem konfigurace solveru
        nebudou tyto cesty automaticky generovány. Metoda obsahuje dva vstupní parametry
        a to cestu, kde se má soubor pro konfigurace solveru uložit a identifikátor
        neuronové sítě.
        """
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
        file = open(filepath, 'w')
        if not file:
            raise self.ProcessException("Nemuzu vytvorit solver soubor (" + filepath + ")!")
        file.write(file_content)
        file.close()
    #enddef
    

    def _learningStatus(self, neural_network_id, log_name):
        """
        Pro vypsání stavu učení slouží právě tato metoda, která jako parametry očekává
        identifikátor modelu o kterém má vypsat statistiku učení a databázi fotografií
        nad kterou se učení provádělo. Návratovou hodnotou je pole s daty, které
        bude možné v administračním rozhraním vykreslit do podoby grafu nebo případné
        jiné vizualizace.
        """
        result = self.config.backend.proxy.neural_network.getLogPath(neural_network_id, log_name)
        log_path = result['data']
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
        is_restored = False
        
        # Cteni konfiguracniho souboru
        for line in file:
            # V souboru jsme nasli ze byl vytvoreny snapshot (plati pro cislo iterace uvedene pod nim)
            m_snapshot = re.search("Snapshotting\s+solver\s+state\s+to", line, flags=re.IGNORECASE)
            if m_snapshot:
                has_snapshot = True
            #endif
            
            # Pokud jsme nekdy obnovili snapshot, tak ponechame predchozi hodnoty, protoze obnova snapshotu neobsahuje namerene hodnoty
            m_restoring = re.search("Restoring\sprevious\ssolver\sstatus\sfrom", line, flags=re.IGNORECASE)
            if m_restoring:
                is_restored = True
            #endif
            
            # V souboru jsme nasli cislo testovane iterace
            m_iter = re.search("Iteration\s+(\d+),\s+Testing\s+net", line, flags=re.IGNORECASE)
            if m_iter:
                if not is_restored:
                    act_iteration = int(m_iter.group(1))
                    results[act_iteration] = {
                        self.ACCURACY: 0.0,
                        self.LOSS: 0.0,
                        self.SNAPSHOT: has_snapshot
                    }
                else:
                    is_restored = False
                #endif

                
                has_snapshot = False
            #endif

            # V souboru jsme nasli vysledky pro testovanou iteraci
            
            m_result = re.search("Test\s+net\s+output\s+#(\d+):\s*[^=]+=\s*((?:(?:[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)|nan))", line, flags=re.IGNORECASE)
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
            
        #endfor
        
        file.close()
        return results
    #enddef

    def _createClassifyMeanFile(self, source_meanfile, target_meanfile):
        """
        Jelikož framework Caffe vyžaduje jiný formát mean file souboru při učení
        a při klasifikaci, tak tato metody vytváří mean file soubor v numpy numpy formátu,
        který se načítá při vytváření klasifikátoru a zajišťuje rychlejší klasifikaci.
        Vstupními parametry metody je cesta k trénovacímu mean file souboru a cesta, kde
        se má uložit výsledný mean file v numpy formátu.
        """
        # cilovy meanfile pro klasifikaci nebyl zadan, nebudeme ho vytvaret
        if not target_meanfile:
            return
        #endif
                        
        # otevreni souboru s trenovaci mean file
        try:
            f = open(source_meanfile, 'rb')
        except IOError:
            raise self.ProcessException("Mean file soubor nepodarilo otevrit (" + source_meanfile + ")!")
        
        # nacteni mean file dat 
        content = f.read()
        f.close()
        
        # prevod mean file souboru do pole dat
        blob = caffe_pb2.BlobProto()
        blob.ParseFromString(content)
        nparray = blobproto_to_array(blob)
        
        # ulozeni pole dat do vysledneho souboru
        f = open(target_meanfile, 'wb')
        if not f:
            raise self.ProcessException("Cilovy mean file soubor se nepodarilo otevrit pro zapis (" + target_meanfile + ")!")
        #endif
        np.save(f, nparray)
        f.close()
    #enddef
    
    def _getPath(self, neural_network_id, file_path_type):
        """
        Pomocná metoda, která zastřešuje komunikaci s Backendem. Zde z Backendu získáváme
        informaci o cestě ke zvolenému typu souboru pro danou neuronovou síť.
        Vstupní parametry jsou dva a jsou to identifikátor neuronové sítě a typ
        souboru jehož cestu chceme získat.
        """
        result = self.config.backend.proxy.neural_network.getPath(neural_network_id, file_path_type)
        path = result['data']

        return path
    #enddef

#endclass

def blobproto_to_array(blob, return_diff=False):
  """Convert a blob proto to an array. In default, we will just return the data,
  unless return_diff is True, in which case we will return the diff.
  This method is copied from caffe io.py and is fixed (removed first argument blob.num)
  """
  if return_diff:
    return np.array(blob.diff).reshape(
        blob.channels, blob.height, blob.width)
  else:
    return np.array(blob.data).reshape(
        blob.channels, blob.height, blob.width)


def main():
    config = PicturedetectorDaemonConfig('/www/picturedetector/daemon/conf/daemon.conf')
    daemon = PicturedetectorDaemon(config)
    daemon.process()
#enddef


if __name__ == '__main__':
    main()
#endif

