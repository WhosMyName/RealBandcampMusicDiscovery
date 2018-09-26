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
        timeframes = ["-1", "0", "527", "526", "525", "524", "523", "522"]
        recommlvl = ["top", "new", "rec"]
        albumlist = []
        pagenumbers = 1
        for timeframe in timeframes:
            for recomm in recommlvl:
                resp1 = self.session.get("https://bandcamp.com/api/discover/3/get_web?g=%s&s=%s&p=%s&gn=0&f=all&w=%s" % (tag, recomm, pagenum, time))
                maxpages = self.parser.parse_maxpages(resp1.json())
                for pagenum in range(0,maxpages):
                    resp2 = self.session.get("https://bandcamp.com/api/discover/3/get_web?g=%s&s=%s&p=%s&gn=0&f=all&w=%s" % (tag, recomm, pagenum, time))
                    albums = self.parser.parse_albums(resp2.json())
                    for album in albums:
                        albumlist.append(album)
        return albumlist

    def run(self):
        while not self.stop.is_set():
            time.sleep(1)

def main():
    conn = Connector()
    conn.get_tags()

main()