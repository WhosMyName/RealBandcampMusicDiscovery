import requests
import threading
import multiprocessing
from time import sleep
import logging
import sys

from htmlparser import HTMLParser
from messages import *
from messagehandler import MessageHandler

LOG_FORMAT = '%(asctime)-15s | %(module)s %(name)s %(process)d %(thread)d | %(funcName)20s() - Line %(lineno)d | %(levelname)s | %(message)s'
LOGGER = logging.getLogger('rbmd.webconnector')
LOGGER.setLevel(logging.DEBUG)
strmhdlr = logging.StreamHandler(sys.stdout)
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


class Connector(multiprocessing.Process, MessageHandler):

    def __init__(self, queue):
        #threading.Thread.__init__(self)
        multiprocessing.Process.__init__(self)
        MessageHandler.__init__(self)
        self.queue = queue

        self.getGenresEvent = multiprocessing.Event()
        self.getAlbumsEvent = multiprocessing.Event()
        self.tagsReadyEvent = multiprocessing.Event()
        self.albumsReadyEvent = multiprocessing.Event()
        self.getFetchTagsFromQ = multiprocessing.Event()
        self.pauseFetch = multiprocessing.Event()
        self.pauseFetch.clear()
        self.tagsReadyEvent.clear()
        #self.getGenresEvent.set()

        self.taglist = set()
        self.stop = multiprocessing.Event()
        self.session = requests.Session()
        self.parser = HTMLParser()
        self.apiurl = "https://bandcamp.com/tag/%s?page=%s" # tag, pagenum
        self.start()
        LOGGER.debug("Initialized %s" % self)


    def __del__(self):
        MessageHandler.__del__(self)
        self.parser.__del__()
        self.stop.set()


    def getGenres(self):
        self.getGenresEvent.clear()
        LOGGER.info("Obtaining Tags")
        resp = self.session.get("https://bandcamp.com/tags")
        #LOGGER.debug(resp.content.decode("utf-8"))
        tags = self.parser.parse_tags(resp.content.decode("utf-8").split("\n"))
        self.send(MsgPutTags(self.__class__.__name__, data=tags))
        LOGGER.info("Msg sent")


    def getFetchTags(self, msg):
        fetchTags = msg.data
        for tag in fetchTags:
            self.taglist.add(tag)
        LOGGER.info("got tags from Msg %s" % self.taglist)
        self.getAlbumsEvent.set()


    def getAlbums(self):
        LOGGER.info("Getting Albums for Tags: %s" % self.taglist)
        self.getAlbumsEvent.clear()
        for tag in self.taglist:
            resp1 = self.session.get(self.apiurl % (tag, "0"))
            maxpages = self.parser.parse_maxpages(resp1.content.decode("utf-8").split("\n"))
            for num in range(1, 2):#maxpages+1):
                if not self.pauseFetch.is_set():
                    resp2 = self.session.get(self.apiurl % (tag, num))
                    albums = self.parser.parse_albums(resp2.content.decode("utf-8").split("\n"))
                    for album in albums:
                        album.genre = tag #self.update_album_metadata(album)
                    albumdata = {tag: albums}
                    self.send(MsgPutAlbums(self.__class__.__name__, data=albumdata))
                    LOGGER.debug("%s" % albums)
                else:
                    sleep(2)
                    return None


    def update_album_metadata(self, album):#get pictures too
        LOGGER.debug("Updating Tags for %s" % album.name)
        resp = self.session.get(album.url)
        album.genre = self.parser.parse_album_metadata(resp.content.decode("utf-8").split("\n"))
        return album


    def analyze(self, msg): # WIP
        if msg is not None:
            LOGGER.info("Received Msg: %s in Q: %s" % (msg, self.queue))
            if isinstance(msg, MsgGetTags):
                self.getGenresEvent.set()
            elif isinstance(msg, MsgPutFetchTags):
                self.getFetchTags(msg)
            else:
                LOGGER.error("Unknown Message:\n%s" % msg)


    def run(self):
        while not self.stop.is_set(): # event
            self.analyze(self.recieve())
            if self.getGenresEvent.is_set():
                self.getGenres()
            elif self.getAlbumsEvent.is_set():
                self.getAlbums()

            sleep(0.5)


def __main__():
    conn = Connector()
    conn.start()
    #conn.getGenres()
    conn.getAlbums(print, "rock")
    conn.__del__()

if __name__ == "__main__":
    __main__()  

#############################################################
        #for timeframe in timeframes:
        #    for recomm in recommlvl:
        #        LOGGER.info("Getting MaxPages for %s" % self.apiurl % (tag, recomm, "0", timeframe))
        #        LOGGER.debug("MaxPages for %s is %s" % (self.apiurl, maxpages) % (tag, recomm, "0", timeframe))
        #        for pagenum in range(0, 1): #maxpages):
        #            LOGGER.debug("Getting data from %s" % self.apiurl % (tag, recomm, pagenum, timeframe))
        #            resp2 = self.session.get(self.apiurl % (tag, recomm, pagenum, timeframe))
        #            albums = self.parser.parse_albums(resp2.json())
        #            for album in albums:
        #                album = self.update_album_genre(album)
