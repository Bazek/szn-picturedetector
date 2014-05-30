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


#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#include <string>
#include <dbglog.h>
#include <cfgparser.h>

#include "config.h"


/** Read config file and parse values from it.
  * @param filename Config file pathname. */
Config_t::Config_t(const ConfigParser_t& configParser)
{

#define GET_CONFIG_VALUE(SECTION, NAME, VALUE) \
    if (!configParser.getValue(SECTION, NAME, &VALUE)) \
        DBG(WARN2, "Configuration: " NAME " in " SECTION " was not defined.");

    // Get parameters from config file
    //GET_CONFIG_VALUE("section", "value", var.to.save);

    // Database connection
    //GET_CONFIG_VALUE("mysql-master", "Host", dbParams.host);
    //GET_CONFIG_VALUE("mysql-master", "Port", dbParams.port);
    //GET_CONFIG_VALUE("mysql-master", "User", dbParams.user);
    //GET_CONFIG_VALUE("mysql-master", "Password", dbParams.password);
    //GET_CONFIG_VALUE("mysql-master", "Database", dbParams.database);
    //GET_CONFIG_VALUE("mysql-master", "Socket", dbParams.socket);
    //GET_CONFIG_VALUE("mysql-master", "ConnectTimeout", dbParams.connectTimeout);
    //GET_CONFIG_VALUE("mysql-master", "RetryDelay", dbParams.retryDelay);

#undef GET_CONFIG_VALUE

}
