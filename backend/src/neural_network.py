#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# DESCRIPTION
#   Prace s neuronovou siti
#

from dbglog import dbg

from rpc_backbone.decorators import rpcStatusDecorator, MySQL_master, MySQL_slave
from lib.backend import Backend

try:
    import caffe
except:
    dbg.log("Cannot import caffe", ERR=2)
#endtry


caffe_root = '/www/picturedetector/caffe'
MODEL_FILE = 'examples/imagenet/imagenet_deploy.prototxt'
PRETRAINED = 'examples/imagenet/caffe_reference_imagenet_model'
MEAN_FILE = 'python/caffe/imagenet/ilsvrc_2012_mean.npy'

class NeuralNetworkBackend(Backend):
    """
    Trida pro praci s neuronovou siti
    """

    @rpcStatusDecorator('neural_network.function', 'S:,S:b')
    @MySQL_master
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

        return {
            "normal":   self.get(2),
            "bypass":   self.get(2, bypass_rpc_status_decorator=True),
        }
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

    @rpcStatusDecorator('neural_network.list', 'S:')
    @MySQL_slave
    def list(self):
        """
        Vylistuje vsechny neuronove site

        Signature:
            neural_network.list()

        Returns:
            struct {
                int status              200 = OK
                string statusMessage    Textovy popis stavu
                array data {
                    integer id              neural_network_id
                    string description      description
                    string configuration    konfigurace
                }
            }
        """

        query = """
            SELECT id, description, configuration
            FROM neural_network
        """
        self.cursor.execute(query)
        neural_networks = self.cursor.fetchall()
        return neural_networks
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

    @rpcStatusDecorator('neural_network.edit', 'S:iS')
    @MySQL_master
    def edit(self, neural_network_id, params):
        """
        Testovaci funkce

        Signature:
            neural_network.edit(int id, struct param)

        @neural_network_id  Id neuronove site
        @params {
            description         Popisek
            configuration       Konfigurace neuronove site
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
            "configuration":    "configuration = %(configuration)s",
        }
        SET = self._getFilter(filterDict, params, "SET", ", ")
        params["id"] = neural_network_id
        query = """
            UPDATE neural_network
            """ + SET + """
            WHERE id = %(id)s
        """
        self.cursor.execute(query, params)
        return True
    #enddef

    @rpcStatusDecorator('neural_network.delete', 'S:i')
    @MySQL_master
    def delete(self, neural_network_id):
        """
        Odstrani celou neuronovou sit

        Signature:
            neural_network.delete(int neural_network_id)

        @neural_network_id           Id Neuronove site

        Returns:
            struct {
                int status              200 = OK
                string statusMessage    Textovy popis stavu
                bool data               Uspesne smazano
            }
        """

        query = """
            DELETE FROM neural_network
            WHERE id = %s
        """
        self.cursor.execute(query, neural_network_id)
        if self.cursor.rowcount == 0:
            status, statusMessage = 404, "NeuralNetwork #%d not found." % neural_network_id
            raise Exception(status, statusMessage)
        #endif

        return True
    #enddef
    
    @rpcStatusDecorator('neural_network.addImages', 'S:S')
    def addImages(self, images):
        """
        Funkce pro zpracovani obrazku

        Signature:
            neural_network.addImages(struct images)

        @param {
            struct {
                id                      ID obrazku
                path                    Cesta k obrazku
            }
        }

        Returns:
            struct {
                int status              200 = OK
                string statusMessage    Textovy popis stavu
                struct data {
                    imageId {
                        category        Cislo kategorie
                        percentage      Velikost shody s danou kategorii
                    }
                }
            }
        """
        
        dbg.log("Path settings:\nmodel path %s\ntrained_path %s\nmean file %s", (caffe_root + MODEL_FILE, caffe_root + PRETRAINED, caffe_root + MEAN_FILE), DBG=3) 

        # if we get only one image, convert it to array of one image object
        if not isinstance(images, list):
            images = [images]
        
        # create caffe classicifer
        net = caffe.Classifier(
            caffe_root + MODEL_FILE,
            caffe_root + PRETRAINED,
            mean_file=caffe_root + MEAN_FILE,
            channel_swap=(2,1,0),
            input_scale=255
        )
        
        net.set_phase_test()
        
        # set GPU/CPU mode
        net.set_mode_gpu()

        # array of loaded images
        input_images=[]
        for image in images:
            input_images.append(caffe.io.load_image(image['path']))

        # start prediction
        prediction = net.predict(input_images)
        
        # process results
        result={}
        
        i = 0
        
        # @todo hope that result predictions are in same order as input images. Check if it is true.
        # go through all predicted images
        for scores in prediction:
            # get category id with best match
            categoryId = (-scores).argsort()[0]
            
            # save prediction results
            result[images[i]['id']] = {"category":categoryId,"percentage":float(scores[categoryId])}
            i += 1
            
        return result

    #enddef

#endclass

