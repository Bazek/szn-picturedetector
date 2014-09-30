#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# DESCRIPTION
#   Fronta neuronovych siti cekajici na uceni
#

from rpc_backbone.decorators import rpcStatusDecorator, MySQL_master, MySQL_slave
from lib.backend import Backend

class LearningQueueBackend(Backend):
    @rpcStatusDecorator('learning_queue.get', 'S:i')
    @MySQL_slave
    def get(self, neural_network_id):
        query = "SELECT neural_network_id, picture_set_id, start_iteration, status FROM learning_queue WHERE %s"
        self.cursor.execute(query, id)
        queue = self.cursor.fetchone()
        
        if not queue:
            raise Exception(404, "Learning queue for neural network #%d not found" % neural_network_id)
        #endif
        
        return queue
    #enddef
    
    @rpcStatusDecorator('learning_queue.list', 'S:')
    @MySQL_slave
    def list(self):
        query = "SELECT neural_network_id, picture_set_id, start_iteration, status FROM learning_queue"
        self.cursor.execute(query)
        queues = self.cursor.fetchall()
        return queues
    #enddef
    
    @rpcStatusDecorator('learning_queue.add', 'S:S')
    @MySQL_master
    def add(self, param):
        query = """
            INSERT INTO learning_queue (`neural_network_id`, `picture_set_id`, `start_iteration`, `status`)
            VALUE (%(neural_network_id)s, %(picture_set_id)s, %(start_iteration)s, %(status)s)
        """
        self.cursor.execute(query, param)
        model_id = self.cursor.lastrowid
        return model_id
    
    @rpcStatusDecorator('learning_queue.update', 'S:iS')
    @MySQL_master
    def edit(self, neural_network_id, params):
        filterDict = {
            "picture_set_id":       "picture_set_id = %(picture_set_id)s",
            "start_iteration":      "start_iteration = %(start_iteration)s",
            "status":               "status = %(status)s",
        }
        
        SET = self._getFilter(filterDict, params, "SET", ", ")
        params["neural_network_id"] = neural_network_id
        query = """
            UPDATE learning_queue
            """ + SET + """
            WHERE neural_network_id = %(neural_network_id)s
        """
        self.cursor.execute(query, params)
        return True
    #enddef
    
    @rpcStatusDecorator('learning_queue.delete', 'S:i')
    @MySQL_master
    def delete(self, neural_network_id):
        #todo kdyz bude moznost spoustet vice uceni neuronovych siti, tak bude potreba upresnit id neuornove site
        query = "DELETE FROM learning_queue WHERE neural_network_id = %s";
        self.cursor.execute(query, neural_network_id)
        
        if self.cursor.rowcount == 0:
            status, statusMessage = 404, "NeuralNetwork #%d not found." % neural_network_id
            raise Exception(status, statusMessage)
        #endif
        
        return True
    #enddef
    
    @rpcStatusDecorator('learning_queue.deleteLearning', 'S:')
    @MySQL_master
    def deleteLearning(self):
        #todo kdyz bude moznost spoustet vice uceni neuronovych siti, tak bude potreba upresnit id neuornove site
        query = "DELETE FROM learning_queue WHERE status = 'learning'";
        self.cursor.execute(query)
        
        if self.cursor.rowcount == 0:
            status, statusMessage = 404, "NeuralNetwork #%d not found." % neural_network_id
            raise Exception(status, statusMessage)
        #endif
        
        return True
    #enddef
    
    @rpcStatusDecorator('learning_queue.getNext', 'S:')
    @MySQL_master
    def getNext(self):
        query = "SELECT neural_network_id, picture_set_id, start_iteration FROM learning_queue WHERE status = 'waiting' FOR UPDATE"
        self.cursor.execute(query)
        queue_info = self.cursor.fetchone()
        
        if queue_info:
            query = "UPDATE learning_queue SET status = 'learning' WHERE neural_network_id = %s";
            self.cursor.execute(query, queue_info['neural_network_id'])
        #endif
        
        # Prevod None na False, aby to vratilo polozku data
        if not queue_info:
            queue_info = False

        return queue_info
    #enddef
    
#endclass
