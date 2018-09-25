import requests
import threading
import time
#from album import Album
from htmlparser import HTMLParser

class Connector(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.stop = threading.Event()
        self.session = requests.Session()
        self.parser = HTMLParser()

    def get_tags(self):
        resp = self.session.get("https://bandcamp.com/tags")
        return self.parser.parse_tags(resp.content.decode("utf-8"))

    def get_albums(self, tag):
        #send request
        #resp = self.session.get("?")
        albumlist = []
        return self.parser.parse_albums(resp.content.decode("utf-8"))

    def run(self):
        while not self.stop.is_set():
            time.sleep(1)

def main():
    conn = Connector()
    conn.get_tags()

main()