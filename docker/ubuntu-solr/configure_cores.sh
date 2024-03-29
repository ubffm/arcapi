#!/bin/sh
SOLR_HOME="solr"
SOLR_BIN="$SOLR_HOME/bin/solr"

echo 'SOLR_ULIMIT_CHECKS=false
SOLR_JETTY_HOST="0.0.0.0"' > "$SOLR_HOME/bin/solr.in.sh"

"$SOLR_BIN" start || exit 1
while [ -n "$1" ]; do
  core="$1"
  shift

  "$SOLR_BIN" create -c "$core" || exit 1
  cp ./configs/solrconfig.xml "$SOLR_HOME/server/solr/$core/conf/solrconfig.xml"
done

cp ./configs/solr.xml "$SOLR_HOME/server/solr/solr.xml"

"$SOLR_BIN" stop
cp -rp "$SOLR_HOME/server/solr" ~/project-dir/original-config

