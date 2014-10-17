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

import caffe
import os.path

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
                    boolean auto_init               priznak automaticke inicializace neuronove site
                    boolean keep_saved              priznak ulozeni neuronove site pri klasifikaci
                    boolean gpu                     priznak jestli neuronova sit, muze vyuzivat gpu
                    string model_config             obsah souboru s konfiguraci modelu
                    string solver_config            obsah souboru s konfiguraci pro uceni
                }
            }
        """

        query = """
            SELECT neural_network.id, neural_network.description, neural_network.auto_init, neural_network.keep_saved, neural_network.gpu
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
                    boolean auto_init               priznak automaticke inicializace neuronove site
                    boolean keep_saved              priznak ulozeni neuronove site pri klasifikaci
                    boolean gpu                     priznak jestli neuronova sit, muze vyuzivat gpu
                    string model_config             obsah souboru s konfiguraci modelu
                    string solver_config            obsah souboru s konfiguraci pro uceni
                }
            }
        """

        query = """
            SELECT neural_network.id, neural_network.description, neural_network.auto_init, neural_network.keep_saved, neural_network.gpu
            FROM neural_network
        """
        self.cursor.execute(query)
        neural_networks = self.cursor.fetchall()
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
            train_config                obsah souboru s konfiguraci pro uceni modelu
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
        
        #TODO opravit problem s predanim parametru jako text
        dbg.log(str(param), INFO=3)
        server.globals.rpcObjects['neural_network'].saveFile(neural_network_id, 'model', param['model_config'], bypass_rpc_status_decorator=True)
        server.globals.rpcObjects['neural_network'].saveFile(neural_network_id, 'solver', param['solver_config'], bypass_rpc_status_decorator=True)
        server.globals.rpcObjects['neural_network'].saveFile(neural_network_id, 'trainmodel', param['train_config'], bypass_rpc_status_decorator=True)
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
            "auto_init":                "auto_init = %(auto_init)s",
            "keep_saved":               "keep_saved = %(keep_saved)s",
            "gpu":                      "gpu = %(auto_init)s",
        }

        if params['model_config']:
            server.globals.rpcObjects['neural_network'].saveFile(neural_network_id, 'model', params['model_config'], bypass_rpc_status_decorator=True)
            del params['model_config']
        #endif
        
        if params['solver_config']:
            server.globals.rpcObjects['neural_network'].saveFile(neural_network_id, 'solver', params['solver_config'], bypass_rpc_status_decorator=True)
            del params['solver_config']
        #endif
        
        if params['train_config']:
            server.globals.rpcObjects['neural_network'].saveFile(neural_network_id, 'trainmodel', params['train_config'], bypass_rpc_status_decorator=True)
            del params['train_config']
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

        neural_network['solver_config'] = server.globals.rpcObjects['solver_config'].delete(neural_network_id, bypass_rpc_status_decorator=True)
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

        base_path = self.config.neural_networks.base_path
        
        if file_type == 'solver':
            filename = self.config.neural_networks.solver_file
        elif file_type == 'model':
            filename = self.config.neural_networks.deploy_file
        elif file_type == 'trainmodel':
            filename = self.config.neural_networks.trainmodel_file
        elif file_type == 'mean_file':
            filename = self.config.neural_networks.mean_file
        else:
            raise Exception(500, "Unknown file type (" + file_type + ")")
        #endif
        
        path = os.path.join(base_path, str(neural_network_id), filename)
        return path
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
#endclass

