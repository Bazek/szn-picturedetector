#!/usr/bin/env python
#
# DESCRIPTION
#
# PROJECT
#
# AUTHOR            Petr Bartunek <Petr.Bartunek@firma.seznam.cz>
#
# Copyright (C) Seznam.cz a.s. 2014
# All Rights Reserved

from caffe.proto import caffe_pb2
from google.protobuf import text_format

# Konstanty pro rozliseni souboru pro uceni a validaci
TRAIN = 'train'
VALIDATE = 'validate'

# Konstanty, ktere urcuji nactene cesty ze souboru imagenet_train_val.prototxt
SOURCE = 'source'
MEAN_FILE = 'mean_file'    
    
def readProtoLayerFile(filepath):
    layers_config = caffe_pb2.NetParameter()
    return _readProtoFile(filepath, layers_config)
#enddef

def _readProtoFile(filepath, parser_object):
    file = open(filepath, "r")
    if not file:
        raise Exception("Soubor s konfiguraci vrstev neuronove site neexistuje (" + filepath + ")!")

    text_format.Merge(str(file.read()), parser_object)
    file.close()
    return parser_object
#enddef

def parseLayerPaths(proto):
    results = {}

    results[TRAIN] = {
        SOURCE: '',
        MEAN_FILE: ''
    }

    results[VALIDATE] = {
        SOURCE: '',
        MEAN_FILE: ''
    }

    for layer in proto.layers:
        if layer.type == caffe_pb2.LayerParameter.LayerType.Value('DATA'):
            include_name = False
            for include in layer.include:
                if include.phase == caffe_pb2.Phase.Value('TRAIN'):
                    include_name = TRAIN
                elif include.phase == caffe_pb2.Phase.Value('TEST'):
                    include_name = VALIDATE
                #endif
            #endfor

            if not include_name or (include_name == TRAIN):
                if layer.data_param.source:
                    results[TRAIN][SOURCE] = layer.data_param.source
                #endif

                if layer.data_param.mean_file:
                    results[TRAIN][MEAN_FILE] = layer.data_param.mean_file
                #endif
            #endif

            if not include_name or (include_name == VALIDATE):
                if layer.data_param.source:
                    results[VALIDATE][SOURCE] = layer.data_param.source
                #endif

                if layer.data_param.mean_file:
                    results[VALIDATE][MEAN_FILE] = layer.data_param.mean_file
                #endif
            #endif
        #endif
    #endfor

    return results
#enddef