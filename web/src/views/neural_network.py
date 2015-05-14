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
            return redirect('/neural-network?status=1&message=neural_network_not_found')
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
        "model_config":  request.form.get("model_config"),
        "solver_config":  request.form.get("solver_config"),
        "trainmodel_config":  request.form.get("trainmodel_config"),
        "pretrained_iteration":  request.form.get("pretrained_iteration"),
        "auto_init":  request.form.get("auto_init"),
        "keep_saved":  request.form.get("keep_saved"),
        "gpu":  request.form.get("gpu"),
    }
    
    if id:
        result = conf.backend.proxy.neural_network.edit(id, neural_network)
        if result.get("status") != 200:
            return redirect('/neural-network/edit/%d?status=1&message=neural_network_edit_failed'%id)
        #endif
    else:
        result = conf.backend.proxy.neural_network.add(neural_network)
        if result.get("status") != 200:
            return redirect('/neural-network/edit?status=1&message=neural_network_add_failed')
        #endif
        id = result.get("data")
    #endif
    return redirect('/neural-network/edit/%d?status=0&message=neural_network_edit_ok'%id)
#enddef


@app.route("/neural-network/delete/<int:id>", methods=["GET"])
def neural_network__delete_GET(id):
    result = conf.backend.proxy.neural_network.delete(id)
    if result.get("status") != 200:
        return redirect('/neural-network?status=1&message=neural_network_delete_failed')
    #endif
    return redirect('/neural-network?status=0&message=neural_network_delete_ok')
#enddef

@app.route("/neural-network/learn-stat/<int:id>", methods=["GET"], defaults={'log_name': None})
@app.route("/neural-network/learn-stat/<int:id>/<string:log_name>", methods=["POST"])
def neural_network__learn_stat_GET(id, log_name):
    neural_network = {}
    if id:
        result = conf.backend.proxy.neural_network.getLogs(id)
        if result.get("status") != 200:
            return redirect('/neural-network?status=1&message=neural_network_not_found')
        #endif
        logs = result.get("data")
    #endif
    
    if log_name:
        result = conf.backend.proxy.neural_network.learningStatus(id, log_name)
        
        if result.get("status") != 200:
            return redirect('/neural-network?status=1&message=neural_network_log_error')
        #endif
        
        data = result.get("data")
        dbg.log("data >>>" + str(data), INFO=3)
    #endif
    
    return render_teng("neural-network_learn-stat.html", log_list=logs, learn_data=data)
#enddef

@app.route("/neural-network/learn-stat/<int:id>", methods=["POST"])
def neural_network__learn_stat_POST(id):
    neural_network = {}
    if id:
        result = conf.backend.proxy.neural_network.getLogs(id)
        if result.get("status") != 200:
            return redirect('/neural-network?status=1&message=neural_network_not_found')
        #endif
        logs = result.get("data")
    #endif
    
    log_name = request.form.get("selected")
    
    if log_name: 
        return redirect('/neural-network/learn-stat/%d/%s'%id%log_name)
    #endif
    
    return render_teng("neural-network_learn-stat.html?status=1&message=neural_network_log_error", log_list=logs)
#enddef
