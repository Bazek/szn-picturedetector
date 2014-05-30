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


#ifndef METASEARCH_CORE_H
#define METASEARCH_CORE_H

#include <sqlwrapper/sqlwrapper.h>

#include <metaserver/cpp-fastrpc.h>
#include "config.h"


/**
 * Main class for metasearch server.
 */
class Core_t {
public:
    /**
     * @short Constructor.
     * @param config cfgparser class
     * @param ipc Metaserver ipc manager
     */
    Core_t(const ConfigParser_t &config, MetaServer::IPCManager_t *ipc);

    /**
     * Destructor
     */
    ~Core_t();

    /**
     * @short Initialize child - server worker process
     * @return On success 0, else -1
     */
    int childInit();

    /**
     * Config parser
     */
    const ConfigParser_t *parser;

    /**
     * @short Pointer to config.
     */
    Config_t *config;

    /**
     * Return random number
     * @return random number
     */
    int returnNumber();

private:

    /**
     * Database connection object
     */
    SqlWrapper::SqlWrapper_t *db;
};

#endif // METASEARCH_CORE_H
