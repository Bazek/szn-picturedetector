#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# DESCRIPTION
#   Prace s obrazky
#

from dbglog import dbg

from rpc_backbone.decorators import rpcStatusDecorator, MySQL_master, MySQL_slave
from lib.backend import Backend

from hashlib import md5
import os


class PictureBackend(Backend):
    """
    Trida pro praci s obrazky
    """

    @rpcStatusDecorator('picture.save', 'S:ssB')
    def save(self, picture_set, learning_set, data):
        """
        """
        if learning_set not in self.config.pictures.learning_set_paths:
            raise Exception(402, "Unknown learning_set: %s" % learning_set)
        #endif
        path = "%s/%s/%s" % (self.config.pictures.base_path, picture_set, self.config.pictures.learning_set_paths[learning_set])
        dbg.log("picture.save: Path=%s", path, DBG=1)
        if not os.path.exists(path):
            dbg.log("Creating path: %s", path, INFO=1)
            os.makedirs(path)
        #endif
        file_name = md5(data).hexdigest()
        file_path = "%s/%s" % (path, file_name)
        f = open(file_path, "w")
        f.write(data)
        f.close()
        dbg.log("Picture saved successfully: %s", file_path, INFO=3)
        return True
    #enddef
#endclass

