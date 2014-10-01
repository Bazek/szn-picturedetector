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




@app.route("/model")
def model__list():
    result = conf.backend.proxy.model.list()
    models = result.get("data")
    return render_teng("model_list.html", models=models)
#enddef


@app.route("/model/edit", methods=["GET"], defaults={'id': None})
@app.route("/model/edit/<int:id>", methods=["GET"])
def model__edit_GET(id):
    model = {}
    if id:
        result = conf.backend.proxy.model.get(id)
        if result.get("status") != 200:
            return redirect('/model?status=model_not_found')
        #endif
        model = result.get("data")
    #endif
    return render_teng("model_edit.html", model=model)
#enddef


@app.route("/model/edit", methods=["POST"], defaults={'id': None})
@app.route("/model/edit/<int:id>", methods=["POST"])
def model__edit_POST(id):
    model = {
        "description":  request.form.get("description"),
    }
    if id:
        result = conf.backend.proxy.picture_set.edit(id, picture_set)
        if result.get("status") != 200:
            return redirect('/model/edit/%d?status=model_edit_failed'%id)
        #endif
    else:
        result = conf.backend.proxy.picture_set.add(picture_set)
        if result.get("status") != 200:
            return redirect('/model/edit?status=model_add_failed')
        #endif
        id = result.get("data")
    #endif
    return redirect('/model/edit/%d?status=model_edit_ok'%id)
#enddef


@app.route("/model/delete/<int:id>", methods=["GET"])
def model__delete_GET(id):
    result = conf.backend.proxy.model.delete(id)
    if result.get("status") != 200:
        return redirect('/model?status=model_delete_failed')
    #endif
    return redirect('/model?status=model_delete_ok')
#enddef
