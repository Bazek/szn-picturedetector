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
#include <stdexcept>
#include <memory>
#include <dbglog.h>
#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>

#include "error.h"
#include "core.h"
#include "frpcinterface.h"

/**
 * Constructor
 */
FastRPCInterface_t::FastRPCInterface_t(
        MetaServer::FastRPC::ServerStub_t &serverStub, Core_t *core)
            : serverStub(serverStub), core(core) {

    // new seed for rand
    srand(getpid());

    // register HTTP HEAD method handler
    serverStub.registerHeadMethod(FRPC::boundHeadMethod
                                  (&FastRPCInterface_t::httpHead, *this));

#define REGMET(name, callback, signature) \
    serverStub.registerMethod(name, \
        FRPC::boundMethod(&FastRPCInterface_t::callback, *this), signature)

    REGMET("skeleton.test.method", skeleton_test_method, "S:");

#undef REGMET

}

namespace {
    int codeMapping[] = {
    /* E_OK */ 200,
    /* E_LIBC */ 500,
    /* E_EXISTS */ 404,
    /* E_NEXISTS */ 404,
    /* E_ARGUMENT */ 401,
    /* E_FORBIDDEN */ 405,
    /* E_INTEGRITY */ 403,
    /* E_INTERNAL_ERROR */ 500,
    /* E_QUOTA_EXCEEDED */ 407,
    /* E_TRY_LATER */ 301,
    /* E_INPUT_INCONSISTENCY */ 401,
    /* E_BACKEND */ 500,
    };

    FRPC::Struct_t& errorResponse(FRPC::Pool_t &pool, const Error_t &e) {
        int status = 500;
        if ((e.code >= 0) && (e.code < static_cast<int>(sizeof(codeMapping))))
            status = codeMapping[e.code];

        return MetaServer::FastRPC::response(pool, status, e.message);
    }
}


#define FASTRPCINTERFACE_METHOD(name) \
    FRPC::Value_t& FastRPCInterface_t::name(FRPC::Pool_t &pool, \
            FRPC::Array_t &params)

#define TRY_BEGIN try
#define TRY_END catch (const Error_t &e) { \
                    return errorResponse(pool, e); \
                } catch (const SqlWrapper::DBError_t &dbe) { \
                    Error_t e(dbe); \
                    LOG(ERR2, "%s", e.message.c_str()); \
                    return errorResponse(pool, e); \
                }

bool FastRPCInterface_t::httpHead() {

    // OK
    return true;
}

/**
 * @short frpc method
 */
FASTRPCINTERFACE_METHOD(skeleton_test_method) {

    TRY_BEGIN {

        LOG(INFO3, "Test method start.");

        params.checkItems("");
        int i = core->returnNumber();

        LOG(INFO3, "Test method end.");

        return MetaServer::FastRPC::OK(pool).append("number", pool.Int(i));

    } TRY_END;

    LOG(INFO3, "Test method end.");

    return MetaServer::FastRPC::OK(pool);

}
