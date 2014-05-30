/*
 * DESCRIPTION
 *
 * PROJECT
 *
 * AUTHOR           Petr Bartunek <Petr.Bartunek@firma.seznam.cz>
 *
 * Copyright (C) Seznam.cz a.s. 2013
 * All Rights Reserved
 *
 */


#ifndef _CONFIG_H
#define _CONFIG_H

#include <string>
#include <cfgparser.h>
#include <sqlwrapper/sqlwrapperconfig.h>

/** Configuration options class. */
class Config_t
{

public:
    Config_t(const ConfigParser_t& configParser);

    // Public configuration options

    // Database connection
    SqlWrapper::SqlWrapper_t::ConnParams_t dbParams;

};

#endif //_CONFIG_H
