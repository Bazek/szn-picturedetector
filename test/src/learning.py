#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# AUTHOR           Petr Bartunek <petr.bartunek@firma.seznam.cz>
#
# Copyright (c) 2014 Seznam.cz, a.s.
# All rights reserved.
#

import os
import time
import sys
sys.path.insert(0, '/www/picturedetector/common/module/')

from szn_utils.configutils import Config
import subprocess
from picturedetector import util


class LearningConfig(Config):

    class CaffeConfig(object):
        """ Parse caffe section """
        def __init__(self, parser, section="caffe"):
            self.solver_config_dir = parser.get(section, "SolverConfigDir")
            self.learning_time_script = parser.get(section, "LearningTimeScript")
            self.learn_script = parser.get(section, "LearnScript")
            self.graphic_device_id = parser.get(section, "GraphicDeviceId")
            self.test_iterations = parser.get(section, "TestIterations")
            self.log_path = parser.get(section, "LogPath")
            self.time_command = parser.get(section, "TimeCommand")
            self.time_command_param = parser.get(section, "TimeCommandParam")
        #enddef
    #endclass


    def __init__(self, configFile):
        super(LearningConfig, self).__init__(configFile)
        self.caffe = self.CaffeConfig(self.parser, "caffe")
    #enddef

#endclass




class LearningTest(object):
    """ Learning test """
    
    # koncovka log souboru
    LOG_FILE_EXT = '.log'
    
    def __init__(self, config):
        self.config = config
    #enddef


    def process(self):
        learn_time_script = self.config.caffe.learning_time_script
        learn_script = self.config.caffe.learn_script
        
        print self.config.caffe.solver_config_dir
        for dirname, dirnames, filenames in os.walk(self.config.caffe.solver_config_dir):
            for filename in filenames:
                filepath = os.path.join(dirname, filename)
                log_output = os.path.join(self.config.caffe.log_path, os.path.splitext(filename)[0] + self.LOG_FILE_EXT)
                print '----- ' + filepath + ' -----'
                
                # Cteni solver souboru a nacteni cesty k modelu
                solver_config = util.readProtoSolverFile(filepath)
                model_file = solver_config.net
                print 'model: ' + model_file
                print 'log: ' + log_output
                
                log_file = open(log_output, 'w')
                if not log_file:
                    raise self.ProcessException("Nemuzu vytvorit logovaci soubor (" + log_file + ")")
                #endif
                
                print 'Test #1: Learning (iterations: ' + str(solver_config.max_iter) + ')'
                start = time.time()
                
                # Vytvoreni argumentu pro spusteni uceni a nasledneho mereni doby trvani
                learn_args = []
                learn_args.append(self.config.caffe.time_command)
                learn_args.append(self.config.caffe.time_command_param)
                learn_args.append(learn_script)
                learn_args.append('train')
                learn_args.append('-solver=' + filepath)
                p = subprocess.Popen(learn_args, stderr=log_file, stdout=log_file)
                p.communicate()
                
                end = time.time()
                print '  - Time: ' + str((end - start)) + ' s'
                
                test_iterations = self.config.caffe.test_iterations
                print 'Test #2: Caffe time learning (iterations: ' + str(test_iterations) + ')'
                start = time.time()
                # Vytvoreni argumentu pro spusteni skriptu pro mereni rychlosti uceni
                test_lear_args = []
                learn_args.append(self.config.caffe.time_command)
                learn_args.append(self.config.caffe.time_command_param)
                test_lear_args.append(learn_time_script)
                test_lear_args.append(model_file)
                test_lear_args.append(test_iterations)
                
                if self.config.caffe.graphic_device_id != None:
                    test_lear_args.append(self.config.caffe.graphic_device_id)
                #endif

                # Spusteni casove mereneho uceni
                p = subprocess.Popen(test_lear_args, stderr=log_file, stdout=log_file)
                p.communicate()
                
                end = time.time()
                print '  - Time: ' + str((end - start)) + ' s'
                
                log_file.close()
                print ''
            #endfor
        #endfor
    #enddef

#endclass





def main():
    config = LearningConfig('/www/picturedetector/test/conf/learning.conf')
    test = LearningTest(config)
    test.process()
#enddef


if __name__ == '__main__':
    main()
#endif

