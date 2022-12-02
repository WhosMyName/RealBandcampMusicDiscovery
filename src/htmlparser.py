""" utils to allow easy parsing in seperate thread(s) """

import sys
import logging
import json
from html import unescape
from os import name as os_name

if os_name == "nt":
    SLASH = "\\"
else:
    SLASH = "/"

from album import Album

LOGGER = logging.getLogger('rbmd.htmlparser')
LOG_FORMAT = "%(asctime)-15s | %(levelname)s | %(module)s %(name)s %(process)d %(thread)d | %(funcName)20s() - Line %(lineno)d | %(message)s"
LOGGER.setLevel(logging.DEBUG)
STRMHDLR = logging.StreamHandler(stream=sys.stdout)
STRMHDLR.setLevel(logging.INFO)
STRMHDLR.setFormatter(logging.Formatter(LOG_FORMAT))
FLHDLR = logging.FileHandler(f"..{SLASH}logs{SLASH}error.log", mode="a", encoding="utf-8", delay=False)
FLHDLR.setLevel(logging.DEBUG)
FLHDLR.setFormatter(logging.Formatter(LOG_FORMAT))
LOGGER.addHandler(STRMHDLR)
LOGGER.addHandler(FLHDLR)
def uncaught_exceptions(exc_type, exc_val, exc_trace):
    """ injected function to log exceptions """
    import traceback
    if exc_type is None and exc_val is None and exc_trace is None:
        exc_type, exc_val, exc_trace = sys.exc_info()
    LOGGER.exception("Uncaught Exception of type %s was caught: %s\nTraceback:\n%s", exc_type, exc_val, traceback.print_tb(exc_trace))
    try:
        del exc_type, exc_val, exc_trace
    except Exception as excp:
        LOGGER.exception("Exception caught during tb arg deletion:\n%s", excp)
sys.excepthook = uncaught_exceptions


def parse_tags(data):
    """ simple func for parsing bandcamps "default" tags """
    LOGGER.info("Parsing Tags")
    tagset = set()
    for line in data:
        if "class=\"tag size" in line:
            tag = line.split("/tag/")[1].split("\" ")[0]
            #LOGGER.debug("Found Tag: %s" % tag)
            if tag != "":
                tagset.add(tag)
    taglist = sorted(tagset)
    taglist.append("None")
    return taglist


def parse_albums(data):
    """ func that does the basic album parsing"""
    LOGGER.info("Parsing Albums")
    albumlist = set()
    albool = False

    name = ""
    url = ""
    band = ""
    cover_url = ""

    for line in data:
        if "item_list" in line and not albool:
            albool = True
        elif "<a href=" in line and albool:
            url = line.split("<a href=\"")[1].split("\" title")[0]
            name = line.split("title=\"")[1].split("\">")[0]
            if " by " in name:
                name = name.split(" by ")[0]
        elif "<img class=\"art" in line and albool:
            cover_url = line.split("src=\"")[1].split("\" alt")[0]
        elif "<div class=\"itemsubtext" in line and albool:
            band = unescape(line.split("\">")[1].split("</")[0])
            alb = Album(name, url, band, cover_url)
            LOGGER.debug(alb)
            albumlist.add(alb)
        elif "<div class=\"pager_" in line:
            albool = False
    LOGGER.debug("returning to connector")
    return albumlist


def parse_maxpages(data):
    """ helper function for maxpages (esp. usefull for tag/genre pages /w < 10 maxpages) """
    LOGGER.debug("Getting Maxpages")
    maxpages = 0
    for line in data:
        if "pagenum round4" in line:
            page = int(line.split("\">")[1].split("</a>")[0])
            if page > maxpages:
                maxpages = page
    LOGGER.debug("Maxpages: %s", maxpages)
    return maxpages


def parse_album_metadata(data): #grab all metadata
    """ parsing metadata (tags, urls, covers, etc...) """
    LOGGER.debug("Parsing Tags")
    genrelist = set()
    for line in data:
        if "class=\"tag\" href=" in line:
            genre = line.split("/tag/")[1].split("?")[0]
            LOGGER.debug("Found Genre: %s", genre)
            genrelist.add(genre)
    return genrelist


def parse_downloadable_tracks(data):
    """ parses songs from album page """
    for line in data:
        if "data-tralbum=\"" in line:
            unescaped_line = unescape(line.split("data-tralbum=\"")[1].split("\"")[0])
            content = json.loads(unescaped_line)

    tracklist = [[track['title'], track["file"]["mp3-128"]] for track in content["trackinfo"]]
    return tracklist
