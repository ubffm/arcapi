# depends on requests
import sys
import urllib.parse
import requests
import pprint

URL = "http://localhost:8888/api/"
resp = requests.get(URL + urllib.parse.quote(sys.argv[1]))
pprint.pprint(resp.json())
