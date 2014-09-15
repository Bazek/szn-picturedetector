#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# DESCRIPTION
#   Konfigurace pro trenovani neuronovych siti
#

from rpc_backbone.decorators import rpcStatusDecorator, MySQL_master, MySQL_slave
from lib.backend import Backend
from dbglog import dbg

class SolverConfigBackend(Backend):
    @rpcStatusDecorator('solver_config.get', 'S:i')
    @MySQL_slave
    def get(self, id):
        """
        Funkce pro precteni solver konfigurace dle zadaneho ID neuronove site

        Signature:
            daemon.get(integer id)

        @id                 neural_network_id

        Returns:
            struct {
                int status                          200 = OK
                string statusMessage                Textovy popis stavu
                struct data {
                    integer id                      id neuronove site
                    string net                      cesta k definici modelu neuronove site
                    integer stepsize                velikost kroku pro uceni
                    integer display                 pocet iteraci po kterych se am vypisovat loss informace (0 = vypnuto)
                    integer max_iter                maximalni pocet iteraci uceni
                    integer test_iter               pocet iteraci pro otestovani neuronove site (validace)
                    integer test_interval           pocet iteraci mezi dvemi testovacimi fazemi
                    bool test_compute_loss          testovani vypoceteneho loss
                    float base_lr                   zakladni hodnota miry uceni
                    string lr_policy                mira utlumu uceni
                    float gamma                     parametr pro vypocet miry uceni
                    float momentum                  momentum
                    float weight_decay              hodnota rozpadu
                    float power                     parametr pro vypocet miry uceni
                    integer snapshot                interval pro ukladani naucenych snapshotu
                    string snapshot_prefix          prefix nazvu souboru pro snapshot
                    bool snapshot_after_train       vytvoreni snapshotu po skonceni uceni (dosazeno maximum iteraci)
                    bool snapshot_diff              priznak ukladani diff do snapshotu (zvetsuje velikost)
                    integer solver_mode             vyber hardware pro uceni neuronove site (CPU, GPU)
                    integer device_id               id grafickeho zarizeni pro uceni neuronove site
                    integer random_seed             nastaveni zakladnu pro nahodna cisla
                    bool debug_info                 priznak pro zapnuti ladicich informaci
                }
            }
        """

        query = """
            SELECT *
            FROM solver_config
            WHERE neural_network_id = %s
        """
        self.cursor.execute(query, id)
        solver_config = self.cursor.fetchone()
        #cursor.close()
        
        if not solver_config:
            raise Exception(404, "Solver config not found")
        #endif
        
        return solver_config
    #enddef
    
    @rpcStatusDecorator('solver_config.list', 'S:')
    @MySQL_slave
    def list(self):
        """
        Vylistuje vsechny konfigurace solveru neuronovych siti

        Signature:
            solver_config.list()

        Returns:
            struct {
                int status                          200 = OK
                string statusMessage                Textovy popis stavu
                struct data {
                    integer id                      id neuronove site
                    string net                      cesta k definici modelu neuronove site
                    integer stepsize                velikost kroku pro uceni
                    integer display                 pocet iteraci po kterych se am vypisovat loss informace (0 = vypnuto)
                    integer max_iter                maximalni pocet iteraci uceni
                    integer test_iter               pocet iteraci pro otestovani neuronove site (validace)
                    integer test_interval           pocet iteraci mezi dvemi testovacimi fazemi
                    bool test_compute_loss          testovani vypoceteneho loss
                    float base_lr                   zakladni hodnota miry uceni
                    string lr_policy                mira utlumu uceni
                    float gamma                     parametr pro vypocet miry uceni
                    float momentum                  momentum
                    float weight_decay              hodnota rozpadu
                    float power                     parametr pro vypocet miry uceni
                    integer snapshot                interval pro ukladani naucenych snapshotu
                    string snapshot_prefix          prefix nazvu souboru pro snapshot
                    bool snapshot_after_train       vytvoreni snapshotu po skonceni uceni (dosazeno maximum iteraci)
                    bool snapshot_diff              priznak ukladani diff do snapshotu (zvetsuje velikost)
                    integer solver_mode             vyber hardware pro uceni neuronove site (CPU, GPU)
                    integer device_id               id grafickeho zarizeni pro uceni neuronove site
                    integer random_seed             nastaveni zakladnu pro nahodna cisla
                    bool debug_info                 priznak pro zapnuti ladicich informaci
                }
            }
        """

        query = """
            SELECT *
            FROM solver_config
        """
        self.cursor.execute(query)
        models = self.cursor.fetchall()
        return models
    #enddef
    
    @rpcStatusDecorator('solver_config.add', 'S:S')
    @MySQL_master
    def add(self, params):
        """
        Pridani nove konfigurace solveru neuronovych siti

        Signature:
            solver_config.add(struct param)

        @param {
            integer neural_network_id       id neuronove site
            string net                      cesta k definici modelu neuronove site
            integer stepsize                velikost kroku pro uceni
            integer display                 pocet iteraci po kterych se am vypisovat loss informace (0 = vypnuto)
            integer max_iter                maximalni pocet iteraci uceni
            integer test_iter               pocet iteraci pro otestovani neuronove site (validace)
            integer test_interval           pocet iteraci mezi dvemi testovacimi fazemi
            bool test_compute_loss          testovani vypoceteneho loss
            float base_lr                   zakladni hodnota miry uceni
            string lr_policy                mira utlumu uceni
            float gamma                     parametr pro vypocet miry uceni
            float momentum                  momentum
            float weight_decay              hodnota rozpadu
            float power                     parametr pro vypocet miry uceni
            integer snapshot                interval pro ukladani naucenych snapshotu
            string snapshot_prefix          prefix nazvu souboru pro snapshot
            bool snapshot_after_train       vytvoreni snapshotu po skonceni uceni (dosazeno maximum iteraci)
            bool snapshot_diff              priznak ukladani diff do snapshotu (zvetsuje velikost)
            integer solver_mode             vyber hardware pro uceni neuronove site (CPU, GPU)
            integer device_id               id grafickeho zarizeni pro uceni neuronove site
            integer random_seed             nastaveni zakladnu pro nahodna cisla
            bool debug_info                 priznak pro zapnuti ladicich informaci
        }

        Returns:
            struct {
                int status              200 = OK
                string statusMessage    Textovy popis stavu
                int data                Vraci id nove konfigurace solveru
            }
        """

        if 'neural_network_id' not in params:
            raise Exception(402, "Neural network id is missing")
        #endif

        filterDict = {
            "neural_network_id":            "neural_network_id = %(neural_network_id)s",
            "net":                          "net = %(net)s",
            "stepsize":                     "stepsize = %(stepsize)s",
            "display":                      "display = %(display)s",
            "max_iter":                     "max_iter = %(max_iter)s",
            "test_iter":                    "test_iter = %(test_iter)s",
            "test_interval":                "test_interval = %(test_interval)s",
            "test_compute_loss":            "test_compute_loss = %(test_compute_loss)s",
            "base_lr":                      "base_lr = %(base_lr)s",
            "lr_policy":                    "lr_policy = %(lr_policy)s",
            "gamma":                        "gamma = %(gamma)s",
            "momentum":                     "momentum = %(momentum)s",
            "weight_decay":                 "weight_decay = %(weight_decay)s",
            "power":                        "power = %(power)s",
            "snapshot":                     "snapshot = %(snapshot)s",
            "snapshot_prefix":              "snapshot_prefix = %(snapshot_prefix)s",
            "snapshot_after_train":         "snapshot_after_train = %(snapshot_after_train)s",
            "snapshot_diff":                "snapshot_diff = %(snapshot_diff)s",
            "solver_mode":                  "solver_mode = %(solver_mode)s",
            "device_id":                    "device_id = %(device_id)s",
            "random_seed":                  "random_seed = %(random_seed)s",
            "debug_info":                   "debug_info = %(debug_info)s",
        }
        
        SET = self._getFilter(filterDict, params, "SET", ", ")
        query = """
            INSERT INTO solver_config
            """ + SET + """
        """
        dbg.log(query, INFO=3)
        self.cursor.execute(query, params)
        model_id = self.cursor.lastrowid
        return model_id
    #enddef
    
    @rpcStatusDecorator('solver_config.edit', 'S:iS')
    @MySQL_master
    def edit(self, neural_network_id, params):
        """
        Upraveni existujici konfigurace solveru neuronovych siti

        Signature:
            solver_config.edit(struct param)

        @param {
            string net                      cesta k definici modelu neuronove site
            integer stepsize                velikost kroku pro uceni
            integer display                 pocet iteraci po kterych se am vypisovat loss informace (0 = vypnuto)
            integer max_iter                maximalni pocet iteraci uceni
            integer test_iter               pocet iteraci pro otestovani neuronove site (validace)
            integer test_interval           pocet iteraci mezi dvemi testovacimi fazemi
            bool test_compute_loss          testovani vypoceteneho loss
            float base_lr                   zakladni hodnota miry uceni
            string lr_policy                mira utlumu uceni
            float gamma                     parametr pro vypocet miry uceni
            float momentum                  momentum
            float weight_decay              hodnota rozpadu
            float power                     parametr pro vypocet miry uceni
            integer snapshot                interval pro ukladani naucenych snapshotu
            string snapshot_prefix          prefix nazvu souboru pro snapshot
            bool snapshot_after_train       vytvoreni snapshotu po skonceni uceni (dosazeno maximum iteraci)
            bool snapshot_diff              priznak ukladani diff do snapshotu (zvetsuje velikost)
            integer solver_mode             vyber hardware pro uceni neuronove site (CPU, GPU)
            integer device_id               id grafickeho zarizeni pro uceni neuronove site
            integer random_seed             nastaveni zakladnu pro nahodna cisla
            bool debug_info                 priznak pro zapnuti ladicich informaci
        }
        
        Returns:
            struct {
                int status              200 = OK
                string statusMessage    Textovy popis stavu
                bool data               Success
            }
        """

        filterDict = {
            "net":                          "net = %(net)s",
            "stepsize":                     "stepsize = %(stepsize)s",
            "display":                      "display = %(display)s",
            "max_iter":                     "max_iter = %(max_iter)s",
            "test_iter":                    "test_iter = %(test_iter)s",
            "test_interval":                "test_interval = %(test_interval)s",
            "test_compute_loss":            "test_compute_loss = %(test_compute_loss)s",
            "base_lr":                      "base_lr = %(base_lr)s",
            "lr_policy":                    "lr_policy = %(lr_policy)s",
            "gamma":                        "gamma = %(gamma)s",
            "momentum":                     "momentum = %(momentum)s",
            "weight_decay":                 "weight_decay = %(weight_decay)s",
            "power":                        "power = %(power)s",
            "snapshot":                     "snapshot = %(snapshot)s",
            "snapshot_prefix":              "snapshot_prefix = %(snapshot_prefix)s",
            "snapshot_after_train":         "snapshot_after_train = %(snapshot_after_train)s",
            "snapshot_diff":                "snapshot_diff = %(snapshot_diff)s",
            "solver_mode":                  "solver_mode = %(solver_mode)s",
            "device_id":                    "device_id = %(device_id)s",
            "random_seed":                  "random_seed = %(random_seed)s",
            "debug_info":                   "debug_info = %(debug_info)s",
        }
        
        SET = self._getFilter(filterDict, params, "SET", ", ")
        params["neural_network_id"] = neural_network_id
        query = """
            UPDATE solver_config
            """ + SET + """
            WHERE neural_network_id = %(neural_network_id)s
        """
        self.cursor.execute(query, params)
        return True
    #enddef
    
    @rpcStatusDecorator('solver_config.delete', 'S:i')
    @MySQL_master
    def delete(self, neural_network_id):
        """
        Odstrani celou konfiguraci solveru neuronove site

        Signature:
            solver_config.delete(int model_id)

        @neural_network_id           id neuronove site

        Returns:
            struct {
                int status              200 = OK
                string statusMessage    Textovy popis stavu
                bool data               Uspesne smazano
            }
        """

        query = """
            DELETE FROM solver_config
            WHERE neural_network_id = %s
        """
        self.cursor.execute(query, neural_network_id)
        if self.cursor.rowcount == 0:
            status, statusMessage = 404, "Solver config for NeuralNetwork #%d not found." % neural_network_id
            raise Exception(status, statusMessage)
        #endif

        return True
    #enddef
    
#endclass