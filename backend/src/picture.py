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

    def _add_pictures_counts(self, picture_sets):
        if type(picture_sets) not in (list, tuple, set):
            picture_sets = [ picture_sets ]
        #endif
        dbg.log("picture_sets: %s", picture_sets, DBG=1)

        if picture_sets:
            picture_sets_dict = {}
            for picture_set in picture_sets:
                picture_set["pictures_counts"] = {}
                for learning_set in self.config.pictures.learning_set_paths.keys():
                    picture_set["pictures_counts"][learning_set] = { "true":0, "false":0 }
                #endfor
                picture_sets_dict[picture_set["id"]] = picture_set
            #endfor
            dbg.log("picture_sets_dict: %s", repr(picture_sets_dict), DBG=1)

            query = """
                SELECT `picture_set_id`, `learning_set`, `learning_subset`, COUNT(id) AS count
                FROM picture
                WHERE picture_set_id IN (%s)
                GROUP BY `picture_set_id`, `learning_set`, `learning_subset`
            """ % ",".join(map(str,picture_sets_dict.keys()))
            self.cursor.execute(query)
            pictures_counts = self.cursor.fetchall()

            dbg.log("pictures_counts: %s", repr(pictures_counts), DBG=1)
            for pictures_count in pictures_counts:
                picture_sets_dict[pictures_count["picture_set_id"]]["pictures_counts"][pictures_count["learning_set"]][pictures_count["learning_subset"]] = pictures_count["count"]
            #endfor
        #endif
    #enddef


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
                    struct pictures_counts {
                        struct training {
                            int true            Pocet trenovacich obrazku z podmnoziny true
                            int false           Pocet trenovacich obrazku z podmnoziny false
                        }
                        struct validation {
                            int true            Pocet validacnich obrazku z podmnoziny true
                            int false           Pocet validacnich obrazku z podmnoziny false
                        }
                        struct testing {
                            int true            Pocet testovacich obrazku z podmnoziny true
                            int false           Pocet testovacich obrazku z podmnoziny false
                        }
                    }
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
        self._add_pictures_counts(picture_sets)
        return picture_sets
    #enddef

    @rpcStatusDecorator('picture_set.get', 'S:i')
    @MySQL_slave
    def get(self, picture_set_id):
        """
        Vrati sadu obrazku podle zadaneho id

        Signature:
            picture_set.get()

        Returns:
            struct {
                int status              200 = OK
                string statusMessage    Textovy popis stavu
                struct data {
                    int id                  Id sady
                    string description      Popisek
                    struct pictures_counts {
                        struct training {
                            int true            Pocet trenovacich obrazku z podmnoziny true
                            int false           Pocet trenovacich obrazku z podmnoziny false
                        }
                        struct validation {
                            int true            Pocet validacnich obrazku z podmnoziny true
                            int false           Pocet validacnich obrazku z podmnoziny false
                        }
                        struct testing {
                            int true            Pocet testovacich obrazku z podmnoziny true
                            int false           Pocet testovacich obrazku z podmnoziny false
                        }
                    }
                }
            }
        """

        query = """
            SELECT `id`, `description`
            FROM picture_set
            WHERE id = %s
        """
        self.cursor.execute(query, picture_set_id)
        picture_set = self.cursor.fetchone()
        if not picture_set:
            raise Exception(404, "Picture set not found")
        #endif
        self._add_pictures_counts(picture_set)
        return picture_set
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

    @rpcStatusDecorator('picture.save', 'S:issB')
    @MySQL_master
    def save(self, picture_set_id, learning_set, learning_subset, data):
        """
        """

        if learning_set not in self.config.pictures.learning_set_paths:
            raise Exception(402, "Unknown learning_set: %s" % learning_set)
        #endif
        if learning_subset not in ("true", "false"):
            raise Exception(402, "Unknown learning_subset: %s" % learning_subset)
        #endif

        # Ulozeni souboru na disk
        path = "%s/%d/%s" % (self.config.pictures.base_path, picture_set_id, self.config.pictures.learning_set_paths[learning_set][learning_subset])
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
            INSERT INTO picture (`picture_set_id`,`learning_set`,`learning_subset`,`hash`)
            VALUE (%s, %s, %s, %s)
        """
        params = (picture_set_id, learning_set, learning_subset, file_name)
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

        # Kontrola parametru
        if "learning_set" in params and params["learning_set"] not in self.config.pictures.learning_set_paths:
            raise Exception(402, "Unknown learning_set: %s" % params["learning_set"])
        #endif
        if "learning_subset" in params and params["learning_subset"] not in ("true", "false"):
            raise Exception(402, "Unknown learning_subset: %s" % params["learning_subset"])
        #endif

        filterDict = {
            "picture_set_id":   "picture_set_id = %(picture_set_id)s",
            "learning_set":     "learning_set = %(learning_set)s",
            "learning_subset":  "learning_subset = %(learning_subset)s",
        }
        params["picture_set_id"] = picture_set_id
        WHERE = self._getFilter(filterDict, params)

        query = """
            SELECT `id`, `picture_set_id`, `learning_set`, `learning_subset`, `hash`
            FROM picture
            """ + WHERE + """
            ORDER BY id ASC
        """
        self.cursor.execute(query, params)
        pictures = self.cursor.fetchall()

        return pictures
    #enddef

#endclass

