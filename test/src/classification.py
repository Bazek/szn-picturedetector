#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# AUTHOR           Petr Bartunek <petr.bartunek@firma.seznam.cz>
#
# Copyright (c) 2014 Seznam.cz, a.s.
# All rights reserved.
#


import sys
sys.path.insert(0, '/www/picturedetector/common/module/')

from szn_utils.configutils import Config, ConfigBox
import time
import os
import fastrpc

class ClassificationConfig(Config):

    class CaffeConfig(object):
        """ Parse caffe section """
        def __init__(self, parser, section="caffe"):
            self.image_path = parser.get(section, "ImagePath")
            self.print_results = parser.get(section, "PrintResults")
        #enddef
    #endclass


    def __init__(self, config_file):
        super(ClassificationConfig, self).__init__(config_file)
        self.backend = ConfigBox(self.parser, "backend")
        self.caffe = self.CaffeConfig(self.parser, "caffe")
    #enddef

#endclass




class ClassificationTest(object):
    """ Classification test """

    def __init__(self, config):
        self.config = config
    #enddef


    def process(self):
        """
        Provede časový test na všech neuronových sítích, které se nacházejí v databázi.
        Test rychlosti klasifikace se provede pro 1, 2, 5, 10 a 20 fotografií.
        Fotografie nejsou načteny z databáze, ale ze složky, která je definovaná
        v konfiguraci. Je potřebné dodržet, aby složka obsahovala dostatečný počet
        fotografií, tedy v tomto případně minimálně 20 fotografií.
        """
        images = []
        for dirname, dirnames, filenames in os.walk(self.config.caffe.image_path):
            for filename in filenames:
                filepath = os.path.join(dirname, filename)
                images.append(filepath)
            #endfor
        #endfor
        
        print 'Classification test'
        test_nums = [1, 1, 2, 5, 10, 20]
        images_count = len(images)
        
        neural_networks = self.config.backend.proxy.neural_network.list()
        if not neural_networks['data']:
            raise self.ProcessException("V databazi nebyla nalezena zadna neuronova sit")
        
        for neural_network in neural_networks['data']:
            print '----- Testing neural network #' + str(neural_network['id']) + ' -----'
            for test_num in test_nums:
                print 'Images count: ' + str(test_num)                
                if images_count >= test_num:
                    images_param = []
                    images_slice = images[:test_num]
                    num = 0
                    for im in images_slice:
                        f = open(im, 'r')
                        data = f.read()
                        f.close()
                        images_param.append({"id": im, "path": im, "data": fastrpc.Binary(data)})
                        num = num + 1
                    #endfor

                    try:
                        start = time.time()
                        results = self.config.backend.proxy.classify.classify(neural_network['id'], images_param)
                        end = time.time()
                        print '  - Time: ' + str((end - start)) + ' s'
                        
                        if self.config.caffe.print_results == '1':
                            print str(results)
                        #endif
                        
                    except Exception, e:
                        print 'EXCEPTION:' + str(e)
                        
                else:
                    print 'Not enough images'
                #endif
            #endfor
        #endfor
    #enddef

#endclass





def main():
    config = ClassificationConfig('/www/picturedetector/test/conf/classification.conf')
    test = ClassificationTest(config)
    test.process()
#enddef


if __name__ == '__main__':
    main()
#endif

