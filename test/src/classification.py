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

from szn_utils.configutils import Config




class ClassificationConfig(Config):

    class CaffeConfig(object):
        """ Parse caffe section """
        def __init__(self, parser, section="caffe"):
            self.variable = parser.get(section, "Variable")        
        #enddef
    #endclass


    def __init__(self, configFile):
        super(ClassificationConfig, self).__init__(configFile)
        self.caffe = self.CaffeConfig(self.parser, "caffe")
    #enddef

#endclass




class ClassificationTest(object):
    """ Classification test """

    def __init__(self, config):
        self.config = config
    #enddef


    def process(self):
        pass
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

