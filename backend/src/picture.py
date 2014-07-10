#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# DESCRIPTION
#   Prace s obrazky
#

from dbglog import dbg

from rpc_backbone.decorators import rpcStatusDecorator, MySQL_master, MySQL_slave
from lib.backend import Backend

from hashlib import md5
import os, shutil


class PictureSetBackend(Backend):
    """
    Trida pro praci s ucici sadou obrazku
    """

    @rpcStatusDecorator('picture_set.add', 'S:S')
    @MySQL_master
    def add(self, picture_set):
        """
        Vytvori novou (prazdnou) ucici sadu obrazku

        Signature:
            picture_set.add(struct picture_set)

        @picture_set {
            string description      Popisek
        }

        Returns:
            struct {
                int status              200 = OK
                string statusMessage    Textovy popis stavu
                int data                Vraci id nove sady
            }
        """

        query = """
            INSERT INTO picture_set (`description`)
            VALUE (%(description)s)
        """
        self.cursor.execute(query, picture_set)
        picture_set_id = self.cursor.lastrowid

        path = "%s/%d" % (self.config.pictures.base_path, picture_set_id)
        if os.path.exists(path):
            dbg.log("Path already exists: %s", path, WARN=3)
        else:
            dbg.log("Creating path: %s", path, INFO=1)
            os.makedirs(path)
        #endif

        return picture_set_id
    #enddef

    @rpcStatusDecorator('picture_set.list', 'S:')
    @MySQL_slave
    def list(self):
        """
        Vylistuje vsechny ucici sady obrazku

        Signature:
            picture_set.list()

        Returns:
            struct {
                int status              200 = OK
                string statusMessage    Textovy popis stavu
                array data {
                    int id                  Id sady
                    string description      Popisek
                }
            }
        """

        query = """
            SELECT `id`, `description`
            FROM picture_set
            ORDER BY id ASC
        """
        self.cursor.execute(query)
        picture_sets = self.cursor.fetchall()

        return picture_sets
    #enddef

    @rpcStatusDecorator('picture_set.delete', 'S:i')
    @MySQL_master
    def delete(self, picture_set_id):
        """
        Odstrani celou ucici sadu i s obrazky

        Signature:
            picture_set.delete(int picture_set_id)

        @picture_set_id             Id sady

        Returns:
            struct {
                int status              200 = OK
                string statusMessage    Textovy popis stavu
                bool data               Uspesne smazano
            }
        """

        # Smazani metadat z DB
        query = """
            DELETE FROM picture_set
            WHERE id = %s
        """
        self.cursor.execute(query, picture_set_id)
        if self.cursor.rowcount == 0:
            status, statusMessage = 404, "PictureSet #%d not found." % picture_set_id
            raise Exception(status, statusMessage)
        #endif

        # Smazani souboru na disku
        path = "%s/%d" % (self.config.pictures.base_path, picture_set_id)
        shutil.rmtree(path, True)

        return True
    #enddef

#endclass


class PictureBackend(Backend):
    """
    Trida pro praci s obrazky
    """

    @rpcStatusDecorator('picture.save', 'S:isB')
    @MySQL_master
    def save(self, picture_set_id, learning_set, data):
        """
        """

        if learning_set not in self.config.pictures.learning_set_paths:
            raise Exception(402, "Unknown learning_set: %s" % learning_set)
        #endif

        # Ulozeni souboru na disk
        path = "%s/%d/%s" % (self.config.pictures.base_path, picture_set_id, self.config.pictures.learning_set_paths[learning_set])
        dbg.log("picture.save: Path=%s", path, DBG=1)
        if not os.path.exists(path):
            dbg.log("Creating path: %s", path, INFO=1)
            os.makedirs(path)
        #endif
        file_name = md5(data).hexdigest()
        file_path = "%s/%s" % (path, file_name)
        f = open(file_path, "w")
        f.write(data)
        f.close()
        dbg.log("Picture saved successfully: %s", file_path, INFO=3)

        # Ulozeni metadat do DB
        query = """
            INSERT INTO picture (`picture_set_id`,`learning_set`,`hash`)
            VALUE (%s, %s, %s)
        """
        params = (picture_set_id, learning_set, file_name)
        self.cursor.execute(query, params)
        picture_id = self.cursor.lastrowid

        return {
            "id":   picture_id,
            "hash": file_name,
        }
    #enddef

    @rpcStatusDecorator('picture.list', 'S:i,S:iS')
    @MySQL_slave
    def list(self, picture_set_id, params={}):
        """
        """

        if "learning_set" in params and params["learning_set"] not in self.config.pictures.learning_set_paths:
            raise Exception(402, "Unknown learning_set: %s" % params["learning_set"])
        #endif

        filterDict = {
            "picture_set_id":   "picture_set_id = %(picture_set_id)s",
            "learning_set":     "learning_set = %(learning_set)s",
        }
        params["picture_set_id"] = picture_set_id
        WHERE = self._getFilter(filterDict, params)

        query = """
            SELECT `id`, `picture_set_id`, `learning_set`, `hash`
            FROM picture
            """ + WHERE + """
           ORDER BY id ASC
        """
        self.cursor.execute(query, params)
        picture_sets = self.cursor.fetchall()

        return picture_sets
    #enddef

#endclass

