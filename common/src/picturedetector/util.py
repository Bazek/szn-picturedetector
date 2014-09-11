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


def readProtoLayerFile(self, filepath):
    layers_config = caffe_pb2.NetParameter()
    return self._readProtoFile(filepath, layers_config)
#enddef

def readProtoSolverFile(self, filepath):
    solver_config = caffe_pb2.SolverParameter()
    return self._readProtoFile(filepath, solver_config)
#enddef

def readProtoFile(self, filepath, parser_object):
    file = open(filepath, "r")
    if not file:
        raise self.ProcessException("Soubor s konfiguraci vrstev neuronove site neexistuje (" + filepath + ")!")

    text_format.Merge(str(file.read()), parser_object)
    file.close()
    return parser_object
#enddef
    
def getSolverPath(self, neural_network_id):
    solver_path = os.path.join(self.config.caffe.solver_file_path, self.config.caffe.solver_file_prefix + str(neural_network_id))
    return solver_path
#enddef

def parseLayerPaths(self, proto):
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