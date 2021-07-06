# depends on requests
import sys
import urllib.parse
import requests
import pprint

session = requests.Session()
domain, query = sys.argv[1:3]
URL = f"{domain}/api/"
resp = session.get(URL + urllib.parse.quote(query)) #, verify=False)
pprint.pprint(resp.json())
