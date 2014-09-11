#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# DESCRIPTION
#   Konfigurace pro trenovani neuronovych siti
#

from rpc_backbone.decorators import rpcStatusDecorator, MySQL_master, MySQL_slave
from lib.backend import Backend

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
                    integer id                      neural network id
                    string net
                    integer stepsize
                    integer display
                    integer max_iter
                    integer test_iter
                    integer test_interval
                    bool test_compute_loss
                    float base_lr
                    string lr_policy
                    float gamma
                    float momentum
                    float weight_decay
                    float power
                    integer snapshot
                    string snapshot_prefix
                    bool snapshot_after_train
                    bool snapshot_diff
                    integer solver_mode
                    integer device_id
                    integer random_seed
                    bool debug_info
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
    
#endclass