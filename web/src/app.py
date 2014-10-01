#!/usr/bin/env python
#
# FILE             $Id:  $
#
# DESCRIPTION
#
# PROJECT
#
# AUTHOR           Petr Bartunek <petr.bartunek@firma.seznam.cz>
#
# Copyright (C) Seznam.cz a.s. 2014
# All Rights Reserved
#


from flask import Flask
from lib.config import Config


app = None
conf = None


def create_app(config_path):

    global app, conf

    conf = Config(config_path)

    app = Flask(__name__)
    app.config.update({"DEBUG": conf.flask.DEBUG, "SECRET_KEY": conf.flask.SECRET_KEY})

    # make config accessible from template
    app.config.conf = conf

    # Import handlers
    from views import picturedetector
    from views import model
    from views import learning
    from views import neural_network
    from views import picture

    return app

#enddef
