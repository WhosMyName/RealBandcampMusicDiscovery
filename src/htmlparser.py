"""rewfew"""

import sys
import threading
from time import sleep
import logging
from album import Album

LOG_FORMAT = '%(asctime)-15s | %(module)s %(name)s %(process)d %(thread)d | %(funcName)20s() - Line %(lineno)d | %(levelname)s | %(message)s'
LOGGER = logging.getLogger('rbmd.htmlparser')
LOGGER.setLevel(logging.DEBUG)
strmhdlr = logging.StreamHandler(stream=sys.stdout)
strmhdlr.setLevel(logging.INFO)
strmhdlr.setFormatter(logging.Formatter(LOG_FORMAT))
flhdlr = logging.FileHandler("../logs/error.log", mode='a', encoding="utf-8", delay=False)
flhdlr.setLevel(logging.DEBUG)
flhdlr.setFormatter(logging.Formatter(LOG_FORMAT))
LOGGER.addHandler(strmhdlr)
LOGGER.addHandler(flhdlr)

class HTMLParser(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.stop = threading.Event()
        LOGGER.debug("Initialized %s" % self)

    def __del__(self):
        self.stop.set()

    def parse_tags(self, data):
        LOGGER.info("Parsing Tags")
        taglist = set()
        for line in data:
            if "class=\"tag size" in line:
                tag = line.split("/tag/")[1].split("\" ")[0]
                LOGGER.debug("Found Tag: %s" % tag)
                taglist.add(tag)
        return sorted(taglist)
    
    def parse_albums(self, data):
        LOGGER.info("Parsing Albums")
        albumlist = set()
        albool = False

        name = ""
        url = ""
        band = ""
        cover_url = ""

        for line in data:
            if ">new arrivals</a>" in line and not albool:
                albool = True
            elif "<a href=" in line and albool:
                url = line.split("<a href=\"")[1].split("\" title")[0]
                name = line.split("title=\"")[1].split("\">")[0]
            elif "<div class=\"tralbum" in line and albool:
                cover_url = line.split("url(")[1].split(")'")[0]
            elif "<div class=\"itemsubtext" in line and albool:
                band = line.split("\">")[1].split("</")[0]
                alb = Album(name, url, band, cover_url)
                LOGGER.debug(alb)
                albumlist.add(alb)
            elif "<div class=\"pager_" in line:
                albool = False
        return albumlist

    def parse_maxpages(self, data):
        LOGGER.info("Getting Maxpages")
        maxpages = 0
        for line in data:
            if "pagenum round4" in line:
                page = int(line.split("nofollow\">")[1].split("</a>")[0])
                if page > maxpages:
                    maxpages = page
        LOGGER.debug("Maxpages: %s" % maxpages)
        return maxpages

    def parse_album_genres(self, data):
        LOGGER.info("Parsing Tags")
        genrelist = set()
        for line in data:
            if "class=\"tag\" href=" in line:
                genre = line.split("/tag/")[1].split("\" ")[0]
                LOGGER.debug("Found Genre: %s" % genre) # LOGGER.debug
                genrelist.add(genre)
        return genrelist

    def get_cover(self, data):
        #parse url from data
        #return url
        pass

    def run(self):
        while not self.stop.is_set():
            sleep(0.1)