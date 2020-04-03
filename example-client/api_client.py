# depends on requests
import json
import urllib.parse
import requests

encode = json.JSONEncoder(ensure_ascii=False).encode


class ArcClient:
    def __init__(self, url):
        """
        url -- url of the arc web service
        """
        self.url = url
        self.session = requests.Session()

    def get(self, method, data):
        return self.session.get("/".join((self.url, method, urllib.parse.quote(data))))

    def json(self, method, data):
        return self.client(method, encode(data))
