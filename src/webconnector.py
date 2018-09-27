import requests
import threading
from time import sleep
import logging
import sys
#from album import Album
from htmlparser import HTMLParser

LOG_FORMAT = '%(asctime)-15s | %(module)s %(name)s %(process)d %(thread)d | %(funcName)20s() - Line %(lineno)d | %(levelname)s | %(message)s'
logging.basicConfig(format=LOG_FORMAT, level=logging.DEBUG, filename="../logs/error.log")
strmhdlr = logging.StreamHandler(sys.stdout)
strmhdlr.setLevel(logging.INFO)
strmhdlr.setFormatter(logging.Formatter(LOG_FORMAT))
LOGGER = logging.getLogger('rbmd.webconnector')
LOGGER.addHandler(strmhdlr)

class Connector(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.stop = threading.Event()
        self.session = requests.Session()
        self.parser = HTMLParser()
        self.parser.start()
        self.apiurl = "https://bandcamp.com/api/discover/3/get_web?g=%s&s=%s&p=%s&gn=0&f=all&w=%s" # genre, recommlvl, pagenum, timeframe
        LOGGER.debug("Initialized %s" % self)

    def __del__(self):
        self.parser.__del__()
        self.stop.set()

    def get_tags(self):
        LOGGER.info("Obtaining Tags")
        resp = self.session.get("https://bandcamp.com/tags")
        #LOGGER.debug(resp.content.decode("utf-8"))
        return self.parser.parse_tags(resp.content.decode("utf-8").split("\n"))

    def get_albums(self, tag):
        #send request
        timeframes = ["-1", "0", "527", "526", "525", "524", "523", "522"]
        recommlvl = ["top", "new", "rec"]
        albumlist = [] # make this a set
        pagenumbers = 1
        for timeframe in timeframes:
            for recomm in recommlvl:
                LOGGER.debug("Getting MaxPages for %s" % self.apiurl % (tag, recomm, pagenum, time))
                resp1 = self.session.get(self.apiurl % (tag, recomm, pagenum, time))
                maxpages = self.parser.parse_maxpages(resp1.json())
                LOGGER.debug("MaxPages for %s is %s" % (self.apiurl, maxpages) % (tag, recomm, pagenum, time))
                for pagenum in range(0,maxpages):
                    LOGGER.debug("Getting data from %s" % self.apiurl % (tag, recomm, pagenum, time))
                    resp2 = self.session.get(self.apiurl % (tag, recomm, pagenum, time))
                    albums = self.parser.parse_albums(resp2.json())
                    LOGGER.debug("%r" % albums)
                    for album in albums:
                        albumlist.append(self.update_album_genre(album))
        return albumlist

    def update_album_genre(self, album):
        LOGGER.info("Updating Tags for %s" % album.name)
        resp = self.session.get(album.url)
        album.genre = self.parser.parse_album_genres(resp.content.decode("utf-8").split("\n"))
        return album

    def run(self):
        while not self.stop.is_set():
            sleep(1)

def main():
    conn = Connector()
    conn.start()
    resp = conn.session.get(conn.apiurl % ("rock", "top", "0", "0"))
    albums = conn.parser.parse_albums(resp.json())
    for album in albums:
        print(conn.update_album_genre(album))

main()  