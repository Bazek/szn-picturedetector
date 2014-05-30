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


#ifndef ERROR_H_
#define ERROR_H_

#include <string>

#include <sqlwrapper/sqlwrapper.h>
#include <sqlwrapper/dbstuff.h>

namespace SqlWrapper {
    class SqlWrapper_t;
}

#define ERROR(logLevel, errCode, format...) \
    do { \
        Error_t e(errCode, format); \
        LOG(logLevel, "%s", e.message.c_str()); \
        throw e; \
    } while (false)

#define DBERROR(logLevel, db) \
    do { \
        Error_t e(db); \
        LOG(logLevel, "%s", e.message.c_str()); \
        throw e; \
    } while (false)

enum ErrorCode_t {
    // do not change this zero!
    FE_OK = 0,            // Operation succeeded.
    FE_LIBC,              // System call error.
    FE_EXISTS,            // Object exists.
    FE_NEXISTS,           // Object does not exist.
    FE_SQL,               // MySQL error.
    FE_ARGUMENT,          // Bad argument.
    FE_FORBIDDEN,         // Operation forbidden.
    FE_INTEGRITY,         // Integrity error.
    FE_INTERNAL_ERROR,    // Internal error.
    FE_QUOTA_EXCEEDED,    // Quota exceeded.
    FE_TRY_LATER,         // Try again.

    // prepend new error codes before this one
    FE_LASTERROR
};

struct Error_t {
    /**
     * Create exception.
     */
    Error_t(ErrorCode_t code, const char *format, ...);

    Error_t(SqlWrapper::SqlWrapper_t *db);

    Error_t(SqlWrapper::DBError_t exc);

    ErrorCode_t code;

    std::string message;
};

#endif // ERROR_H_
