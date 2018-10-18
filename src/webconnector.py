import requests
import threading
import multiprocessing
from time import sleep
import logging
import sys
#from album import Album
from htmlparser import HTMLParser

LOG_FORMAT = '%(asctime)-15s | %(module)s %(name)s %(process)d %(thread)d | %(funcName)20s() - Line %(lineno)d | %(levelname)s | %(message)s'
LOGGER = logging.getLogger('rbmd.webconnector')
LOGGER.setLevel(logging.DEBUG)
strmhdlr = logging.StreamHandler(sys.stdout)
strmhdlr.setLevel(logging.INFO)
strmhdlr.setFormatter(logging.Formatter(LOG_FORMAT))
flhdlr = logging.FileHandler("../logs/error.log", mode='a', encoding="utf-8", delay=False)
flhdlr.setLevel(logging.DEBUG)
flhdlr.setFormatter(logging.Formatter(LOG_FORMAT))
LOGGER.addHandler(strmhdlr)
LOGGER.addHandler(flhdlr)

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
        self.getTagsEvent.set()

        self.taglist = set()
        self.stop = multiprocessing.Event()
        self.session = requests.Session()
        self.parser = HTMLParser()
        self.parser.start()
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
            LOGGER.debug("Put %s in Q" % tag)
        self.tagsReadyEvent.set()
        LOGGER.warning("Putting Tags")
        #return self.parser.parse_tags(resp.content.decode("utf-8").split("\n"))


    def getTagsFromQ(self):
        while not self.queue.empty():
            self.queue.g


    def get_albums(self):
        self.get.clear()
        LOGGER.info("Getting Albums for Tags: %s with CallBack %s" % (self.taglist, self.fnc))
        if len(self.taglist) is not 0:
            for tag in self.taglist:
                resp1 = self.session.get(self.apiurl % (tag, "0"))
                maxpages = self.parser.parse_maxpages(resp1.content.decode("utf-8").split("\n"))
                for num in range(1, maxpages+1):
                    resp2 = self.session.get(self.apiurl % (tag, num))
                    albums = self.parser.parse_albums(resp2.content.decode("utf-8").split("\n"))
                    for album in albums:
                        album = self.update_album_genre(album)
                        #LOGGER.debug("%r" % albums)
                    self.fnc(albums)
        else:
            LOGGER.error("Missing Tags, can't obtain Albums")
                    

    def update_album_genre(self, album):#switch to metadata and get pictures too
        LOGGER.debug("Updating Tags for %s" % album.name)
        resp = self.session.get(album.url)
        album.genre = self.parser.parse_album_genres(resp.content.decode("utf-8").split("\n"))
        return album


    def get_album_cover(self, album):
        #get
        #parse
        #dl
        #return
        pass


    def run(self):

        if self.getTagsEvent.is_set():
            self.get_tags()

        while not self.stop.is_set():
            #if self.
            if self.getAlbumsEvent.is_set():
                self.get_albums()
            sleep(0.1)


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
