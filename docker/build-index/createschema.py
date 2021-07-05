#!/usr/bin/env python
from arc.nlitools import solrmarc
from arc import solrtools
import sys

server = sys.argv[1]

core = solrtools.SolrCore(f"{server}:8983/solr/nlibooks",)
resps = list(core.build_hebrew_shema(solrmarc.HEBFIELDS))
print(core.add_copy_fields("alltitles", solrmarc.TITLEFILEDS))
print(core.add_copy_fields("allnames", solrmarc.NAMEFIELDS))

resp = core.add_source_field()
print(resp.text)

core = solrtools.SolrCore(f"{server}:8983/solr/nliauth",)
resps = list(core.build_hebrew_shema(solrmarc.HEBFIELDS))
print(core.add_copy_fields("allnames", solrmarc.NAMEFIELDS))

resp = core.add_source_field()
print(resp.text)
