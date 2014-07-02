#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# DESCRIPTION
#   Prace s neuronovou siti
#

from dbglog import dbg

from rpc_backbone.decorators import rpcStatusDecorator, MySQL_master, MySQL_slave
from lib.backend import Backend


class NeuralNetworkBackend(Backend):
    """
    Trida pro praci s neuronovou siti
    """

    @rpcStatusDecorator('neural_network.function', 'S:,S:b')
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

        return param
    #enddef

    @rpcStatusDecorator('neural_network.get', 'S:i')
    @MySQL_slave
    def get(self, id):
        """
        Testovaci funkce

        Signature:
            neural_network.get(integer id)

        @id                 neural_network_id

        Returns:
            struct {
                int status              200 = OK
                string statusMessage    Textovy popis stavu
                struct data {
                    integer id              neural_network_id
                    string description      description
                    string configuration    konfigurace
                }
            }
        """

        query = """
            SELECT id, description, configuration
            FROM neural_network
            WHERE id = %s
        """
        self.cursor.execute(query, id)
        neural_network = self.cursor.fetchone()
        if not neural_network:
            raise Exception(404, "Neural network not found")
        #endif
        return neural_network
    #enddef

    @rpcStatusDecorator('neural_network.add', 'S:S')
    @MySQL_master
    def add(self, param):
        """
        Testovaci funkce

        Signature:
            neural_network.add(struct param)

        @param {
            description     Popisek
            configuration   Konfigurace neuronove site
        }

        Returns:
            struct {
                int status              200 = OK
                string statusMessage    Textovy popis stavu
                int data                Vraci id nove neuronove site
            }
        """

        query = """
            INSERT INTO neural_network (`description`, `configuration`)
            VALUE (%(description)s, %(configuration)s)
        """
        self.cursor.execute(query, param)
        neural_network_id = self.cursor.lastrowid
        return neural_network_id
    #enddef
#endclass

