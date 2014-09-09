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
import numpy as np
import caffe
from caffe.proto import caffe_pb2
from google.protobuf import text_format

class ClassifyBackend(Backend):
        
    # Konstanty pro rozliseni souboru pro uceni a validaci
    TRAIN = 'train'
    VALIDATE = 'validate'

    # Konstanty, ktere urcuji nactene cesty ze souboru imagenet_train_val.prototxt
    SOURCE = 'source'
    MEAN_FILE = 'mean_file'
    
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

        model_config_path = network['model_config_path']
        pretrained_model_path = network['pretrained_model_path']

        solver_config = self._readProtoSolverFile(network['solver_config_path'])
    
        # Parsovani cest ze souboru imagenet_train_val.prototxt
        layer_config = self._readProtoLayerFile(solver_config.net)
        layer_paths = self._parseLayerPaths(layer_config)
        mean_file_path = layer_paths[self.TRAIN][self.MEAN_FILE]
        
        dbg.log("Path settings:\nmodel path %s\ntrained_path %s\nmean file %s", (model_config_path, pretrained_model_path, mean_file_path), DBG=3) 

        # if we get only one image, convert it to array of one image object
        if not isinstance(images, list):
            images = [images]
            
        dbg.log("caffe %s", caffe, INFO=3) 
        # create caffe classicifer
        net = caffe.Classifier(
            model_config_path,
            pretrained_model_path,
            #TODO get meanfile in npy format
            #mean=np.load(mean_file_path),
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
    
    def _readProtoLayerFile(self, filepath):
        layers_config = caffe_pb2.NetParameter()
        return self._readProtoFile(filepath, layers_config)
    #enddef
    
    def _readProtoSolverFile(self, filepath):
        solver_config = caffe_pb2.SolverParameter()
        return self._readProtoFile(filepath, solver_config)
    #enddef
    
    def _readProtoFile(self, filepath, parser_object):
        file = open(filepath, "r")
        if not file:
            raise self.ProcessException("Soubor s konfiguraci vrstev neuronove site neexistuje (" + filepath + ")!")

        text_format.Merge(str(file.read()), parser_object)
        file.close()
        return parser_object
    #enddef
    
    def _parseLayerPaths(self, proto):
        results = {}
        
        results[self.TRAIN] = {
            self.SOURCE: '',
            self.MEAN_FILE: ''
        }
        
        results[self.VALIDATE] = {
            self.SOURCE: '',
            self.MEAN_FILE: ''
        }
        
        for layer in proto.layers:
            if layer.type == caffe_pb2.LayerParameter.LayerType.Value('DATA'):
                include_name = False
                for include in layer.include:
                    if include.phase == caffe_pb2.Phase.Value('TRAIN'):
                        include_name = self.TRAIN
                    elif include.phase == caffe_pb2.Phase.Value('TEST'):
                        include_name = self.VALIDATE
                    #endif
                #endfor

                if not include_name or (include_name == self.TRAIN):
                    if layer.data_param.source:
                        results[self.TRAIN][self.SOURCE] = layer.data_param.source
                    #endif

                    if layer.data_param.mean_file:
                        results[self.TRAIN][self.MEAN_FILE] = layer.data_param.mean_file
                    #endif
                #endif
                
                if not include_name or (include_name == self.VALIDATE):
                    if layer.data_param.source:
                        results[self.VALIDATE][self.SOURCE] = layer.data_param.source
                    #endif

                    if layer.data_param.mean_file:
                        results[self.VALIDATE][self.MEAN_FILE] = layer.data_param.mean_file
                    #endif
                #endif
            #endif
        #endfor
        
        return results
    #enddef
    
#endclass