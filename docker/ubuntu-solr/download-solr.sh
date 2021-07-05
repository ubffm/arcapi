#!/bin/sh
VERSION="$1"
SOLR_HOME="solr-$VERSION"
wget "http://mirror.23media.de/apache/lucene/solr/$VERSION/$SOLR_HOME.tgz" || exit 1
tar xaf "$SOLR_HOME.tgz" || exit 1
rm "$SOLR_HOME.tgz"
