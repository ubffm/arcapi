#!/bin/sh
VERSION="$1"
shift
SOLR_HOME="solr-$VERSION"
SOLR_BIN="$SOLR_HOME/bin/solr"

echo "SOLR_ULIMIT_CHECKS=false" > "$SOLR_HOME/bin/solr.in.sh"

"$SOLR_BIN" start || exit 1
while [ -n "$1" ]; do
  core="$1"
  shift

  "$SOLR_BIN" create -c "$core" || exit 1
  cp ./configs/solrconfig.xml "$SOLR_HOME/server/solr/$core/conf/solrconfig.xml"
done

cp ./configs/solr.xml "$SOLR_HOME/server/solr/solr.xml"

"$SOLR_BIN" stop
