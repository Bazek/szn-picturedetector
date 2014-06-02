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
    @MySQL_slave
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
#endclass

