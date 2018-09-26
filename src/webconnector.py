import requests
import threading
import time
import logging
#from album import Album
from htmlparser import HTMLParser

LOG_FORMAT = '%(asctime)-15s | %(module)s %(name)s %(process)d %(thread)d | %(funcName)20s() - Line %(lineno)d | %(levelname)s | %(message)s'
logging.basicConfig(format=LOG_FORMAT, level=logging.DEBUG)
LOGGER = logging.getLogger('rbmd.webconnector')

class Connector(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.stop = threading.Event()
        self.session = requests.Session()
        self.parser = HTMLParser()
        self.apiurl = "https://bandcamp.com/api/discover/3/get_web?g=%s&s=%s&p=%s&gn=0&f=all&w=%s" # genre, recommlvl, pagenum, timeframe
        LOGGER.debug("Initialized %s" % self)

    def get_tags(self):
        LOGGER.info("Obtaining Tags")
        resp = self.session.get("https://bandcamp.com/tags")
        #LOGGER.debug(resp.content.decode("utf-8"))
        return self.parser.parse_tags(resp.content.decode("utf-8"))

    def get_albums(self, tag):
        #send request
        timeframes = ["-1", "0", "527", "526", "525", "524", "523", "522"]
        recommlvl = ["top", "new", "rec"]
        albumlist = []
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
                        albumlist.append(album)
        return albumlist

    def run(self):
        while not self.stop.is_set():
            time.sleep(1)

def main():
    conn = Connector()
    print(conn.parser.parse_maxpages(conn.session.get("https://bandcamp.com/api/discover/3/get_web?g=jazz&g=ambient&s=top&p=0&gn=0&f=all&w=0").json()))

main()