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

from dbglog     import dbg
from datetime   import datetime

from app import conf


def render_teng(template, **data):
    """
    Vyrenderuje stranku pres Teng

    dataRoot - Teng data root
    template - Template filename

    """

    dbg.log("Generating page %s", (template, ), INFO=2)

    if data is None:
        data = {}
    #endif

    data["YEAR"] = datetime.now().year

    data_root = conf.teng.createDataRoot(data)

    # Generate page
    res = conf.teng.generatePage(
        templateFilename=template,
        data=data_root,
        configFilename=conf.template.configFile,
        dictionaryFilename=conf.template.dictionaryFile,
        contentType="text/html",
        encoding="UTF-8"
    )

    # Log if error
    for error in res["errorLog"]:
        dbg.log("%s:%s:%s: %s", (error["filename"], error["line"], error["column"], error["message"]), ERR=2)
    #endfor

    # Send page to user
    return res["output"]

#enddef
