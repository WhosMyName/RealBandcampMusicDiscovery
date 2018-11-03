import multiprocessing
from time import sleep
import logging
import sys
import concurrent.futures as cf

import requests

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

    def __init__(self, queue=None):
        multiprocessing.Process.__init__(self)
        MessageHandler.__init__(self, queue)

        self.executor = cf.ThreadPoolExecutor(max_workers=15)

        self.getGenresEvent = multiprocessing.Event()
        self.getAlbumsEvent = multiprocessing.Event()
        self.tagsReadyEvent = multiprocessing.Event()
        self.albumsReadyEvent = multiprocessing.Event()
        self.getFetchTagsFromQ = multiprocessing.Event()
        self.pauseFetch = multiprocessing.Event()
        self.pauseFetch.clear()
        self.tagsReadyEvent.clear()

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
        self.executor.shutdown()


    def getGenres(self):
        self.getGenresEvent.clear()
        LOGGER.info("Obtaining Tags")
        resp = self.session.get("https://bandcamp.com/tags")
        #LOGGER.debug(resp.content.decode("utf-8"))
        tags = self.parser.parse_tags(resp.content.decode("utf-8").split("\n"))
        self.send(MsgPutTags(data=tags))
        LOGGER.info("Msg sent")


    def getFetchTags(self, msg):
        self.taglist = set(msg.data)
        LOGGER.info("got tags from Msg %s" % self.taglist)
        self.getAlbumsEvent.set()


    def getAlbums(self):
        LOGGER.info("Getting Albums for Tags: %s" % self.taglist)
        self.getAlbumsEvent.clear()
        for tag in self.taglist:
            resp1 = self.session.get(self.apiurl % (tag, "0"))
            maxpages = self.parser.parse_maxpages(resp1.content.decode("utf-8").split("\n"))
            for num in range(1, 6):#maxpages+1):
                if not self.pauseFetch.is_set():
                    resp2 = self.session.get(self.apiurl % (tag, num))
                    albums = self.parser.parse_albums(resp2.content.decode("utf-8").split("\n"))
                    future_metadata = {self.executor.submit(self.update_album_metadata, album): album for album in albums}
                    for future in cf.as_completed(future_metadata):
                        supposed_album = future_metadata[future]
                        try:
                            album = future.result()
                        except Exception as excp:
                            LOGGER.exception("%s has thrown Exception:\n%s" % (supposed_album, excp))
                    albumdata = {tag: albums}
                    self.send(MsgPutAlbums(data=albumdata))
                    LOGGER.debug("%s" % albums)
                else:
                    sleep(2)
                    return None


    def update_album_metadata(self, album):#get pictures too
        LOGGER.debug("Updating Tags for %s" % album.name)
        resp = self.session.get(album.url)
        album.genre = self.parser.parse_album_metadata(resp.content.decode("utf-8").split("\n"))
        return album


    def analyze(self, msg):
        if msg is not None:
            LOGGER.info("Received Msg: %s in Q: %s" % (msg, self.queue))
            if isinstance(msg, MsgGetTags):
                self.getGenresEvent.set()
            elif isinstance(msg, MsgPutFetchTags):
                self.getFetchTags(msg)
            else:
                LOGGER.error("Unknown Message:\n%s" % msg)


    def run(self):
        while not self.stop.is_set():
            self.analyze(self.recieve())
            if self.getGenresEvent.is_set():
                self.getGenres()
            elif self.getAlbumsEvent.is_set():
                self.getAlbums()

            sleep(0.5)


def __main__():
    conn = Connector()
    #conn.start()
    #conn.getGenres()
    conn.taglist.add("metal")
    conn.getAlbums()
    conn.__del__()

if __name__ == "__main__":
    __main__()  
