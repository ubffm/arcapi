#!/usr/bin/env python
import json
import sys
from arc import solrtools
import sys


def main():
    decode = json.JSONDecoder().decode

    server = sys.argv[1]
    index = sys.argv[2]
    json_records = sys.stdin

    core = solrtools.SolrCore(f"{server}:8983/solr/" + index)
    docs = map(decode, json_records)
    for resp in core.add_docs(docs, 1000):
        print(resp)


if __name__ == "__main__":
    main()
