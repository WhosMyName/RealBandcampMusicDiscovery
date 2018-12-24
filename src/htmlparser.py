""" class to allow easy parsing in seperate thread """

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
flhdlr = logging.FileHandler("../logs/error.log", mode="a", encoding="utf-8", delay=False)
flhdlr.setLevel(logging.DEBUG)
flhdlr.setFormatter(logging.Formatter(LOG_FORMAT))
LOGGER.addHandler(strmhdlr)
LOGGER.addHandler(flhdlr)
def uncaught_exceptions(exc_type, exc_val, exc_trace):
    import traceback
    if exc_type is None and exc_val is None and exc_trace is None:
        exc_type, exc_val, exc_trace = sys.exc_info()
    LOGGER.exception("Uncaught Exception of type %s was caught: %s\nTraceback:\n%s" % (exc_type, exc_val, traceback.print_tb(exc_trace)))
    try:
        del exc_type, exc_val, exc_trace
    except:
        LOGGER.exception(Exception("Exception args could not be deleted"))
sys.excepthook = uncaught_exceptions


class HTMLParser():
    def __init__(self):
        LOGGER.debug("Initialized %s" % self)


    def __del__(self):
        del(self)


    def parse_tags(self, data):
        LOGGER.info("Parsing Tags")
        taglist = set()
        for line in data:
            if "class=\"tag size" in line:
                tag = line.split("/tag/")[1].split("\" ")[0]
                #LOGGER.debug("Found Tag: %s" % tag)
                if tag != "":
                    taglist.add(tag)
        taglist.add("None")
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
        LOGGER.info("returning to connector")
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


    def parse_album_metadata(self, data): #grab all metadata
        LOGGER.info("Parsing Tags")
        genrelist = set()
        for line in data:
            if "class=\"tag\" href=" in line:
                genre = line.split("/tag/")[1].split("\" ")[0]
                LOGGER.debug("Found Genre: %s" % genre)
                genrelist.add(genre)
        return genrelist


    def get_cover(self, data):
        #parse url from data
        #return url
        pass
