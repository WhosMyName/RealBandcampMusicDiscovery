import requests
import threading
import multiprocessing
from time import sleep
import logging
import sys

from htmlparser import HTMLParser
from messages import *

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
def uncaught_exceptions(type, value, tb):
    LOGGER.exception("Uncaught Exception of type %s was caught: %s\nTraceback:\n%s" % (type, value, tb))
sys.excepthook = uncaught_exceptions

#class Connector(threading.Thread):
class Connector(multiprocessing.Process):

    def __init__(self, queue):
        #threading.Thread.__init__(self)
        multiprocessing.Process.__init__(self)
        self.queue = queue

        self.getTagsEvent = multiprocessing.Event()
        self.getAlbumsEvent = multiprocessing.Event()
        self.tagsReadyEvent = multiprocessing.Event()
        self.albumsReadyEvent = multiprocessing.Event()
        self.getFetchTagsFromQ = multiprocessing.Event()
        self.pauseFetch = multiprocessing.Event()
        self.pauseFetch.clear()
        self.tagsReadyEvent.clear()
        self.getTagsEvent.set()

        self.taglist = set()
        self.stop = multiprocessing.Event()
        self.session = requests.Session()
        self.parser = HTMLParser()
        self.apiurl = "https://bandcamp.com/tag/%s?page=%s" # tag, pagenum
        LOGGER.debug("Initialized %s" % self)


    def __del__(self):
        self.parser.__del__()
        self.stop.set()


    def get_tags(self):
        LOGGER.info("Obtaining Tags")
        resp = self.session.get("https://bandcamp.com/tags")
        #LOGGER.debug(resp.content.decode("utf-8"))
        tags = self.parser.parse_tags(resp.content.decode("utf-8").split("\n"))
        for tag in tags:
            self.queue.put(tag)
            #LOGGER.debug("Put %s in Q" % tag)
        self.tagsReadyEvent.set()


    def getTagsFromQ(self):
        self.getFetchTagsFromQ.clear()
        while not self.queue.empty():
            self.taglist.add(self.queue.get())
        LOGGER.info("got tags from Q %s" % self.taglist)
        self.getAlbumsEvent.set()


    def get_albums(self):
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
                    self.queue.put({tag: albums})
                    self.albumsReadyEvent.set()
                    LOGGER.info(self.albumsReadyEvent.is_set())
                    LOGGER.debug("%s" % albums)
                else:
                    sleep(2)
                    self.albumsReadyEvent.clear()
                    return None
        sleep(2)
        self.albumsReadyEvent.clear()


    def update_album_metadata(self, album):#get pictures too
        LOGGER.debug("Updating Tags for %s" % album.name)
        resp = self.session.get(album.url)
        album.genre = self.parser.parse_album_genres(resp.content.decode("utf-8").split("\n"))
        return album


    def send(self, msg):
        self.queue.put(msg)


    def recieve(self):
        if not self.queue.empty():
            msg = self.queue.get()
            if msg.sender == self.__name__:
                self.send(msg)
                return None
            return msg


    def analyze(self, msg):
        if isinstance(msg, MsgGetTags):
            #set event for tags
        elif isinstance(msg, MsgPutFetchTags):
            #set event for albums
        else:
            LOGGER.error("Unknown Message:\n%s" % msg)



    def run(self):
        while True: # event
            self.analyze(self.recieve())
            sleep(0.5)


def __main__():
    conn = Connector()
    conn.start()
    #conn.get_tags()
    conn.get_albums(print, "rock")
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
