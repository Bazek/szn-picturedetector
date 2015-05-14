#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# DESCRIPTION
#   Fronta neuronovych siti cekajici na uceni
#

from rpc_backbone.decorators import rpcStatusDecorator, MySQL_master, MySQL_slave
from lib.backend import Backend
from dbglog import dbg

class LearningQueueBackend(Backend):
    @rpcStatusDecorator('learning_queue.get', 'S:i')
    @MySQL_slave
    def get(self, neural_network_id):
        """
        Vrátí informace o záznamech učení, které jsou naplánovány pro neuronovou
        síť, která je specifikována jejím identifikátorem předaným jako parametr
        metody. Výstupem je tedy pole záznamů, které obsahují informace z databáze.
        Informace jsou v poli pod shodným klíčem jako je název sloupce.
        
        Signature:
            learning_queue.get(int neural_network_id)

        @param {
            int neural_network_id       ID neuronove site
        }

        Returns:
            struct {
                int status              200 = OK
                string statusMessage    Textovy popis stavu
                array data {
                    int neural_network_id   ID neuronove site
                    int picture_set_id      ID setu obrazku
                    int start_iteration     Pocatecni iterace
                    string status           Status uceni
                }
            }
        """
        query = "SELECT neural_network_id, picture_set_id, start_iteration, status FROM learning_queue WHERE neural_network_id = %s"
        self.cursor.execute(query, neural_network_id)
        queue = self.cursor.fetchone()
        
        if not queue:
            raise Exception(404, "Learning queue for neural network #%d not found" % neural_network_id)
        #endif
        
        return queue
    #enddef
    
    @rpcStatusDecorator('learning_queue.list', 'S:')
    @MySQL_slave
    def list(self):
        """
        Metoda vypisuje seznam informací pro všechny záznamy ve frontě pro učení
        nových neuronových sítí. Nevyžaduje žádný parametr a návratovou hodnotou
        je pole, které obsahuje informace načtené z databáze a hodnoty jsou uloženy
        vždy pod klíčem, který má stejný název jako sloupec v databázi.
        
        Signature:
            learning_queue.list()

        @param {
        }

        Returns:
            struct {
                int status              200 = OK
                string statusMessage    Textovy popis stavu
                array data {
                    int neural_network_id   ID neuronove site
                    int picture_set_id      ID setu obrazku
                    int start_iteration     Pocatecni iterace
                    string status           Status uceni
                }
            }
        """
        query = "SELECT neural_network_id, picture_set_id, start_iteration, status FROM learning_queue"
        self.cursor.execute(query)
        queues = self.cursor.fetchall()
        return queues
    #enddef
    
    @rpcStatusDecorator('learning_queue.add', 'S:S')
    @MySQL_master
    def add(self, param):
        """
        Pomocí této metody lze přidávat nové záznamy do fronty pro učení. Očekáván
        je jeden parametr typu pole. V tomto poli musí být uloženy hodnoty pro započatí
        učení a musí být uloženy pod konkrétními klíči, které mají stejné názvy jako
        sloupečky v příslušné databázové tabulce learning_queue.
        
        Signature:
            learning_queue.add()

        @param {
            neural_network_id               ID neuronove site
            picture_set_id                  ID setu obrazku
            start_iteration                 Pocatecni iterace
            status                          Status uceni
        }

        Returns:
            struct {
                int status              200 = OK
                string statusMessage    Textovy popis stavu
                array data {
                    int neural_network_id   ID neuronove site
                    int picture_set_id      ID setu obrazku
                    int start_iteration     Pocatecni iterace
                    string status           Status uceni
                }
            }
        """
        query = """
            INSERT INTO learning_queue (`neural_network_id`, `picture_set_id`, `start_iteration`, `status`)
            VALUE (%(neural_network_id)s, %(picture_set_id)s, %(start_iteration)s, %(status)s)
        """
        self.cursor.execute(query, param)
        model_id = self.cursor.lastrowid
        return model_id
    
    @rpcStatusDecorator('learning_queue.edit', 'S:iS')
    @MySQL_master
    def edit(self, neural_network_id, params):
        """
        Metoda sloužící k editaci záznamu z fronty pro učení.
        
        Signature:
            learning_queue.edit(int neural_network_id, struct params)

        @param {
            neural_network_id               ID neuronove site
            params                          pole s hodnotami
        }

        Returns:
            struct {
                int status              200 = OK
                string statusMessage    Textovy popis stavu
                bool data               True pri uspesne editaci
            }
        """
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
        """
        Tato metoda se používá k mazání záznamu z fronty pro učení. Očekává dva parametry, kterými
        se identifikuje záznam v databázi. Těmito parametry jsou identifikátor neuronové sítě
        a identifikátor databáze fotografií.
        
        Signature:
            learning_queue.delete(int neural_network_id)

        @param {
            neural_network_id           ID neuronove site
        }

        Returns:
            struct {
                int status              200 = OK
                string statusMessage    Textovy popis stavu
                bool data               True pri uspesnem provedeni dotazu
            }
        """
        #todo musi se upresnit i obrazky s kterymi
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
        """
        Aktuálně může v systému probíhat pouze jedna instance učení neuronoví sítě
        a proto byla vytvořena tato metoda, která nevyžaduje žádné parametry a je
        schopna odstranit právě učený záznam. Této metody je využito v případě, kdy běžící
        Daemon dostane signál SIGABRT, což znamená že má ukončit aktuálně učenou
        instanci klasifikátoru a případně začít učení klasifikátoru jiného, pokud ve frontě
        pro učení neuronových sítí je nějaký záznam ve stavu waiting.
        
        Signature:
            learning_queue.deleteLearning()

        @param {
        }

        Returns:
            struct {
                int status              200 = OK
                string statusMessage    Textovy popis stavu
                bool data               True pri uspesnem provedeni dotazu
            }
        """
        #todo kdyz bude moznost spoustet vice uceni neuronovych siti, tak bude potreba upresnit id neuornove site
        query = "DELETE FROM learning_queue WHERE status = 'learning'";
        self.cursor.execute(query)
        
        if self.cursor.rowcount == 0:
            status, statusMessage = 404, "Learning is not running"
            raise Exception(status, statusMessage)
        #endif
        
        return True
    #enddef
    
    @rpcStatusDecorator('learning_queue.getNext', 'S:')
    @MySQL_master
    def getNext(self):
        """
        Daemon, který neučí žádnou neuronovou síť se cyklicky s daným intervalem dotazuje
        Backendu jestli existuje ve frontě pro učení nějaká neuronová síť, kterou by mohl
        zpracovat. 
        Metoda neočekává žádný parametr. Pokud existuje neuronová síť, tak vrátí načtené
        informace o tomto záznamu učení ve formě pole a pokud žádná neuronová síť
        není ve frontě ve stavu waiting, tak vrátí hodnotu False.
        
        Signature:
            learning_queue.getNext()

        @param {
        }

        Returns:
            struct {
                int status              200 = OK
                string statusMessage    Textovy popis stavu
                array data {
                    int neural_network_id   ID neuronove site
                    int picture_set_id      ID setu obrazku
                    int start_iteration     Pocatecni iterace
                    string status           Status uceni
                }
            }
        """
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
