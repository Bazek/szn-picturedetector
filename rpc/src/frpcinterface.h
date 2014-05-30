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


#ifndef METASEARCH_FRPCINTERFACE_H
#define METASEARCH_FRPCINTERFACE_H

#include <frpc.h>
#include <metaserver/cpp-fastrpc.h>

// forwards
class Core_t;

#define FASTRPCINTERFACE_METHOD(name) \
    FRPC::Value_t& name(FRPC::Pool_t &pool, \
            FRPC::Array_t &params)

class FastRPCInterface_t {
public:
    /**
     * @short construct new frpc intreface
     */
    FastRPCInterface_t(
            MetaServer::FastRPC::ServerStub_t &serverStub, Core_t *core);

    /**
     * @short frpc method
     */
    FASTRPCINTERFACE_METHOD(skeleton_test_method);

private:
    bool httpHead();

    MetaServer::FastRPC::ServerStub_t &serverStub;

    Core_t *core;
};

#undef FASTRPCINTERFACE_METHOD

#endif // METASEARCH_FRPCINTERFACE_H
