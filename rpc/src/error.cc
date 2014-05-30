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


#include <stdio.h>
#include <stdarg.h>

#include <sqlwrapper/sqlwrapper.h>
#include <sqlwrapper/dbstuff.h>

#include "error.h"

Error_t::Error_t(ErrorCode_t code, const char *format, ...)
    : code(code)
{
    va_list valist;
    va_start(valist, format);

    char msg[2048];
    vsnprintf(msg, sizeof(msg), format, valist);
    message = msg;

    va_end(valist);
}

Error_t::Error_t(SqlWrapper::SqlWrapper_t *db)
    : code(FE_SQL)
{
    SqlWrapper::DBError_t exc(db);

    // switch over methods
    switch (exc.err) {
    case ER_DUP_ENTRY:
        code = FE_EXISTS;
        break;

    default:
        break;
    }

    char msg[2048];
    snprintf(msg, sizeof(msg), "MySQL error: <%d, %s>.",
             exc.err, exc.message.c_str());
    message = msg;
}

Error_t::Error_t(SqlWrapper::DBError_t exc)
    : code(FE_SQL)
{
    // switch over methods
    switch (exc.err) {
    case ER_DUP_ENTRY:
        code = FE_EXISTS;
        break;

    default:
        break;
    }

    char msg[2048];
    snprintf(msg, sizeof(msg), "MySQL error: <%d, %s>.",
             exc.err, exc.message.c_str());
    message = msg;
}
