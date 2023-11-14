#!/usr/bin/env python
from arc.nlitools import solrmarc
from arc import solrtools
import sys

server = sys.argv[1]
try:
    proxies = {"http": "socks5h://" + sys.argv[2]}
except IndexError:
    proxies = None

print("creating nlibooks")
core = solrtools.SolrCore(f"{server}:8983/solr/nlibooks", proxies=proxies)
resps = list(core.build_hebrew_shema(solrmarc.HEBFIELDS))
print(core.add_copy_fields("alltitles", solrmarc.TITLEFILEDS))
print(core.add_copy_fields("allnames", solrmarc.NAMEFIELDS))

resp = core.add_source_field()
print(resp.text)

print("creating nliauth")
core = solrtools.SolrCore(f"{server}:8983/solr/nliauth", proxies=proxies)
resps = list(core.build_hebrew_shema(solrmarc.HEBFIELDS))
print(core.add_copy_fields("allnames", solrmarc.NAMEFIELDS))

resp = core.add_source_field()
print(resp.text)
