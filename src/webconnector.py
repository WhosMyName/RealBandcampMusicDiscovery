""" request beast, parsing monster, a core at it's best """
from multiprocessing import Event, Process
from threading import Thread
from time import sleep
import logging
import sys
import concurrent.futures as cf
import os
#import sqlite3

import requests

from messagehandler import MessageHandler
from htmlparser import parse_album_metadata, parse_albums, parse_maxpages, parse_tags, parse_downloadable_tracks
from messages import MsgGetTags, MsgPutAlbums, MsgPutFetchTags, MsgPutTags, MsgDownloadAlbums, MsgFinishedDownloads, MsgPause, MsgQuit

if os.name == "nt":
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
FLHDLR = logging.FileHandler(
    "../logs/error.log", mode="a", encoding="utf-8", delay=False)
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


class Connector(Process, MessageHandler):
    """ Connector Class """

    # pylint: disable=too-many-instance-attributes

    def __init__(self, queue=None):
        """ init init init """
        Process.__init__(self)
        MessageHandler.__init__(self, queue)

        #self.sync_thread = Thread(target=self.analyze, args=(self.recieve, )) #nope why??
        #self.sync_thread.start()

        self.worker_executor = cf.ThreadPoolExecutor(max_workers=5, thread_name_prefix="func_worker")
        self.fetcher_executor = cf.ThreadPoolExecutor(max_workers=20, thread_name_prefix="requester")

        self.get_genres_event = Event()
        self.get_albums_event = Event()
        self.tags_ready_event = Event()
        self.albums_ready_event = Event()
        self.get_fetchtags_from_q = Event()
        self.pause_fetch = Event()
        self.stop = Event()

        self.pause_fetch.clear()
        self.tags_ready_event.clear()

        self.threadlist = []

        self.taglist = set()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0 (Linux; Android 7.0; PLUS Build/NRD90M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.98 Mobile Safari/537.36",})
        adapter = requests.adapters.HTTPAdapter(pool_connections=15, pool_maxsize=25,max_retries=3)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.apiurl = "https://bandcamp.com/tag/%s?page=%s"  # tag, pagenum
        self.start()
        LOGGER.debug("Initialized %s", self)

    def __del__(self):
        """ delet dis """
        self.pause_fetch.set()
        self.stop.set()
        #self.sync_thread.join()
        MessageHandler.__del__(self)
        self.fetcher_executor.shutdown()
        self.worker_executor.shutdown()

    def download_file(self, srcfile, srcurl):
        """Function to Downloadad and verify downloaded Files"""
        if not os.path.isfile(srcfile):
            LOGGER.debug("Downloading %s as %s", srcurl, srcfile)
            with open(srcfile, "wb") as fifo:#open in binary write mode
                response = self.session.get(srcurl)#get request
                fifo.write(response.content)#write to file

    def get_genres(self):
        """ func to request + parse bandcamps default tags """
        LOGGER.info("Obtaining Tags")
        resp = self.session.get("https://bandcamp.com/tags")
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
        for tag in self.taglist: # thread for each tag to grab????
            if self.pause_fetch.is_set():
                LOGGER.debug("Quiting worker")
                return None
            # check albums from db
            resp1 = self.session.get(self.apiurl % (tag, "0"))
            maxpages = parse_maxpages(
                resp1.content.decode("utf-8").split("\n"))
            for num in range(1, maxpages+1):
                resp2 = self.session.get(self.apiurl % (tag, num))
                albums = parse_albums(
                    resp2.content.decode("utf-8").split("\n"))
                future_metadata = {self.fetcher_executor.submit(
                        self.update_album_metadata, album): album for album in albums}
                for future in cf.as_completed(future_metadata):
                    if self.pause_fetch.is_set():
                        for future in future_metadata:
                            future.cancel()
                            LOGGER.debug("Quiting worker")
                        return None
                    supposed_album = future_metadata[future]
                    LOGGER.debug("Supposed Album:\t%s", supposed_album)
                    try:
                        album = future.result()
                    except Exception as excp:
                        LOGGER.exception(
                            "%s has thrown Exception:\n%s", supposed_album, excp)
                albumdata = {tag: albums}
                LOGGER.debug("Sending albums")
                self.send(MsgPutAlbums(data=albumdata))
                #LOGGER.debug("%s", albums)
                    # add albums to db
        return None

    def update_album_metadata(self, album):
        """ func that grabs+parses album metadata """
        LOGGER.debug("Updating Tags for %s", album.name)
        resp = self.session.get(album.url)
        album.genre = parse_album_metadata(
            resp.content.decode("utf-8").split("\n"))
        resp2 = self.session.get(album.cover)
        album.cover = resp2.content
        return album

    def add_album_to_db(self, album):
        """ func to smartly insert new albums into db """

    def download_albums(self, msg):
        """ downloads all albums from message """
        albumlist = msg.get_data()
        for album in albumlist:
            location = DOWNLOADLOCATION + album.__str__() + SLASH
            if not os.path.exists(location):
                os.makedirs(location)
            resp = self.session.get(album.url)
            tracklist = parse_downloadable_tracks(resp.content.decode("utf-8").split("\n"))
            for track in tracklist:
                self.download_file(location+track[0], track[1])
        self.send(MsgFinishedDownloads(None))


    def analyze(self, msg):
        """ generic "callback" to check msgs and set flags and call functions """
        if msg != None:
            if isinstance(msg, MsgGetTags):
                self.get_genres_event.set()
            elif isinstance(msg, MsgPutFetchTags):
                self.get_fetch_tags(msg)
            elif isinstance(msg, MsgDownloadAlbums):
                self.download_albums(msg)
            elif isinstance(msg, MsgPause):
                self.pause_fetch.set()
                LOGGER.debug("SET PAUSE FLAG")
            elif isinstance(msg, MsgQuit):
                self.__del__()
            else:
                LOGGER.error("Unknown Message:\n%s", msg)

    def run(self):
        """ RUN! """
        while not self.stop.is_set():
            self.analyze(self.recieve())
            if self.get_genres_event.is_set():
                self.get_genres_event.clear()
                t1 = self.worker_executor.submit(self.get_genres)
                self.threadlist.append(["worker", t1])
            elif self.get_albums_event.is_set():
                self.get_albums_event.clear()
                t1 = self.worker_executor.submit(self.get_albums)
                self.threadlist.append(["worker", t1])
            elif self.pause_fetch.is_set(): # critical aborts @anytime #truestorybro/sis
                LOGGER.debug("PAUSING FETCH")
            if len(self.threadlist) > 0:
                #print(self.threadlist)
                for thread in self.threadlist:
                    if thread[1].done():
                        self.threadlist.remove(thread)
            else:
                self.pause_fetch.clear()
            sleep(0.1)


def __main__():
    """ basic testing main func """
    conn = Connector()
    conn.queue.put(MsgGetTags(None))
    conn.queue.put(MsgPutFetchTags(["metal"]))
    sleep(60)
    conn.queue.put(MsgQuit(None))


if __name__ == "__main__":
    __main__()
