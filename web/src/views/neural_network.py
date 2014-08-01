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




@app.route("/neural-network", methods=["GET"])
def neural_network__list():
    result = conf.backend.proxy.neural_network.list()
    neural_networks = result.get("data")
    return render_teng("neural-network_list.html", neural_networks=neural_networks)
#enddef


@app.route("/neural-network/edit", methods=["GET"], defaults={'id': None})
@app.route("/neural-network/edit/<int:id>", methods=["GET"])
def neural_network__edit_GET(id):
    neural_network = {}
    if id:
        result = conf.backend.proxy.neural_network.get(id)
        if result.get("status") != 200:
            return redirect('/neural-network?status=neural-network_not_found')
        #endif
        neural_network = result.get("data")
    #endif
    return render_teng("neural-network_edit.html", neural_network=neural_network)
#enddef

@app.route("/neural-network/edit", methods=["POST"], defaults={'id': None})
@app.route("/neural-network/edit/<int:id>", methods=["POST"])
def neural_network__edit_POST(id):
    neural_network = {
        "description":  request.form.get("description"),
        "configuration":  request.form.get("configuration"),
    }
    if id:
        result = conf.backend.proxy.neural_network.edit(id, neural_network)
        if result.get("status") != 200:
            return redirect('/neural-network/edit/%d?status=neural-network_edit_failed'%id)
        #endif
    else:
        result = conf.backend.proxy.neural_network.add(neural_network)
        if result.get("status") != 200:
            return redirect('/neural-network/edit?status=neural-network_add_failed')
        #endif
        id = result.get("data")
    #endif
    return redirect('/neural-network/edit/%d?status=neural-network_edit_ok'%id)
#enddef


@app.route("/neural-network/delete/<int:id>", methods=["GET"])
def neural_network__delete_GET(id):
    result = conf.backend.proxy.neural_network.delete(id)
    if result.get("status") != 200:
        return redirect('/neural-network?status=neural-network_delete_failed')
    #endif
    return redirect('/neural-network?status=neural-network_delete_ok')
#enddef
