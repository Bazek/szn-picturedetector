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




@app.route("/picture-set")
def picture_set__list():
    result = conf.backend.proxy.picture_set.list()
    picture_sets = result.get("data")
    return render_teng("picture-set_list.html", picture_sets=picture_sets)
#enddef
