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


#include <algorithm>
#include <iostream>
#include <cfgparser.h>
#include <metaserver/ipcmanager.h>
#include <metaserver/text.h>
#include <metaserver/service.h>
#include <metaserver/semlock.h>

#include <sqlwrapper/sqlwrapper.h>
#include <sqlwrapper/sqlwrapperconfig.h>
#include <sqlwrapper/dbstuff.h>
#include <set>

#include "error.h"
#include "core.h"
#include "transaction.h"
#include <dbglog.h>



/**
 * @short Constructor.
 * @param config cfgparser class
 * @param ipc Metaserver ipc manager
 */
Core_t::Core_t(const ConfigParser_t &parser, MetaServer::IPCManager_t *ipc)
    : parser(&parser), config(new Config_t(parser))
{
    DBG(DBG4, "Core_t::constructor()");

    //db = new SqlWrapper::SqlWrapper_t(SqlWrapper::configureParameters(parser));
    //checkDatabase(db);

}


/**
 * Destructor
 */
Core_t::~Core_t() {
    delete config;
    //delete db;
}


/**
 * Initialize new child
 */
int Core_t::childInit() {
    DBG(DBG4, "Core_t::childInit()");

    // connect to database
    // db->connect();

    DBG(DBG4, "Core_t::childInit() done");
    return 0;
}


/**
 * Return random number
 * @return random number
 */
int Core_t::returnNumber() {
    DBG(DBG4, "Core_t::returnNumber()");

    /*
    std::stringstream query;
    query << "SELECT * FROM table" << id;

    RWTransaction_t trans(db);

    if (db->read_query(query.str())) {
        trans.rollback();
        DBERROR(ERR2, db);
    }

    SqlWrapper::DBResult_t result(db);

    for(int i = result.size(); i; --i) {

        MyStruct_t myStruct;

        result >> myStruct.id1 >> myStruct.id2 >> myStruct.id3;

        someVector.push_back(myStruct);
    }

    trans.commit();
    */

    DBG(DBG4, "Core_t::returnNumber() done");
    return random();
}
