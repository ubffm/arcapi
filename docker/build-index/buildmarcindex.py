#!/usr/bin/env python
import json
import sys
from arc import solrtools


def main():
    decode = json.JSONDecoder().decode

    server = sys.argv[1]
    index = sys.argv[2]
    try:
        proxies = {"http": "socks5h://" + sys.argv[3]}
    except IndexError:
        proxies = None

    json_records = sys.stdin

    core = solrtools.SolrCore(f"{server}:8983/solr/" + index, proxies=proxies)
    docs = map(decode, json_records)
    for resp in core.add_docs(docs, 1000):
        print(resp)


if __name__ == "__main__":
    main()
