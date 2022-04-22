#!/bin/sh
VERSION="$1"
SOLR_HOME="solr-$VERSION"
wget "https://dlcdn.apache.org/lucene/solr/$VERSION/$SOLR_HOME.tgz" || exit 1
sha512sum --check shasum.txt --ignore-missing || exit 1
tar xaf "$SOLR_HOME.tgz" || exit 1
rm "$SOLR_HOME.tgz"
