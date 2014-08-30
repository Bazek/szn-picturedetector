#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# DESCRIPTION
#   Klasifikace obrazku pomoci neuronove site
#

import StringIO
from ConfigParser import SafeConfigParser

import metaserver.fastrpc as server
from dbglog import dbg
from lib.backend import Backend
from rpc_backbone.decorators import rpcStatusDecorator
import numpy as np
import caffe

class ClassifyBackend(Backend):

    @rpcStatusDecorator('classify.classify', 'S:iA')
    def classify(self, neural_network_id, images):
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

        network = server.globals.rpcObjects['neural_network'].get(neural_network_id, bypass_rpc_status_decorator=True)
        dbg.log("network %s", network, INFO=3) 
        
        network_configuration = network['configuration']
        dbg.log("network_configuration %s", network_configuration, INFO=3) 
        
        config = SafeConfigParser(allow_no_value=True)
        config_file = StringIO.StringIO(network_configuration)
        config.readfp(config_file)

        model_config_path = config.get('paths', 'modelConfiguration')
        pretrained_model_path = config.get('paths', 'pretrainedModel')
        mean_file_path = config.get('paths', 'meanFile')
        
        dbg.log("Path settings:\nmodel path %s\ntrained_path %s\nmean file %s", (model_config_path, pretrained_model_path, mean_file_path), DBG=3) 

        # if we get only one image, convert it to array of one image object
        if not isinstance(images, list):
            images = [images]
            
        dbg.log("caffe %s", caffe, INFO=3) 
        # create caffe classicifer
        net = caffe.Classifier(
            model_config_path,
            pretrained_model_path,
            mean=np.load(mean_file_path),
            channel_swap=(2,1,0),
            raw_scale=255,
            gpu=self.config.caffe.gpu_mode
        )
        
        net.set_phase_test()
        
        # set GPU/CPU mode
        if self.config.caffe.gpu_mode:
            net.set_mode_gpu()
        else:
            net.set_mode_cpu()
            
        # array of loaded images
        input_images=[]
        for image in images:
            input_images.append(caffe.io.load_image(image['path']))

        dbg.log("input_images %s", input_images, INFO=3) 
        
        # start prediction
        prediction = net.predict(input_images)
        
        # process results
        result={}
        
        i = 0
        
        # crop categories array
        slice_size = int(self.config.classify.number_of_categories)
        dbg.log("max output categories %s", slice_size, INFO=3)
            
        # @todo hope that result predictions are in same order as input images. Check if it is true.
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
            
            result[images[i]['id']] = categories;
            i += 1
            
        return result

    #enddef