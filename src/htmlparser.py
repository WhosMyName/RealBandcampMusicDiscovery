""" utils to allow easy parsing in seperate thread(s) """

import json
from html import unescape
from re import sub as re_sub

from album import Album
from helpers import safety_wrapper, HLogger, DANGER_CHARS

LOGGER = HLogger(name="rbmd.htmlparser")

@safety_wrapper
def parse_tags(data):
    """ simple func for parsing bandcamps "default" tags """
    LOGGER.debug("Parsing Tags")
    tagset: set = set() # create our storage [set becuase we don't want any duplicates]
    for line in data:
        if "class=\"tag size" in line:
            tag: str = line.split("/tag/")[1].split("\" ")[0]
            #LOGGER.debug(f"Found Tag: {tag}")
            if tag != "": # check if parsed correctly and not empty
                tagset.add(tag)
    taglist: list = sorted(tagset) # sort the set and return as list
    taglist.insert(0, "None") # add removal value as first value
    return taglist

@safety_wrapper
def parse_albums(data):
    """ func that does the basic album parsing"""
    LOGGER.debug("Parsing Albums")
    albumset: set = set() 
    albool: bool = False

    # define vars for albums data
    name: str = ""
    url: str = ""
    band: str = ""
    cover_url: str = ""

    for line in data:
        if "item_list" in line and not albool: # check if we're in the range of parsable albums
            albool = True
        elif "<a href=" in line and albool:
            url = line.split("<a href=\"")[1].split("\" title")[0] # parse albums url
            name = line.split("title=\"")[1].split("\">")[0] # parse albums name
            if " by " in name: # modify the naming as we don't need XXX by XZY album names
                name = name.split(" by ")[0]
        elif "<img class=\"art" in line and albool:
            cover_url = line.split("src=\"")[1].split("\" alt")[0] # parse the cover url
        elif "<div class=\"itemsubtext" in line and albool:
            band = unescape(line.split("\">")[1].split("</")[0]) # parse the interprets name
            alb = Album(name, url, band, cover_url) # create the album object
            #LOGGER.debug(alb)
            albumset.add(alb) # add allbum to list
        elif "<div class=\"pager_" in line: # reset parsing check bool
            albool = False
    LOGGER.debug("returning to connector")
    return albumset

@safety_wrapper
def parse_maxpages(data):
    """ helper function for maxpages (esp. usefull for tag/genre pages /w < 10 maxpages) """
    LOGGER.debug("Getting Maxpages")
    maxpages = 0
    for line in data:
        if "pagenum round4" in line:
            page = int(line.split("\">")[1].split("</a>")[0])
            if page > maxpages:
                maxpages = page
    LOGGER.debug(f"Maxpages: {maxpages}")
    return maxpages

@safety_wrapper
def parse_album_metadata(data): #grab all metadata
    """ parsing metadata (tags, urls, covers, etc...) """
    LOGGER.debug("Parsing Tags")
    genrelist = set()
    for line in data:
        if "class=\"tag\" href=" in line:
            genre = line.split("/tag/")[1].split("?")[0]
            LOGGER.debug(f"Found Genre: {genre}")
            genrelist.add(genre)
    return genrelist

@safety_wrapper
def parse_downloadable_tracks(data):
    """ parses songs from album page """
    content = None
    for line in data:
        if "data-tralbum=\"" in line:
            unescaped_line = unescape(line.split("data-tralbum=\"")[1].split("\"")[0])
            content = json.loads(unescaped_line)
    if content and "trackinfo" in content.keys():
        tracklist = [[re_sub(DANGER_CHARS, "_", track['title']), track["file"]["mp3-128"]] for track in content["trackinfo"]]
        return tracklist
    return []
