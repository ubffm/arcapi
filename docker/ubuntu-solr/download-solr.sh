#!/bin/sh
SOLR_URL="$1"
wget "$SOLR_URL" || exit 1
mv solr*.tgz* solr.tgz
tar xaf solr.tgz || exit 1
rm solr.tgz
ln -s "$PWD"/solr* solr
