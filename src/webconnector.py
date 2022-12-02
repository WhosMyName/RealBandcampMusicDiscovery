""" request beast, parsing monster, a core at it's best """
import multiprocessing
from time import sleep
import logging
import sys
import concurrent.futures as cf
import os
#import sqlite3

import requests

from album import Album
from messagehandler import MessageHandler
from htmlparser import parse_album_metadata, parse_albums, parse_maxpages, parse_tags, parse_downloadable_tracks
from messages import MsgGetTags, MsgPutAlbums, MsgPutFetchTags, MsgPutTags, MsgDownloadAlbums, MsgFinishedDownloads, MsgPause, MsgQuit

from os import name as os_name

if os_name == "nt":
    SLASH = "\\"
else:
    SLASH = "/"

CWD = os.path.dirname(os.path.realpath(__file__)) + SLASH
DOWNLOADLOCATION = CWD + ".." + SLASH + "Albums" + SLASH

LOGGER = logging.getLogger('rbmd.webconnector')
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
    LOGGER.exception("Uncaught Exception of type %s was caught: %s\nTraceback:\n%s",
                     exc_type, exc_val, traceback.print_tb(exc_trace))
    try:
        del exc_type, exc_val, exc_trace
    except Exception as excp:
        LOGGER.exception("Exception caught during tb arg deletion:\n%s", excp)


sys.excepthook = uncaught_exceptions


class Connector(multiprocessing.Process):
    """ Connector Class """

    # pylint: disable=too-many-instance-attributes

    def __init__(self, connectionParams: dict):
        """ init init init """
        multiprocessing.Process.__init__(self)
        self.executor = None
        self.messagehandler = None
        self.connectionParams = connectionParams

        self.get_genres_event = multiprocessing.Event()
        self.get_albums_event = multiprocessing.Event()
        self.pause_fetch = multiprocessing.Event()
        self.pause_fetch.clear()

        self.taglist = set()
        self.stop: bool = False
        self.session: requests.Session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0 (Android 12; Mobile; rv:97.0) Gecko/97.0 Firefox/97.0",})
        self.apiurl: str = "https://bandcamp.com/tag/%s?page=%s"  # tag, pagenum
        self.start()

    def __del__(self):
        """ delet dis """
        if self.messagehandler:
            self.messagehandler.__del__()
        if self.executor:
            self.executor.shutdown()
        self.stop = True

    def download_file(self, srcfile, srcurl):
        """Function to Downloadad and verify downloaded Files"""
        if not os.path.isfile(srcfile):
            LOGGER.debug("Downloading %s as %s", srcurl, srcfile)
            with open(srcfile, "wb") as fifo:#open in binary write mode
                response = self.session.get(srcurl)#get request
                fifo.write(response.content)#write to file

    def get_genres(self):
        """ func to request + parse bandcamps default tags """
        self.get_genres_event.clear()
        LOGGER.info("Obtaining Tags")
        resp = self.session.get("https://bandcamp.com/tags")
        LOGGER.debug(resp.text)
        tags = parse_tags(resp.text.split("\n"))
        self.messagehandler.send(MsgPutTags(data=tags))
        LOGGER.info("Msg sent")

    def get_fetch_tags(self, msg):
        """ updates the list of tags that need to be fetched during current/next iteration """
        self.taglist = set(msg.data)
        LOGGER.info("got tags from Msg %s", self.taglist)
        self.get_albums_event.set()

    def get_albums(self):
        """ func grabs albums based on fetch-tags, parses and adds sprinkles of metadata on them """
        LOGGER.info("Getting Albums for Tags: %s", self.taglist)
        self.get_albums_event.clear()
        for tag in self.taglist:
            # check albums from db
            resp1 = self.session.get(self.apiurl % (tag, "0"))
            maxpages = parse_maxpages(
                resp1.text.split("\n"))
            for num in range(1, maxpages+1):
                if not self.pause_fetch.is_set():
                    resp2 = self.session.get(self.apiurl % (tag, num))
                    albums = parse_albums(
                        resp2.text.split("\n"))
                    future_metadata = {self.executor.submit(
                        self.update_album_metadata, album): album for album in albums}
                    for future in cf.as_completed(future_metadata):
                        supposed_album = future_metadata[future]
                        try:
                            future.result()
                        except Exception as excp:
                            LOGGER.exception(
                                "%s has thrown Exception:\n%s", supposed_album, excp)
                    albumdata = {tag: albums}
                    self.messagehandler.send(MsgPutAlbums(data=albumdata))
                    LOGGER.debug("%s", albums)
                    # add albums to db
                else:
                    sleep(2)
                    return None
        return None

    def update_album_metadata(self, album: Album):  # get pictures too
        """ func that grabs+parses album metadata """
        LOGGER.debug("Updating Tags for %s", album.name)
        resp = self.session.get(album.url)
        album.genre = parse_album_metadata(
            resp.text.split("\n"))
        resp2 = self.session.get(album.cover_url)
        album.cover = resp2.content
        return album

    #def add_album_to_db(self, album):
    #    """ func to smartly insert new albums into db """
    #    pass

    def download_albums(self, msg):
        """ downloads all albums from message """
        albumlist = msg.get_data()
        for album in albumlist:
            location = DOWNLOADLOCATION + album.__str__() + SLASH
            if not os.path.exists(location):
                os.makedirs(location)
            resp = self.session.get(album.url)
            tracklist = parse_downloadable_tracks(resp.text.split("\n"))
            for track in tracklist:
                self.download_file(f"{location}{track[0]}.mp3", track[1])
            if album.cover["data"]:
                with open(f"{location}cover.jpg", "w+b") as cover:
                    album.cover["data"].seek(0)
                    cover.write(album.cover["data"].read())
        self.messagehandler.send(MsgFinishedDownloads(None))


    def analyze(self, msg):
        """ generic "callback" to check msgs and set flags and call functions """
        if msg is not None:
            if isinstance(msg, MsgGetTags):
                self.get_genres_event.set()
            elif isinstance(msg, MsgPutFetchTags):
                self.get_fetch_tags(msg)
            elif isinstance(msg, MsgDownloadAlbums):
                self.download_albums(msg)
            elif isinstance(msg, MsgQuit):
                self.__del__()
            elif isinstance(msg, MsgPause):
                self.pause_fetch.set()
            else:
                LOGGER.error("Unknown Message:\n%s", msg)

    def run(self):
        """ RUN! """
        # little hack the avoids pickling a queue when forking ;)
        self.executor: cf.ThreadPoolExecutor = cf.ThreadPoolExecutor(max_workers=15)
        self.messagehandler = MessageHandler(self.connectionParams, isClient=True)
        LOGGER.info(f"Creating handler {self.messagehandler}")
        while not self.stop:
            self.analyze(self.messagehandler.recieve())
            if self.get_genres_event.is_set():
                self.get_genres()
            elif self.get_albums_event.is_set():
                self.get_albums()
            sleep(0.1)


def __main__():
    """ basic testing main func """
    conn = Connector()
    # conn.start()
    #conn.get_genres()
    conn.taglist.add("metal")
    conn.get_albums()
    conn.__del__()


if __name__ == "__main__":
    __main__()
