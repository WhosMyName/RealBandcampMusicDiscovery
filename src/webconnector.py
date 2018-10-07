import requests
import threading
from time import sleep
import logging
import sys
#from album import Album
from htmlparser import HTMLParser

LOG_FORMAT = '%(asctime)-15s | %(module)s %(name)s %(process)d %(thread)d | %(funcName)20s() - Line %(lineno)d | %(levelname)s | %(message)s'
LOGGER = logging.getLogger('rbmd.webconnector')
LOGGER.setLevel(logging.DEBUG)
strmhdlr = logging.StreamHandler(sys.stdout)
strmhdlr.setLevel(logging.INFO)
strmhdlr.setFormatter(logging.Formatter(LOG_FORMAT))
flhdlr = logging.FileHandler("../logs/error.log", mode='a', encoding="utf-8", delay=False)
flhdlr.setLevel(logging.DEBUG)
flhdlr.setFormatter(logging.Formatter(LOG_FORMAT))
LOGGER.addHandler(strmhdlr)
LOGGER.addHandler(flhdlr)

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
        print("tags")
        LOGGER.info("Obtaining Tags")
        resp = self.session.get("https://bandcamp.com/tags")
        #LOGGER.debug(resp.content.decode("utf-8"))
        return self.parser.parse_tags(resp.content.decode("utf-8").split("\n"))

    def get_albums(self, func, tag):
        LOGGER.info("Getting Albums for Tag: %s" % tag)
        timeframes = ["-1"]#, "0", "527", "526", "525", "524", "523", "522"]
        recommlvl = ["top", "new", "rec"]
        albumlist = set()
        for timeframe in timeframes:
            for recomm in recommlvl:
                LOGGER.info("Getting MaxPages for %s" % self.apiurl % (tag, recomm, "0", timeframe))
                resp1 = self.session.get(self.apiurl % (tag, recomm, "0", timeframe))
                maxpages = self.parser.parse_maxpages(resp1.json())
                LOGGER.debug("MaxPages for %s is %s" % (self.apiurl, maxpages) % (tag, recomm, "0", timeframe))
                for pagenum in range(0, 1): #maxpages):
                    LOGGER.debug("Getting data from %s" % self.apiurl % (tag, recomm, pagenum, timeframe))
                    resp2 = self.session.get(self.apiurl % (tag, recomm, pagenum, timeframe))
                    albums = self.parser.parse_albums(resp2.json())
                    for album in albums:
                        album = self.update_album_genre(album)
                    LOGGER.debug("%r" % albums)
                    func(albums)

    def update_album_genre(self, album):
        LOGGER.info("Updating Tags for %s" % album.name)
        resp = self.session.get(album.url)
        album.genre = self.parser.parse_album_genres(resp.content.decode("utf-8").split("\n"))
        return album

    def get_album_cover(self, album):
        #get
        #parse
        #dl
        #return
        pass

    def run(self):
        while not self.stop.is_set():
            sleep(0.1)

def __main__():
    conn = Connector()
    conn.start()
    #conn.get_tags()
    conn.get_albums("rock")
    conn.__del__()

if __name__ == "__main__":
    __main__()  