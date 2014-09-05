#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# DESCRIPTION
#   Prace s neuronovou siti
#

from dbglog import dbg

from rpc_backbone.decorators import rpcStatusDecorator, MySQL_master, MySQL_slave
from lib.backend import Backend

try:
    import caffe
except:
    dbg.log("Cannot import caffe", ERR=2)
#endtry

class NeuralNetworkBackend(Backend):
    """
    Trida pro praci s neuronovou siti
    """

    @rpcStatusDecorator('neural_network.function', 'S:,S:b')
    @MySQL_master
    def function(self, param=True):
        """
        Testovaci funkce

        Signature:
            neural_network.function(boolean param)

        @param          Popis parametru
                        Volitelny parametr. Default True.

        Returns:
            struct {
                int status              200 = OK
                string statusMessage    Textovy popis stavu
                boolean data            Vraci nejakou hodnotu (Vzdycky v polozce data)
            }
        """

        return {
            "normal":   self.get(2),
            "bypass":   self.get(2, bypass_rpc_status_decorator=True),
        }
    #enddef

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

        query = """
            SELECT neural_network.id, neural_network.model_id, neural_network.description, neural_network.pretrained_model_path, neural_network.mean_file_path, neural_network.train_db_path, neural_network.validate_db_path, model.model_config_path, model.solver_config_path
            FROM neural_network
            JOIN model ON neural_network.model_id = model.id
            WHERE neural_network.id = %s
        """
        self.cursor.execute(query, id)
        neural_network = self.cursor.fetchone()
        if not neural_network:
            raise Exception(404, "Neural network not found")
        #endif
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

        query = """
            SELECT neural_network.id, neural_network.model_id, neural_network.description, neural_network.pretrained_model_path, neural_network.mean_file_path, neural_network.train_db_path, neural_network.validate_db_path, model.model_config_path, model.solver_config_path
            FROM neural_network
            JOIN model ON neural_network.model_id = model.id
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
            model_id                    ID modelu z ktereho neuronova sit vychazi
            description                 Popisek
            pretrained_model_path       cesta k predtrenovanemu modelu
            mean_file_path              cesta k mean file souboru
            string train_db_path        cesta k slozce s trenovacimi obrazky
            string validate_db_path     cesta k slozce s validovanymi obrazky
        }

        Returns:
            struct {
                int status              200 = OK
                string statusMessage    Textovy popis stavu
                int data                Vraci id nove neuronove site
            }
        """

        query = """
            INSERT INTO neural_network (`model_id`, `description`, `pretrained_model_path`, `mean_file_path`, `train_db_path`, `validate_db_path`)
            VALUE (%(model_id)s, %(description)s, %(pretrained_model_path)s, %(mean_file_path)s, %(train_db_path)s, %(validate_db_path)s)
        """
        self.cursor.execute(query, param)
        neural_network_id = self.cursor.lastrowid
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
            model_id                    ID modelu z ktereho neuronova sit vychazi
            description                 Popisek
            pretrained_model_path       cesta k predtrenovanemu modelu
            mean_file_path              cesta k mean file souboru
            string train_db_path        cesta k slozce s trenovacimi obrazky
            string validate_db_path     cesta k slozce s validovanymi obrazky
        }

        Returns:
            struct {
                int status              200 = OK
                string statusMessage    Textovy popis stavu
                bool data               Success
            }
        """

        filterDict = {
            "model_id":                 "model_id = %(model_id)s",
            "description":              "description = %(description)s",
            "pretrained_model_path":    "pretrained_model_path = %(pretrained_model_path)s",
            "mean_file_path":           "mean_file_path = %(mean_file_path)s",
            "train_db_path":            "train_db_path = %(train_db_path)s",
            "validate_db_path":         "validate_db_path = %(validate_db_path)s",
        }
        
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

        return True
    #enddef
    
#endclass

