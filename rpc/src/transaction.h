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


#ifndef TRANSACTION_H
#define TRANSACTION_H

#include <sqlwrapper/sqlwrapper.h>
#include <sqlwrapper/sqlwrapperconfig.h>
#include <sqlwrapper/dbstuff.h>

class Transaction_t {
public:
    Transaction_t(SqlWrapper::SqlWrapper_t *db)
        : db(db), inTransaction(true)
    {
    }

    virtual ~Transaction_t() {
        if (inTransaction) {
            LOG(INFO1, "Automatic rollback due to stack being unwound.");
            if (db->rollback()) {
                if (std::uncaught_exception()) {
                    SqlWrapper::DBError_t exc(db);
                    LOG(ERR2, "MySQL error during automatic rollback: "
                        "<%d, %s>. Exception already thrown.",
                        exc.err, exc.message.c_str());
                } else {
                    DBERROR(ERR2, db);
                }
            }
        }
    }

    void commit() {
        if (db->commit()) DBERROR(ERR2, db);
        inTransaction = false;
    }

    void rollback() {
        if (db->rollback()) DBERROR(ERR2, db);
        inTransaction = false;
    }

protected:
    virtual void dummy() = 0;

    SqlWrapper::SqlWrapper_t *db;
    bool inTransaction;
};

class ROTransaction_t : public Transaction_t {
public:
    ROTransaction_t(SqlWrapper::SqlWrapper_t *db, bool readUncommited = false)
        : Transaction_t(db)
    {
        if (db->beginRO()) DBERROR(ERR3, db);
        // set read uncommited
        if (readUncommited == true &&
            db->read_query("SET SESSION TRANSACTION ISOLATION LEVEL READ"
                " UNCOMMITTED"))
            DBERROR(ERR2, db);
    }

    virtual ~ROTransaction_t() { };

private:
    virtual void dummy() {}
};

class RWTransaction_t : public Transaction_t {
public:
    RWTransaction_t(SqlWrapper::SqlWrapper_t *db)
        : Transaction_t(db)
    {
        if (db->beginRW()) DBERROR(ERR3, db);
    }

    virtual ~RWTransaction_t() { };

private:
    virtual void dummy() {}
};


namespace {
    void checkDatabase(SqlWrapper::SqlWrapper_t *db) {
        // connect to the DB
        if (db->connect())
            throw std::runtime_error("Cannot connect to database.");

        // rw database
        try {
            RWTransaction_t trans(db);

            // try to dispatch one simple sql command
            if (db->read_query("SELECT 1"))
                DBERROR(ERR3, db);

            SqlWrapper::DBResult_t result(db);
            trans.commit();
        } catch (Error_t) {
            // some error occurred
            throw std::runtime_error("Cannot fetch data from db.");
        }

        // ro database
        try {
            ROTransaction_t trans(db);

            // try to dispatch one simple sql command
            if (db->read_query("SELECT 1"))
                DBERROR(ERR3, db);

            SqlWrapper::DBResult_t result(db);
            trans.commit();
        } catch (Error_t) {
            // some error occurred
            throw std::runtime_error("Cannot fetch data from db.");
        }

        // close connection to the DB
        if (db->close())
            throw std::runtime_error("Cannot close database connection.");
    }

}


#define DEADLOCK_BEGIN(tries) \
    for (int RESTART_COUNTER = tries; (RESTART_COUNTER > 0); \
         --RESTART_COUNTER) { try {

#define DEADLOCK_END \
    } catch (const SqlWrapper::DBError_t &dbe) { \
        if (dbe.err == ER_LOCK_DEADLOCK) { \
            if (RESTART_COUNTER > 1) { \
                LOG(INFO2, "Trying to restart transaction after deadlock."); \
                continue; \
            } \
            LOG(ERR2, "Too many deadlocks. Bailing out."); \
        } \
        throw; \
    } break; }


#endif

