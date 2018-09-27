"""rewfew"""

import sys
import threading
from time import sleep
import logging
from tags import Tag
from album import Album
from math import ceil

LOG_FORMAT = '%(asctime)-15s | %(module)s %(name)s %(process)d %(thread)d | %(funcName)20s() - Line %(lineno)d | %(levelname)s | %(message)s'
logging.basicConfig(format=LOG_FORMAT, level=logging.DEBUG, filename="../logs/error.log")
strmhdlr = logging.StreamHandler(sys.stdout)
strmhdlr.setLevel(logging.INFO)
strmhdlr.setFormatter(logging.Formatter(LOG_FORMAT))
LOGGER = logging.getLogger('rbmd.htmlparser')
LOGGER.addHandler(strmhdlr)

class HTMLParser(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.stop = threading.Event()
        LOGGER.debug("Initialized %s" % self)

    def __del__(self):
        self.stop.set()

    def parse_tags(self, data):
        LOGGER.info("Parsing Tags")
        taglist = []#make set
        for line in data:
            if "class=\"tag size" in line:
                tag = line.split("/tag/")[1].split("\" ")[0]
                LOGGER.info("Found Tag: %s" % tag)
                taglist.append(tag)
        return taglist
    
    def parse_albums(self, data): #make this a set
        LOGGER.info("Parsing Albums")
        albumlist = []
        for rawalbum in data["items"]:
            alb = Album(rawalbum["primary_text"], "https://%s.bandcamp.com/album/%s" % (rawalbum["url_hints"]["subdomain"], rawalbum["url_hints"]["slug"]),rawalbum["secondary_text"], None)
            LOGGER.debug(alb)
            albumlist.append(alb)
        return albumlist

    def parse_maxpages(self, data):
        maxentries = data["total_count"]
        maxpages = ceil(maxentries/48)
        return int(maxpages)

    def parse_album_genres(self, data): # this too
        LOGGER.info("Parsing Tags")
        genrelist = []
        for line in data:
            if "class=\"tag\" href=" in line:
                genre = line.split("/tag/")[1].split("\" ")[0]
                LOGGER.info("Found Genre: %s" % genre) # debug
                genrelist.append(genre)
        return genrelist

    def run(self):
        while not self.stop.is_set():
            sleep(1)