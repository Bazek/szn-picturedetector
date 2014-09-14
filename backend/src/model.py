#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# DESCRIPTION
#   Modely pro neuoronove site
#

from rpc_backbone.decorators import rpcStatusDecorator, MySQL_master, MySQL_slave
from lib.backend import Backend

class ModelBackend(Backend):
    @rpcStatusDecorator('model.get', 'S:i')
    @MySQL_slave
    def get(self, id):
        """
        Funkce pro precteni dat o modelu dle zadaneho ID modelu

        Signature:
            model.get(integer id)

        @id                 model_id

        Returns:
            struct {
                int status                          200 = OK
                string statusMessage                Textovy popis stavu
                struct data {
                    integer id                      neural network id
                    string name                     nazev modelu
                    string description              description
                    string model_config_path        cesta k souboru s konfiguraci modelu
                }
            }
        """

        query = """
            SELECT id, name, description, model_config_path
            FROM model
            WHERE id = %s
        """
        self.cursor.execute(query, id)
        model = self.cursor.fetchone()
        if not model:
            raise Exception(404, "Model not found")
        #endif
        return model
    #enddef

    @rpcStatusDecorator('model.list', 'S:')
    @MySQL_slave
    def list(self):
        """
        Vylistuje vsechny modely

        Signature:
            model.list()

        Returns:
            struct {
                int status                          200 = OK
                string statusMessage                Textovy popis stavu
                array data {
                    integer id                      neural network id
                    string name                     nazev modelu
                    string description              description
                    string model_config_path        cesta k souboru s konfiguraci modelu
                }
            }
        """

        query = """
            SELECT id, name, description, model_config_path
            FROM model
        """
        self.cursor.execute(query)
        models = self.cursor.fetchall()
        return models
    #enddef

    @rpcStatusDecorator('model.add', 'S:S')
    @MySQL_master
    def add(self, param):
        """
        Pridani noveho modelu pro neuronove site

        Signature:
            model.add(struct param)

        @param {
            string name                     nazev modelu
            string description              description
            string model_config_path        cesta k souboru s konfiguraci modelu
        }

        Returns:
            struct {
                int status              200 = OK
                string statusMessage    Textovy popis stavu
                int data                Vraci id noveho modelu
            }
        """

        query = """
            INSERT INTO model (`name`, `description`, `model_config_path`)
            VALUE (%(name)s, %(description)s, %(model_config_path)s)
        """
        self.cursor.execute(query, param)
        model_id = self.cursor.lastrowid
        return model_id
    #enddef

    @rpcStatusDecorator('model.edit', 'S:iS')
    @MySQL_master
    def edit(self, model_id, params):
        """
        Uprava modelu pro neuronove site

        Signature:
            model.edit(int id, struct param)

        @model_id  Id modelu
        @params {
            string name                 nazev modelu
            string description          description
            string model_config_path    cesta k souboru s konfiguraci modelu
        }

        Returns:
            struct {
                int status              200 = OK
                string statusMessage    Textovy popis stavu
                bool data               Success
            }
        """

        filterDict = {
            "name":                     "name = %(name)s",
            "description":              "description = %(description)s",
            "model_config_path":        "model_config_path = %(model_config_path)s",
        }
        
        SET = self._getFilter(filterDict, params, "SET", ", ")
        params["id"] = model_id
        query = """
            UPDATE model
            """ + SET + """
            WHERE id = %(id)s
        """
        self.cursor.execute(query, params)
        return True
    #enddef

    @rpcStatusDecorator('model.delete', 'S:i')
    @MySQL_master
    def delete(self, model_id):
        """
        Odstrani cely model

        Signature:
            model.delete(int model_id)

        @model_id           Id modelu

        Returns:
            struct {
                int status              200 = OK
                string statusMessage    Textovy popis stavu
                bool data               Uspesne smazano
            }
        """

        query = """
            DELETE FROM model
            WHERE id = %s
        """
        self.cursor.execute(query, model_id)
        if self.cursor.rowcount == 0:
            status, statusMessage = 404, "Model #%d not found." % model_id
            raise Exception(status, statusMessage)
        #endif

        return True
    #enddef
    
#endclass