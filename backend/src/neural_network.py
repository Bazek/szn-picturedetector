#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# DESCRIPTION
#   Prace s neuronovou siti
#

from dbglog import dbg
import metaserver.fastrpc as server

from rpc_backbone.decorators import rpcStatusDecorator, MySQL_master, MySQL_slave
from lib.backend import Backend

import os.path
import shutil

class NeuralNetworkBackend(Backend):
    """
    Trida pro praci s neuronovou siti
    """

    @rpcStatusDecorator('neural_network.get', 'S:i')
    @MySQL_slave
    def get(self, id):
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
                    string description              description
                    integer pretrained_iteration    iterace pouzita pro klasifikaci
                    boolean auto_init               priznak automaticke inicializace neuronove site
                    boolean keep_saved              priznak ulozeni neuronove site pri klasifikaci
                    boolean gpu                     priznak jestli neuronova sit, muze vyuzivat gpu
                    string model_config             obsah souboru s konfiguraci modelu
                    string solver_config            obsah souboru s konfiguraci pro uceni
                    string trainmodel_config        obsaj souboru s konfiguraci modelu pro uceni
                    string net_path                 cesta k souboru s konfiguraci pro reseni neuronove site
                    string snapshot_path            cesta k slozce, kde se ukladaji snapshoty
                    string train_source_path        cesta k slozce, kde jsou ulozeny trenovaci obrazky
                    string train_meanfile_path      cesta k trenovacimu meanfile souboru
                    string validate_source_path     cesta k slozce, kde jsou ulozeny validacni obrazky
                    string validate_meanfile_path   cesta k validacnimu meanfile souboru
                }
            }
        """

        query = """
            SELECT neural_network.id, neural_network.description, neural_network.pretrained_iteration, neural_network.auto_init, neural_network.keep_saved, neural_network.gpu
            FROM neural_network
            WHERE neural_network.id = %s
        """
        self.cursor.execute(query, id)
        neural_network = self.cursor.fetchone()
        if not neural_network:
            raise Exception(404, "Neural network not found")
        #endif

        neural_network['model_config'] = server.globals.rpcObjects['neural_network'].getFileContent(id, 'model', bypass_rpc_status_decorator=True)
        neural_network['solver_config'] = server.globals.rpcObjects['neural_network'].getFileContent(id, 'solver', bypass_rpc_status_decorator=True)
        neural_network['trainmodel_config'] = server.globals.rpcObjects['neural_network'].getFileContent(id, 'trainmodel', bypass_rpc_status_decorator=True)
        neural_network['net_path'] = server.globals.rpcObjects['neural_network'].getPath(id, 'trainmodel', bypass_rpc_status_decorator=True)
        neural_network['snapshot_path'] = os.path.join(server.globals.rpcObjects['neural_network'].getPath(id, 'snapshot_dir', bypass_rpc_status_decorator=True), self.config.neural_networks.snapshots_name)
        neural_network['train_source_path'] = server.globals.rpcObjects['neural_network'].getPath(id, 'train_source_path', bypass_rpc_status_decorator=True)
        neural_network['train_meanfile_path'] = server.globals.rpcObjects['neural_network'].getPath(id, 'train_meanfile_path', bypass_rpc_status_decorator=True)
        neural_network['validate_source_path'] = server.globals.rpcObjects['neural_network'].getPath(id, 'validate_source_path', bypass_rpc_status_decorator=True)
        neural_network['validate_meanfile_path'] = server.globals.rpcObjects['neural_network'].getPath(id, 'validate_meanfile_path', bypass_rpc_status_decorator=True)
        return neural_network
    #enddef

    @rpcStatusDecorator('neural_network.list', 'S:')
    @MySQL_slave
    def list(self):
        """
        Vylistuje vsechny neuronove site

        Signature:
            neural_network.list()

        Returns:
            struct {
                int status                          200 = OK
                string statusMessage                Textovy popis stavu
                array data {
                    integer id                      neural_network_id
                    string description              description
                    integer pretrained_iteration    iterace pouzita pro klasifikaci
                    boolean auto_init               priznak automaticke inicializace neuronove site
                    boolean keep_saved              priznak ulozeni neuronove site pri klasifikaci
                    boolean gpu                     priznak jestli neuronova sit, muze vyuzivat gpu
                    string model_config             obsah souboru s konfiguraci modelu
                    string solver_config            obsah souboru s konfiguraci pro uceni
                }
            }
        """

        query = """
            SELECT neural_network.id, neural_network.description, neural_network.pretrained_iteration, neural_network.auto_init, neural_network.keep_saved, neural_network.gpu, learning_queue.status
            FROM neural_network
            LEFT JOIN learning_queue ON learning_queue.neural_network_id = neural_network.id
        """
        self.cursor.execute(query)
        neural_networks = self.cursor.fetchall()
        
        for neural_network in neural_networks:
            neural_network['status'] = self._getStatus(neural_network)
        #endfor
        
        return neural_networks
    #enddef
    
    @rpcStatusDecorator('neural_network.add', 'S:S')
    @MySQL_master
    def add(self, param):
        """
        Pridani nove neuornove site s vybranym ID modelu

        Signature:
            neural_network.add(struct param)

        @param {
            description                 Popisek
            model_config                obsah souboru s konfiguraci modelu
            solver_config               obsah souboru s konfiguraci pro uceni
            trainmodel_config           obsah souboru s konfiguraci pro uceni modelu
            auto_init                   priznak automaticke inicializace neuronove site
            keep_saved                  priznak ulozeni neuronove site pri klasifikaci
            gpu                         priznak jestli neuronova sit, muze vyuzivat gpu
        }

        Returns:
            struct {
                int status              200 = OK
                string statusMessage    Textovy popis stavu
                int data                Vraci id nove neuronove site
            }
        """

        query = """
            INSERT INTO neural_network (`description`, `auto_init`, `keep_saved`, `gpu`)
            VALUE (%(description)s, %(auto_init)s, %(keep_saved)s, %(gpu)s)
        """
        self.cursor.execute(query, param)
        neural_network_id = self.cursor.lastrowid
        
        # inicializace (vytvoreni) adresaru potrebnych pro uceni
        init_dirs = ['base_dir', 'snapshot_dir', 'temp_dir', 'log_dir']
        for directory in init_dirs:
            directory_path = server.globals.rpcObjects['neural_network'].getPath(neural_network_id, directory, bypass_rpc_status_decorator=True)
            if not os.path.exists(directory_path):
                os.makedirs(directory_path)
            #endif
        #endfor

        server.globals.rpcObjects['neural_network'].saveFile(neural_network_id, 'model', param['model_config'], bypass_rpc_status_decorator=True)
        server.globals.rpcObjects['neural_network'].saveFile(neural_network_id, 'solver', param['solver_config'], bypass_rpc_status_decorator=True)
        server.globals.rpcObjects['neural_network'].saveFile(neural_network_id, 'trainmodel', param['trainmodel_config'], bypass_rpc_status_decorator=True)
        return neural_network_id
    #enddef

    @rpcStatusDecorator('neural_network.edit', 'S:iS')
    @MySQL_master
    def edit(self, neural_network_id, params):
        """
        Editace neuronove site

        Signature:
            neural_network.edit(int id, struct param)

        @neural_network_id  Id neuronove site
        @params {
            description                 Popisek
            pretrained_iteration        iterace pouzita pro klasifikaci
            auto_init                   priznak automaticke inicializace neuronove site
            keep_saved                  priznak ulozeni neuronove site pri klasifikaci
            gpu                         priznak jestli neuronova sit, muze vyuzivat gpu
            pretrained_model_path       cesta k predtrenovanemu modelu
            mean_file                   cesta k mean file souboru pro klasifikaci
        }

        Returns:
            struct {
                int status              200 = OK
                string statusMessage    Textovy popis stavu
                bool data               Success
            }
        """

        filterDict = {
            "description":              "description = %(description)s",
            "pretrained_iteration":     "pretrained_iteration = %(pretrained_iteration)s",
            "auto_init":                "auto_init = %(auto_init)s",
            "keep_saved":               "keep_saved = %(keep_saved)s",
            "gpu":                      "gpu = %(gpu)s",
        }

        if params['model_config']:
            server.globals.rpcObjects['neural_network'].saveFile(neural_network_id, 'model', params['model_config'], bypass_rpc_status_decorator=True)
            del params['model_config']
        #endif
        
        if params['solver_config']:
            server.globals.rpcObjects['neural_network'].saveFile(neural_network_id, 'solver', params['solver_config'], bypass_rpc_status_decorator=True)
            del params['solver_config']
        #endif
        
        if params['trainmodel_config']:
            server.globals.rpcObjects['neural_network'].saveFile(neural_network_id, 'trainmodel', params['trainmodel_config'], bypass_rpc_status_decorator=True)
            del params['trainmodel_config']
        #endif
        
        SET = self._getFilter(filterDict, params, "SET", ", ")
        params["id"] = neural_network_id
        query = """
            UPDATE neural_network
            """ + SET + """
            WHERE id = %(id)s
        """
        self.cursor.execute(query, params)
                
        return True
    #enddef

    @rpcStatusDecorator('neural_network.delete', 'S:i')
    @MySQL_master
    def delete(self, neural_network_id):
        """
        Odstrani celou neuronovou sit

        Signature:
            neural_network.delete(int neural_network_id)

        @neural_network_id           Id Neuronove site

        Returns:
            struct {
                int status              200 = OK
                string statusMessage    Textovy popis stavu
                bool data               Uspesne smazano
            }
        """

        query = """
            DELETE FROM neural_network
            WHERE id = %s
        """
        self.cursor.execute(query, neural_network_id)
        if self.cursor.rowcount == 0:
            status, statusMessage = 404, "NeuralNetwork #%d not found." % neural_network_id
            raise Exception(status, statusMessage)
        #endif

#        server.globals.rpcObjects['neural_network'].deleteFile(neural_network_id, 'model', bypass_rpc_status_decorator=True)
#        server.globals.rpcObjects['neural_network'].deleteFile(neural_network_id, 'solver', bypass_rpc_status_decorator=True)
#        server.globals.rpcObjects['neural_network'].deleteFile(neural_network_id, 'trainmodel', bypass_rpc_status_decorator=True)

        base_dir = server.globals.rpcObjects['neural_network'].getPath(neural_network_id, 'base_dir', bypass_rpc_status_decorator=True)
        temp_dir = server.globals.rpcObjects['neural_network'].getPath(neural_network_id, 'temp_dir', bypass_rpc_status_decorator=True)
        
        # Vymaze slozku s daty
        if os.path.exists(base_dir):
            shutil.rmtree(base_dir)
        #endif
        
        # Vymaze slozku s docasnymi soubory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        #endif
        
        return True
    #enddef
    
    @rpcStatusDecorator('neural_network.getPath', 'S:is')
    def getPath(self, neural_network_id, file_type):
        """
        Vrati cestu k souboru neuronove site.
        Cesta je vygenerovana dle ID neuronove site a dle typu souboru

        Signature:
            neural_network.getPath(int neural_network_id, string file_type)

        @neural_network_id           Id Neuronove site
        @file_type                   Typ souboru

        Returns:
            struct {
                int status              200 = OK
                string statusMessage    Textovy popis stavu
                string data             Cesta k souboru
            }
        """

        base_folder = self.config.neural_networks.base_path
        
        if file_type == 'solver':
            filename = self.config.neural_networks.solver_file
        elif file_type == 'model':
            filename = self.config.neural_networks.deploy_file
        elif file_type == 'trainmodel':
            filename = self.config.neural_networks.trainmodel_file
        elif file_type == 'mean_file':
            filename = self.config.neural_networks.classify_mean_file
        elif file_type == 'snapshot_dir':
            filename = self.config.neural_networks.snapshots_folder
        elif file_type == 'base_dir':
            filename = ''
        elif file_type == 'temp_dir':
            filename = self.config.neural_networks.temp_folder
        elif file_type == 'log_dir':
            filename = self.config.neural_networks.logs_folder
        elif file_type == 'new_log':
            filename = os.path.join(self.config.neural_networks.logs_folder, datetime.datetime.now().strftime(self.config.neural_networks.log_timestamp_format) + self.config.neural_networks.log_extension)
        elif file_type == 'train_source_path':
            filename = os.path.join(self.config.neural_networks.temp_folder, self.config.neural_networks.train_db_folder)
        elif file_type == 'train_meanfile_path':
            filename = os.path.join(self.config.neural_networks.temp_folder, self.config.neural_networks.train_mean_file)
        elif file_type == 'validate_source_path':
            filename = os.path.join(self.config.neural_networks.temp_folder, self.config.neural_networks.validation_db_folder)
        elif file_type == 'validate_meanfile_path':
            filename = os.path.join(self.config.neural_networks.temp_folder, self.config.neural_networks.validation_mean_file)
        else:
            raise Exception(500, "Unknown file type (" + file_type + ")")
        #endif
        
        path = os.path.join(base_folder, str(neural_network_id), filename)
        return path
    #enddef
    
    @rpcStatusDecorator('neural_network.getSnapshotPath', 'S:is')
    def getSnapshotPath(self, neural_network_id, iteration):
        """
        Vrati cestu ke souboru s ulozenym stavem uceni s danou iteraci.
        Cesta je vygenerovana dle ID neuronove site.

        Signature:
            neural_network.getPath(int neural_network_id, string file_type)

        @neural_network_id           Id Neuronove site
        @iteration                   Iterace uceni

        Returns:
            struct {
                int status              200 = OK
                string statusMessage    Textovy popis stavu
                string data             Cesta k souboru
            }
        """

        snapshot_dir = server.globals.rpcObjects['neural_network'].getPath(neural_network_id, 'snapshot_dir', bypass_rpc_status_decorator=True)
        filename = self.config.neural_networks.snapshots_name
        caffe_const = self.config.caffe.caffe_snapshot_const
        extension = self.config.caffe.caffe_snapshot_ext
        path = os.path.join(snapshot_dir, filename + caffe_const + str(iteration) + extension)
        return path
    #enddef
    
    @rpcStatusDecorator('neural_network.getLogPath', 'S:is')
    def getLogPath(self, neural_network_id, log_name):
        """
        Vrati cestu ke souboru s logem.
        Cesta je vygenerovana dle ID neuronove site a zadaneho nazvu souboru.

        Signature:
            neural_network.getLogPath(int neural_network_id, string log_name)

        @neural_network_id           Id Neuronove site
        @log_name                    Nazev logu

        Returns:
            struct {
                int status              200 = OK
                string statusMessage    Textovy popis stavu
                string data             Cesta k souboru
            }
        """

        log_dir = server.globals.rpcObjects['neural_network'].getPath(neural_network_id, 'log_dir', bypass_rpc_status_decorator=True)
        extension = self.config.caffe.log_extension
        path = os.path.join(log_dir, log_name + extension)
        return path
    #enddef
    
    @rpcStatusDecorator('neural_network.getLogs', 'S:i')
    def getLogs(self, neural_network_id):
        log_dir = server.globals.rpcObjects['neural_network'].getPath(neural_network_id, 'log_dir', bypass_rpc_status_decorator=True)
        logs = self._getFiles(log_dir)
        
        paths = []
        for path in logs:
            paths.append({'filename': path})
        #endfor
        
        return paths
    #enddef

    @rpcStatusDecorator('neural_network.getFileContent', 'S:i')
    def getFileContent(self, id, file_type):
        file_path = server.globals.rpcObjects['neural_network'].getPath(id, file_type, bypass_rpc_status_decorator=True)
        file = open(file_path, 'r')
        if not file:
            raise self.ProcessException("Nemuzu otevrit " + file_type + " soubor (" + file_path + ")!")
        file_content = file.read()
        return file_content;
    #enddef

    @rpcStatusDecorator('neural_network.saveFile', 'S:s')
    def saveFile(self, id, file_type, file_content):
        file_path = server.globals.rpcObjects['neural_network'].getPath(id, file_type, bypass_rpc_status_decorator=True)
        
        # Vytvoreni potrebnych adresaru
        dir = os.path.dirname(file_path)
        if not os.path.exists(dir):
            os.makedirs(dir)
            
        file = open(file_path, 'w')
        if not file:
            raise self.ProcessException("Nemuzu vytvorit " + file_type + " soubor (" + file_path + ")!")
        file.write(file_content)
        file.close()
        
        return True
    #enddef

    @rpcStatusDecorator('neural_network.deleteFile', 'S:i')
    def deleteFile(self, id, file_type):
        file_path = server.globals.rpcObjects['neural_network'].getPath(id, file_type, bypass_rpc_status_decorator=True)
        if os.path.isfile(file_path):
            os.remove(file_path)
        else:
            dbg.log("Soubor " + file_type + " neexistuje (" + file_path +")", INFO=3)
            return False
        #endif
        
        return True
    #enddef
    
    @rpcStatusDecorator('neural_network.test', 'S:ii')
    def test(self, id, picture_set_id):
        params = {'learning_set': 'testing'}
        pictures = server.globals.rpcObjects['picture'].listSimple(picture_set_id, params, bypass_rpc_status_decorator=True)
        max_images = int(self.config.test.max_images)
        print_results = []
        start = 0
        correct = 0
        wrong = 0
        wrong_false = 0
        wrong_true = 0
        wrong_60 = 0
        wrong_70 = 0
        wrong_80 = 0
        wrong_90 = 0
        wrong_100 = 0
        correct_sum = 0
        wrong_sum = 0
        wrong_false_sum = 0
        wrong_true_sum = 0
        stop = max_images
        wrong_false_files = []
        wrong_true_files = []
        failed_classify = 0
        script_false = "#!/bin/bash\n"
        script_true = "#!/bin/bash\n"

        while 1:
            pictures_block = pictures[start:stop]
            classify_images = []
            images_categories = {}
            
            if len(pictures_block) < 1:
                break
            
            start = stop
            stop += max_images
            
            for picture in pictures_block:
                subset = picture['learning_subset_id']
                hash = picture['hash']
                images_categories[hash] = subset
                classify_images.append({'id': hash, 'path': hash})
            #endfor

            results = server.globals.rpcObjects['classify'].classify(id, classify_images, bypass_rpc_status_decorator=True)
            failed_classify += len(pictures_block) - len(results)
            
            for hash in results:
                correct_category = images_categories[hash]
                # Kategorie v DB zacina od 1, v caffe zacina od 0
                category = (results[hash][0]['category'] + 1)
                percentage = results[hash][0]['percentage']

                if category == correct_category:
                    correct += 1
                    correct_sum += percentage
                    message='OK'
                else:
                    wrong += 1
                    wrong_sum += percentage
                    message='Wrong'
                    if (category - correct_category) < 0:
                        wrong_false += 1
                        wrong_false_sum += percentage
                        wrong_false_files.append("{0:.4f}".format(percentage) + "\t" + hash)
                        script_false += "xdg-open " + hash + "\nsleep 3\n"
                    else:
                        wrong_true += 1
                        wrong_true_sum += percentage
                        wrong_true_files.append("{0:.4f}".format(percentage) + "\t" + hash)
                        script_true += "xdg-open " + hash + "\nsleep 3\n"
                        
                    if percentage < 0.6:
                        wrong_60 += 1
                    elif percentage < 0.7:
                        wrong_70 += 1
                    elif percentage < 0.8:
                        wrong_80 += 1
                    elif percentage < 0.9:
                        wrong_90 += 1
                    elif percentage < 1:
                        wrong_100 += 1
                    
                #print_results.append(hash + ":\n\t" + message + "\t(" + "{0:.4f}".format(percentage) + ")")
            #endfor 
            
        #endwhile
        
        script_false += "sleep 300"
        script_true += "sleep 300"
        
        print_results.append("----------------------------------------")
        print_results.append("Script True")
        print_results.append(script_true)
        print_results.append("Script False")
        print_results.append(script_false)
        print_results.append("----------------------------------------")
        print_results.append("Wrong True files")
#        for record in wrong_true_files:
#            print_results.append(record)
        print_results.append("----------------------------------------")
        print_results.append("Wrong False files")
        for record in wrong_false_files:
            print_results.append(record)
        print_results.append("----------------------------------------")
        print_results.append("Wrong")
        print_results.append("Wrong False:\t" + str(wrong_false))
        print_results.append("Wrong True:\t" + str(wrong_true))
        print_results.append("Wrong < 0.6:\t" + str(wrong_60))
        print_results.append("Wrong < 0.7:\t" + str(wrong_70))
        print_results.append("Wrong < 0.8:\t" + str(wrong_80))
        print_results.append("Wrong < 0.9:\t" + str(wrong_90))
        print_results.append("Wrong < 1.0:\t" + str(wrong_100))
        print_results.append("----------------------------------------")
        print_results.append("Average values")
        if correct > 0:
            print_results.append("Correct:\t\t" + str(correct_sum/correct))
        if wrong > 0:
            print_results.append("Wrong:\t\t" + str(wrong_sum/wrong))
        if wrong_true > 0:
            print_results.append("Wrong True:\t" + str(wrong_true_sum/wrong_true))
        if wrong_false > 0:
            print_results.append("Wrong False:\t" + str(wrong_false_sum/wrong_false))
        print_results.append("----------------------------------------")
        print_results.append("Final results")
        print_results.append("Failed:\t\t" + str(failed_classify))
        print_results.append("Correct:\t\t" + str(correct))
        print_results.append("Wrong:\t\t" + str(wrong))
        print_results.append("Total:\t\t" + str(correct + wrong))
        
        return print_results
    #enddef

    @rpcStatusDecorator('neural_network.learningStatus', 'S:s')
    def learningStatus(self, neural_network_id, learn_log):
        log_path = server.globals.rpcObjects['neural_network'].getLogPath(neural_network_id, learn_log, bypass_rpc_status_decorator=True)
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
    
    def _getStatus(self, neural_network_data):
        status = neural_network_data['status']
        if not neural_network_data['status']:
            if neural_network_data['pretrained_iteration']:
                status = 'ready (iter: ' + str(neural_network_data['pretrained_iteration']) + ')'
            else:
                status = 'not learned'
            #endif
        #endif
        
        return status
    #enddef
    
    def _getFiles(self, folder):
        files = []
        for file in os.listdir(folder):
            if file.endswith(self.config.neural_networks.log_extension):
                files.append(file)
            #endif
        #endfor
                
        return files
    #enddef
    
#endclass

