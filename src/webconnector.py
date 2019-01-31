""" request beast, parsing monster, a core at it's best """
import multiprocessing
from time import sleep
import logging
import sys
import concurrent.futures as cf

import requests

from messagehandler import MessageHandler
from htmlparser import parse_album_metadata, parse_albums, parse_maxpages, parse_tags
from messages import MsgGetTags, MsgPutAlbums, MsgPutFetchTags, MsgPutTags, MsgStop

LOGGER = logging.getLogger('rbmd.webconnector')
LOG_FORMAT = "%(asctime)-15s | %(levelname)s | %(module)s %(name)s %(process)d %(thread)d | %(funcName)20s() - Line %(lineno)d | %(message)s"
LOGGER.setLevel(logging.DEBUG)
STRMHDLR = logging.StreamHandler(stream=sys.stdout)
STRMHDLR.setLevel(logging.INFO)
STRMHDLR.setFormatter(logging.Formatter(LOG_FORMAT))
FLHDLR = logging.FileHandler("../logs/error.log", mode="a", encoding="utf-8", delay=False)
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


class Connector(multiprocessing.Process, MessageHandler):
    """ Connector Class """

    # pylint: disable=too-many-instance-attributes

    def __init__(self, queue=None):
        """ init init init """
        multiprocessing.Process.__init__(self)
        MessageHandler.__init__(self, queue)

        self.executor = cf.ThreadPoolExecutor(max_workers=15)

        self.get_genres_event = multiprocessing.Event()
        self.get_albums_event = multiprocessing.Event()
        self.tags_ready_event = multiprocessing.Event()
        self.albums_ready_event = multiprocessing.Event()
        self.get_fetchtags_from_q = multiprocessing.Event()
        self.pause_fetch = multiprocessing.Event()
        self.pause_fetch.clear()
        self.tags_ready_event.clear()

        self.taglist = set()
        self.stop = multiprocessing.Event()
        self.session = requests.Session()
        self.apiurl = "https://bandcamp.com/tag/%s?page=%s" # tag, pagenum
        self.start()
        LOGGER.debug("Initialized %s", self)


    def __del__(self):
        """ delet dis """
        MessageHandler.__del__(self)
        self.stop.set()
        self.executor.shutdown()


    def get_genres(self):
        """ func to request + parse bandcamps default tags """
        self.get_genres_event.clear()
        LOGGER.info("Obtaining Tags")
        resp = self.session.get("https://bandcamp.com/tags")
        #LOGGER.debug(resp.content.decode("utf-8"))
        tags = parse_tags(resp.content.decode("utf-8").split("\n"))
        self.send(MsgPutTags(data=tags))
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
            resp1 = self.session.get(self.apiurl % (tag, "0"))
            maxpages = parse_maxpages(resp1.content.decode("utf-8").split("\n"))
            for num in range(1, maxpages+1):
                if not self.pause_fetch.is_set():
                    resp2 = self.session.get(self.apiurl % (tag, num))
                    albums = parse_albums(resp2.content.decode("utf-8").split("\n"))
                    future_metadata = {self.executor.submit(self.update_album_metadata, album): album for album in albums}
                    for future in cf.as_completed(future_metadata):
                        supposed_album = future_metadata[future]
                        try:
                            album = future.result()
                        except Exception as excp:
                            LOGGER.exception("%s has thrown Exception:\n%s", supposed_album, excp)
                    albumdata = {tag: albums}
                    self.send(MsgPutAlbums(data=albumdata))
                    LOGGER.debug("%s", albums)
                else:
                    sleep(2)
                    return None
        return None


    def update_album_metadata(self, album):#get pictures too
        """ func that grabs+parses album metadata """
        LOGGER.debug("Updating Tags for %s", album.name)
        resp = self.session.get(album.url)
        album.genre = parse_album_metadata(resp.content.decode("utf-8").split("\n"))
        return album


    def analyze(self, msg):
        """ generic "callback" to check msgs and set flags and call functions """
        if msg is not None:
            LOGGER.info("Received Msg: %s in Q: %s", msg, self.queue)
            if isinstance(msg, MsgGetTags):
                self.get_genres_event.set()
            elif isinstance(msg, MsgPutFetchTags):
                self.get_fetch_tags(msg)
            elif isinstance(msg, MsgStop):
                self.__del__()
            else:
                LOGGER.error("Unknown Message:\n%s", msg)


    def run(self):
        """ RUN! """
        while not self.stop.is_set():
            self.analyze(self.recieve())
            if self.get_genres_event.is_set():
                self.get_genres()
            elif self.get_albums_event.is_set():
                self.get_albums()

            sleep(0.5)


def __main__():
    """ basic testing main func """
    conn = Connector()
    #conn.start()
    #conn.get_genres()
    conn.taglist.add("metal")
    conn.get_albums()
    conn.__del__()

if __name__ == "__main__":
    __main__()
