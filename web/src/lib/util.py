#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# FILE          $Id$
#
# DESCRIPTION   Admin picturedetector
#
# AUTHOR:       Petr Bartunek <petr.bartunek@firma.seznam.cz>
#
# Copyright (C) Seznam.cz a.s. 2014
# All Rights Reserved
#




def utifize(variable):
    t = type(variable)

    if t == unicode:
        return variable.encode("utf8")
    elif t == dict:
        for key in variable:
            variable[key] = utifize(variable[key])
        #endfor

        return variable
    elif t == list:
        new = []

        for item in variable:
            new.append(utifize(item))
        #endfor

        return new
    elif t == str:
        return variable
    elif t == int:
        return variable
    #endif

    return variable
#enddef
