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




@app.route("/picture-set")
def picture_set__list():
    result = conf.backend.proxy.picture_set.list()
    picture_sets = result.get("data")
    return render_teng("picture-set_list.html", picture_sets=picture_sets)
#enddef


@app.route("/picture-set/edit", methods=["GET"], defaults={'id': None})
@app.route("/picture-set/edit/<int:id>", methods=["GET"])
def picture_set__edit_GET(id):
    picture_set = {}
    if id:
        result = conf.backend.proxy.picture_set.get(id)
        if result.get("status") != 200:
            return redirect('/picture-set?status=picture-set_not_found')
        #endif
        picture_set = result.get("data")
    #endif
    return render_teng("picture-set_edit.html", picture_set=picture_set)
#enddef

@app.route("/picture-set/edit", methods=["POST"], defaults={'id': None})
@app.route("/picture-set/edit/<int:id>", methods=["POST"])
def picture_set__edit_POST(id):
    picture_set = {
        "description":  request.form.get("description"),
    }
    if id:
        result = conf.backend.proxy.picture_set.edit(id, picture_set)
        if result.get("status") != 200:
            return redirect('/picture-set/edit/%d?status=picture-set_edit_failed'%id)
        #endif
    else:
        result = conf.backend.proxy.picture_set.add(picture_set)
        if result.get("status") != 200:
            return redirect('/picture-set/edit?status=picture-set_add_failed')
        #endif
        id = result.get("data")
    #endif
    return redirect('/picture-set/edit/%d?status=picture-set_edit_ok'%id)
#enddef


@app.route("/picture-set/edit/<int:id>/<string:learning_set>", methods=["GET"], defaults={"learning_subset": None})
@app.route("/picture-set/edit/<int:id>/<string:learning_set>/<string:learning_subset>", methods=["GET"])
def picture_set__edit_pictures_GET(id, learning_set, learning_subset):
    picture_set = {}
    if id:
        result = conf.backend.proxy.picture_set.get(id)
        if result.get("status") != 200:
            return redirect('/picture-set?status=picture-set_not_found')
        #endif
        picture_set = result.get("data")
        params = {}
        if learning_set:  params["learning_set"] = learning_set
        if learning_subset:  params["learning_subset"] = learning_subset
        result = conf.backend.proxy.picture.list(id, params)
        if result.get("status") != 200:
            return redirect('/picture-set?status=picture-set_not_found')
        #endif
        pictures = result.get("data")
    #endif
    return render_teng("picture-set_edit-pictures.html",
        picture_set = picture_set,
        pictures = pictures,
        learning_set = learning_set,
        learning_subset = learning_subset,
    )
#enddef

@app.route("/picture-set/edit/<int:id>/<string:learning_set>/<string:learning_subset>", methods=["POST"])
def picture_set__edit_pictures_POST(id, learning_set, learning_subset):
    dbg.log(str(request.files['file']))
    data = request.files['file'].read()
    result = conf.backend.proxy.picture.save(id, learning_set, learning_subset, fastrpc.Binary(data))
    if result.get("status") != 200:
        return redirect('/picture-set/edit/%d?status=picture-set_edit-pictures_failed'%id)
    #endif
    return redirect('/picture-set/edit/%d?status=picture-set_edit-pictures_ok'%id)
#enddef


@app.route("/picture-set/delete/<int:id>", methods=["GET"])
def picture_set__delete_GET(id):
    result = conf.backend.proxy.picture_set.delete(id)
    if result.get("status") != 200:
        return redirect('/picture-set?status=picture-set_delete_failed')
    #endif
    return redirect('/picture-set?status=picture-set_delete_ok')
#enddef
