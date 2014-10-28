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

@app.route("/learning-queue/edit", methods=["GET"], defaults={'id': None})
@app.route("/learning-queue/edit/<int:id>", methods=["GET"])
def learning_queue__edit_GET(id):
    learning_queue = {}
    if id:
        result = conf.backend.proxy.learning_queue.get(id)
        if result.get("status") != 200:
            return redirect('/learning-queue?status=1&message=learning_queue_not_found')
        #endif
        learning_queue = result.get("data")
    #endif
    return render_teng("learning-queue_edit.html", learning_queue=learning_queue)
#enddef

@app.route("/learning-queue/edit", methods=["POST"], defaults={'id': None})
@app.route("/learning-queue/edit/<int:id>", methods=["POST"])
def learning_queue__edit_POST(id):
    learning_queue = {
        "picture_set_id":  request.form.get("picture_set_id"),
        "start_iteration":  request.form.get("start_iteration"),
        "status":  request.form.get("status"),
    }

    if id:
        result = conf.backend.proxy.learning_queue.edit(id, learning_queue)
        if result.get("status") != 200:
            return redirect('/learning-queue/edit/%d?status=1&message=learning_queue_edit_failed'%id)
        #endif
    else:
        learning_queue["neural_network_id"] = request.form.get("neural_network_id")
        result = conf.backend.proxy.learning_queue.add(learning_queue)
        if result.get("status") != 200:
            return redirect('/learning-queue/edit?status=1&message=learning_queue_add_failed')
        #endif
        id = result.get("data")
    #endif
    return redirect('/learning-queue/edit/%d?status=0&message=learning_queue_edit_ok'%id)
#enddef

@app.route("/learning-queue/delete/<int:id>", methods=["GET"])
def learning_queue__delete_GET(id):
    result = conf.backend.proxy.learning_queue.delete(id)
    if result.get("status") != 200:
        return redirect('/learning-queue?status=1&message=learning_queue_delete_failed')
    #endif
    return redirect('/learning-queue?status=0&message=learning_queue_delete_ok')
#enddef
