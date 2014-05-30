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


#include <iostream>
#include <cfgparser.h>
#include <metaserver/cpp-fastrpc.h>

#include "frpcinterface.h"
#include "core.h"

namespace {
    struct IConfig_t : public MetaServer::FastRPC::InterfaceConfig_t {
        IConfig_t(const ConfigParser_t &config,
                  MetaServer::FastRPC::ServerStub_t &serverStub)
            : MetaServer::FastRPC::InterfaceConfig_t(),
              core(new Core_t(config, &serverStub.ipcManager())),
              frpc(serverStub, core)
        {
        }

        virtual ~IConfig_t() {}

        Core_t *core;
        FastRPCInterface_t frpc;
    };

    MetaServer::FastRPC::InterfaceConfig_t*
    isInit(const ConfigParser_t &config,
            MetaServer::FastRPC::ServerStub_t &serverStub)
    {
        return new IConfig_t(config, serverStub);
    }

    void isChildInit(MetaServer::FastRPC::ServerStub_t &serverStub,
                     MetaServer::FastRPC::InterfaceConfig_t *iconfig)
    {
        dynamic_cast<IConfig_t&>(*iconfig).core->childInit();
    }

    void destroy(MetaServer::FastRPC::ServerStub_t &serverStub, 
                 MetaServer::FastRPC::InterfaceConfig_t *iconfig) 
    { 
        delete dynamic_cast<IConfig_t *>(iconfig); 
    }
}

#ifndef DEBIAN_PACKAGE_VERSION
#define DEBIAN_PACKAGE_VERSION "UNKNOWN"
#endif

MetaServer::FastRPC::ModuleSetup_t rpc_module = {
    CPP_FASTRPC_MODULE_HEAD(DEBIAN_PACKAGE_VERSION),
    /* init = */ isInit,
    /* childInit = */ isChildInit,
    /* childDestroy = */ 0,
    /* destroy = */ destroy
};

