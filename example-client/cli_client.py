# depends on requests
import sys
import urllib.parse
import requests
import pprint


session = requests.Session()
domain = sys.argv[1]
query = sys.stdin.read()
URL = f"{domain}/api/"
resp = session.get(URL + urllib.parse.quote(query), verify=False)
print(resp.text)
