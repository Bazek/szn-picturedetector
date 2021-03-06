#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# DESCRIPTION
#   Prace s obrazky
#

from dbglog import dbg
import metaserver.fastrpc as server

from rpc_backbone.decorators import rpcStatusDecorator, MySQL_master, MySQL_slave
from lib.backend import Backend

from hashlib import md5
import shutil


class PictureSetBackend(Backend):
    """
    Trida pro praci s ucici sadou obrazku
    """

    def _add_learning_subsets(self, picture_sets):
        """
        Pomocná interní metoda, která očekává jako vstupní parametr pole s identifikátory
        databází fotografií a vrací pole, kde jsou přidány informace kolik je fotografií
        v jednotlivých kategoriích a sekcích v rámci vybraných databází fotografií.
        Tato metoda je využita v administračním rozhraní, kde na stránce s databázemi
        fotografií zobrazuje informace kolik fotografií je v daných kategoriích a sekcích.
        Administrátor na základě této informace může doplňovat fotografie do sekcí, které
        obsahují málo fotografií.
        """
        if type(picture_sets) not in (list, tuple, set):
            picture_sets = [ picture_sets ]
        #endif
        dbg.log("picture_sets: %s", str(picture_sets), DBG=1)

        if picture_sets:
            picture_sets_dict = {}
            for picture_set in picture_sets:
                picture_set["pictures_counts"] = {}
                picture_set["learning_subsets"] = {}
                for learning_set in self.config.pictures.LEARNING_SETS:
                    picture_set["pictures_counts"][learning_set] = {}
                #endfor
                picture_sets_dict[picture_set["id"]] = picture_set
            #endfor
            dbg.log("picture_sets_dict: %s", repr(picture_sets_dict), DBG=1)

            query = """
                SELECT learning_subset.picture_set_id AS picture_set_id, learning_set.id AS learning_set, learning_subset.id AS learning_subset_id, learning_subset.name AS learning_subset_name, COUNT(picture.id) AS count
                FROM learning_set JOIN learning_subset LEFT JOIN picture ON (picture.learning_set=learning_set.id AND picture.picture_set_id=learning_subset.picture_set_id AND picture.learning_subset_id=learning_subset.id)
                WHERE learning_subset.picture_set_id IN (%s)
                GROUP BY learning_subset.picture_set_id, learning_set.id, learning_subset.id
            """ % ",".join(map(str,picture_sets_dict.keys()))
            self.cursor.execute(query)
            pictures_counts = self.cursor.fetchall()

            dbg.log("pictures_counts: %s", repr(pictures_counts), DBG=1)
            for pictures_count in pictures_counts:
                picture_sets_dict[pictures_count["picture_set_id"]]["pictures_counts"][pictures_count["learning_set"]][pictures_count["learning_subset_name"]] = pictures_count["count"]
                picture_sets_dict[pictures_count["picture_set_id"]]["learning_subsets"][pictures_count["learning_subset_name"]] = pictures_count["learning_subset_id"]
            #endfor
        #endif

        return picture_sets
    #enddef


    @rpcStatusDecorator('picture_set.add', 'S:SA')
    @MySQL_master
    def add(self, picture_set, learning_subsets):
        """
        Vytvori novou (prazdnou) ucici sadu obrazku

        Signature:
            picture_set.add(struct picture_set, array learning_subsets)

        @picture_set {
            string description      Popisek
        }
        @learning_subsets           Pole nazvu ucicich podmnozin (>=2)

        Returns:
            struct {
                int status              200 = OK
                string statusMessage    Textovy popis stavu
                int data                Vraci id nove sady
            }
        """

        if not learning_subsets:  raise Exception(402, "Empty learning_subsets!")
        if len(learning_subsets) == 1:  raise Exception(402, "Only one learning subset?")

        # Ulozeni nove ucici sady do DB
        query = """
            INSERT INTO picture_set (`description`)
            VALUE (%(description)s)
        """
        self.cursor.execute(query, picture_set)
        picture_set_id = self.cursor.lastrowid
        # Ulozeni ucicich podmnozin pro danou sadu
        # TODO: Udelat na jeden dotaz
        for learning_subset in learning_subsets: 
            query = """
                INSERT INTO learning_subset (`picture_set_id`, `name`)
                VALUE (%s, %s)
            """
            self.cursor.execute(query, (picture_set_id, learning_subset))
        #endfor

        # Vytvoreni prazdne adresarove struktury
        base_path = "%s/%d" % (self.config.pictures.base_path, picture_set_id)
        self._makepath(base_path)
        for learning_set in self.config.pictures.LEARNING_SETS:
            learning_set_path = "%s/%s" % (base_path, learning_set)
            self._makepath(learning_set_path)
            for learning_subset in learning_subsets:
                learning_subset_path = "%s/%s" % (learning_set_path, learning_subset)
                self._makepath(learning_subset_path)
            #endfor
        #endfor

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
                        struct training         Slovnikova struktura, kde klicem je nazev ucici podmnoziny
                                                a hodnotou je pocet trenovacich obrazku z teto podmnoziny
                        struct validation       Slovnikova struktura, kde klicem je nazev ucici podmnoziny
                                                a hodnotou je pocet validacnich obrazku z teto podmnoziny
                        struct testing          Slovnikova struktura, kde klicem je nazev ucici podmnoziny
                                                a hodnotou je pocet testovacich obrazku z teto podmnoziny
                    }
                    struct learning_subsets     Slovnikova struktura, kde klicem je nazev ucici podmnoziny
                                                a hodnotou je id teto podmnoziny
                }
            }
        """

        query = """
            SELECT `id`, `description`
            FROM picture_set
            ORDER BY id DESC
        """
        self.cursor.execute(query)
        picture_sets = self.cursor.fetchall()
        self._add_learning_subsets(picture_sets)
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
                        struct training         Slovnikova struktura, kde klicem je nazev ucici podmnoziny
                                                a hodnotou je pocet trenovacich obrazku z teto podmnoziny
                        struct validation       Slovnikova struktura, kde klicem je nazev ucici podmnoziny
                                                a hodnotou je pocet validacnich obrazku z teto podmnoziny
                        struct testing          Slovnikova struktura, kde klicem je nazev ucici podmnoziny
                                                a hodnotou je pocet testovacich obrazku z teto podmnoziny
                    }
                    struct learning_subsets     Slovnikova struktura, kde klicem je nazev ucici podmnoziny
                                                a hodnotou je id teto podmnoziny
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
        self._add_learning_subsets(picture_set)
        return picture_set
    #enddef

    @rpcStatusDecorator('picture_set.edit', 'S:iS')
    @MySQL_master
    def edit(self, picture_set_id, params):
        """
        Zmeni existujici ucici sadu obrazku

        Signature:
            picture_set.edit(int picture_set_id, struct param)

        @picture_set_id     Id Obrazkove sady
        @params {
            description         Popisek
        }

        Returns:
            struct {
                int status              200 = OK
                string statusMessage    Textovy popis stavu
                bool data               Success
            }
        """

        filterDict = {
            "description":      "description = %(description)s",
        }
        SET = self._getFilter(filterDict, params, "SET", ", ")
        params["id"] = picture_set_id
        query = """
            UPDATE picture_set
            """ + SET + """
            WHERE id = %(id)s
        """
        self.cursor.execute(query, params)
        return True
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
    def save(self, picture_set_id, learning_set, learning_subset, binary):
        """
        Tato metoda umožňuje nahrát novou fotografii do databáze fotografií.
        Metoda očekává čtyři parametry, kdy první tři parametry jsou identifikátory
        a čtvrtý parametr jsou binární data fotografie, která je nahrána z administračního
        rozhraní. První parametr je identifikátor databáze fotografií, druhý identifikuje
        kategorii do které fotografie patří a třetí identifikátor slouží pro upřesnění
        sekce ve které má být fotografie použita. Výstupem metody je pole, které obsahuje
        dvě hodnoty. Hodnota pod klíčem id udává identifikátor fotografie a
        hodnota pod klíčem hash udává unikátní hash v rámci systému.
        
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

        if learning_set not in self.config.pictures.LEARNING_SETS:
            raise Exception(402, "Unknown learning_set: %s" % learning_set)
        #endif
        picture_set = server.globals.rpcObjects['picture_set'].get(picture_set_id, bypass_rpc_status_decorator=True)
        if learning_subset not in picture_set["learning_subsets"]:
            raise Exception(402, "Unknown learning_subset: %s" % learning_subset)
        #endif

        # Ulozeni souboru na disk
        path = "%s/%d/%s/%s" % (self.config.pictures.base_path, picture_set_id, learning_set, learning_subset)
        dbg.log("picture.save: Path=%s", path, DBG=1)
        file_name = md5(binary.data).hexdigest()
        file_path = "%s/%s" % (path, file_name)
        f = open(file_path, "wb")
        f.write(binary.data)
        f.close()
        dbg.log("Picture saved successfully: %s", file_path, INFO=3)

        # Ulozeni metadat do DB
        query = """
            INSERT INTO picture (`picture_set_id`,`learning_set`,`learning_subset_id`,`hash`)
            VALUE (%s, %s, %s, %s)
        """
        params = (picture_set_id, learning_set, picture_set["learning_subsets"][learning_subset], file_name)
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
        Metoda pro vypsání seznamu fotografií včetně jejich informací o příslušných kategorií
        do kterých spadají. Očekávány je jeden povinný parametr a to identifikátor
        databáze fotografií pro kterou se mají fotografie získat a jeden volitelný parametr
        typu pole, který obsahuje filtr, který je možné nastavit dle potřeby. Hodnoty ve filtru
        jsou nastaveny tak, že název sloupce podle kterého se má filtrovat je uložen jako klíč
        v poli a hodnota pod tímto klíčem udává hodnotu, dle které se má filtr provést.
        Filtrovat je možné dle sloupců learning_set, learning_subset_id
        a learning_subset. Návratová hodnota je typu pole, kde jsou uloženy
        všechny informace z databázových tabulek picture a learning_subset.
        
        Signature:
            picture_set.list(int picture_set_id, struct params)

        @picture_set_id             Id sady
        @params                     Filtrovaci parametry

        Returns:
            struct {
                int status              200 = OK
                string statusMessage    Textovy popis stavu
                array data {
                    int id                  ID obrazku
                    int picture_set_id      ID sady obrazku
                    string learning_set     Nazev kategorie obrazku
                    string learning_subset  Nazev sekce obrazku
                    string hash             Hash obrazku
                }
            }
        """

        # Kontrola parametru
        if "learning_set" in params and params["learning_set"] not in self.config.pictures.LEARNING_SETS:
            raise Exception(402, "Unknown learning_set: %s" % params["learning_set"])
        #endif
        picture_set = server.globals.rpcObjects['picture_set'].get(picture_set_id, bypass_rpc_status_decorator=True)
        params["picture_set_id"] = picture_set_id
        if "learning_subset" in params and params["learning_subset"] not in picture_set["learning_subsets"]:
            raise Exception(402, "Unknown learning_subset: %s" % params["learning_subset"])
        #endif

        filterDict = {
            "picture_set_id":       "picture.picture_set_id = %(picture_set_id)s",
            "learning_set":         "picture.learning_set = %(learning_set)s",
            "learning_subset_id":   "picture.learning_subset_id = %(learning_subset_id)s",
            "learning_subset":      "learning_subset.name = %(learning_subset)s",
        }
        WHERE = self._getFilter(filterDict, params)

        query = """
            SELECT picture.`id`, picture.`picture_set_id`, picture.`learning_set`, `learning_subset`.name AS learning_subset, picture.`hash`
            FROM picture LEFT JOIN learning_subset ON (picture.picture_set_id=learning_subset.picture_set_id AND picture.learning_subset_id=learning_subset.id)
            """ + WHERE + """
            ORDER BY id DESC
        """
        self.cursor.execute(query, params)
        pictures = self.cursor.fetchall()

        return pictures
    #enddef
    
    @rpcStatusDecorator('picture.listSimple', 'S:i,S:iS')
    @MySQL_slave
    def listSimple(self, picture_set_id, params={}):
        """
        Nevypisuje nazvy subsetu, ale jejich ID.
        Protoze pri generovani obrazku pro uceni potrebujeme ciselne ID hodnoty (ne textove).
        
        Signature:
            picture_set.listSimple(int picture_set_id, struct params)

        @picture_set_id             Id sady
        @params                     Filtrovaci parametry

        Returns:
            struct {
                int status              200 = OK
                string statusMessage    Textovy popis stavu
                array data {
                    int id                  ID obrazku
                    int picture_set_id      ID sady obrazku
                    string learning_set     Nazev kategorie obrazku
                    int learning_subset_id  ID subsetu
                    string hash             Hash obrazku
                }
            }
        """

        # Kontrola parametru
        if "learning_set" in params and params["learning_set"] not in self.config.pictures.LEARNING_SETS:
            raise Exception(402, "Unknown learning_set: %s" % params["learning_set"])
        #endif
        picture_set = server.globals.rpcObjects['picture_set'].get(picture_set_id, bypass_rpc_status_decorator=True)
        params["picture_set_id"] = picture_set_id
        if "learning_subset" in params and params["learning_subset"] not in picture_set["learning_subsets"]:
            raise Exception(402, "Unknown learning_subset: %s" % params["learning_subset"])
        #endif

        filterDict = {
            "picture_set_id":       "picture.picture_set_id = %(picture_set_id)s",
            "learning_set":         "picture.learning_set = %(learning_set)s",
            "learning_subset_id":   "picture.learning_subset_id = %(learning_subset_id)s",
            "learning_subset":      "learning_subset.name = %(learning_subset)s",
        }
        WHERE = self._getFilter(filterDict, params)

        query = """
            SELECT picture.`id`, picture.`picture_set_id`, picture.`learning_set`, picture.`learning_subset_id`, picture.`hash`
            FROM picture
            """ + WHERE + """
            ORDER BY id DESC
        """
        self.cursor.execute(query, params)
        pictures = self.cursor.fetchall()

        return pictures
    #enddef

#endclass

