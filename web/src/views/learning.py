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


from dbglog import dbg
from flask import request, redirect, url_for
from lib.teng import render_teng
from app import app, conf
import fastrpc




@app.route("/learning-queue")
def learning_queue__list():
    result = conf.backend.proxy.learning_queue.list()
    learning_queue = result.get("data")
    return render_teng("learning-queue_list.html", learning_queue=learning_queue)
#enddef
