#
# DESCRIPTION
#
# PROJECT
#
# AUTHOR            Petr Bartunek <Petr.Bartunek@firma.seznam.cz>
#
# Copyright (C) Seznam.cz a.s. 2014
# All Rights Reserved


AM_CPPFLAGS = -I$(top_srcdir)

CXXFLAGS = -Wall -Wno-deprecated -ggdb -DDEBUG -DUSE_OSTRSTREAM ${CXXEXTRAFLAGS}

lib_LTLIBRARIES = rpc.la

rpc_la_SOURCES = error.cc \
	frpcinterface.cc \
	core.cc \
	rpc.cc \
	config.cc

rpc_la_LDFLAGS = -module -avoid-version

# test linking
noinst_PROGRAMS = test-link
test_link_SOURCES = test-link.cc
test_link_LDADD = rpc.la ${msfastrpchandler} -lmetaserver\
		-lsslwrapper -lcfgparser -ldbglog -luuid

test-link.cc:
	echo 'int main() { return 0; }' > $@

CLEANFILES = test-link.cc

