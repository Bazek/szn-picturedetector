#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# DESCRIPTION
#   Klasifikace obrazku pomoci neuronove site
#

import metaserver.fastrpc as server
from dbglog import dbg
from lib.backend import Backend
from rpc_backbone.decorators import rpcStatusDecorator
import caffe
import numpy
from skimage.util.dtype import convert
from picturedetector import util

try:
    import imread as _imread
except ImportError:
    raise ImportError("Imread could not be found"
        "Please refer to http://pypi.python.org/pypi/imread/ "
        "for further instructions.")

class ClassifyBackend(Backend):
    
    @rpcStatusDecorator('classify.classify', 'S:iA,S:iAi')
    def classify(self, neural_network_id, images, number_of_categories = None):
        """
        Funkce pro zpracovani obrazku

        Signature:
            neural_network.classify(int neural_network_id, struct images)

        @param {
            int neuralNetworkId         ID neuronove site
            array(
                struct {
                    imageId             ID obrazku
                    path                Cesta k obrazku
                }
            )
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
        
        # Nacteni nebo vytvoreni klasifikatoru
        if neural_network_id in server.globals.neuralNetworks:
            net = server.globals.neuralNetworks[neural_network_id]
        else:
            net = self.createClassifier(neural_network_id, bypass_rpc_status_decorator=True)
        #endif

        # if we get only one image, convert it to array of one image object
        if not isinstance(images, list):
            images = [images]

        # array of loaded images
        input_images=[]
        for image in images:
            if 'data' in image:
                input_images.append(self._load_image_from_binary(image['data'].data))
            elif 'path' in image:
                try:
                    input_images.append(caffe.io.load_image(image['path']))
                except Exception as e:
                    dbg.log('Exception - ' + image['path'] + ': ' + str(e), ERR=3)
            #endif

        # start prediction
        prediction = []
        try:
            prediction = net.predict(input_images)
        except Exception as e:
            dbg.log('Exception - prediction: ' + str(e), ERR=3)
            
        # process results
        result={}
        
        i = 0
        
        # crop categories array
        if number_of_categories == None:
            slice_size = int(self.config.classify.number_of_categories)
        else:
            slice_size = int(number_of_categories)
        #endif
            
        # go through all predicted images
        for scores in prediction:
            # get category id with best match
            categoryIds = (-scores).argsort()
            
            if slice_size != 0:
                categoryIds = categoryIds[:slice_size]
            
            # save prediction results
            categories = []
            for id in categoryIds:
                categories.append({"category":id,"percentage":float(scores[id])})

            result[str(images[i]['id'])] = categories;
            i += 1
            
        return result

    #enddef
    
    def _load_image_from_binary(self, data, format = 'jpg', as_grey=False, return_metadate=False):
        blob_data = _imread.imread_from_blob(data, format)
        return convert(blob_data, 'float32')
    #enddef

    @rpcStatusDecorator('classify.createClassifier', 'S:i')
    def createClassifier(self, neural_network_id):
        neural_network = server.globals.rpcObjects['neural_network'].get(neural_network_id, bypass_rpc_status_decorator=True)
        model_config = server.globals.rpcObjects['neural_network'].getPath(neural_network_id, 'model', bypass_rpc_status_decorator=True)
        
        # Nacteni cesty k snapshotu nad kterym se bude provadet klasifikace
        snapshot_path = server.globals.rpcObjects['neural_network'].getSnapshotPath(neural_network_id, neural_network['pretrained_iteration'], bypass_rpc_status_decorator=True)
        
        # Vygenerovani cesty pro mean file soubor pro klasifikaci
        mean_file_path = server.globals.rpcObjects['neural_network'].getPath(neural_network_id, 'mean_file', bypass_rpc_status_decorator=True)

        dbg.log("Classifier file paths:\nModel config: " + model_config + "\nSnapshot: " + snapshot_path + "\nMeanFile:" + mean_file_path, INFO=3)
        # if classifier meanfile path is set, read the mean file
        mean_file = None
        if mean_file_path:
            mean_file = numpy.load(mean_file_path)
        #endif
        
        if neural_network['gpu'] == None:
            gpu_mode = self.config.caffe.gpu_mode
        else:
            gpu_mode = neural_network['gpu']
        #endif

        # create caffe classicifer
        net = caffe.Classifier(
            model_config,
            snapshot_path,
            mean=mean_file,
            channel_swap=(2,1,0),
            raw_scale=255,
            gpu=gpu_mode
        )
        
        net.set_phase_test()
        
        if server.globals.config.caffe.init_networks_on_start and not neural_network_id in server.globals.neuralNetworks:
            if neural_network['keep_saved']:
                server.globals.neuralNetworks[neural_network_id] = net
            #endif
        #endif
        dbg.log(str(net), INFO=3)
        return net
    #enddef
            
#endclass