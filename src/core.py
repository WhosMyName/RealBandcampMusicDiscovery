import logging
import sys
import threading
import time
#from webconnector import Connector

LOG_FORMAT = '%(asctime)-15s | %(module)s %(name)s %(process)d %(thread)d | %(funcName)20s() - Line %(lineno)d | %(levelname)s | %(message)s'
LOGGER = logging.getLogger('rbmd.core')
LOGGER.setLevel(logging.DEBUG)
strmhdlr = logging.StreamHandler(sys.stdout)
strmhdlr.setLevel(logging.INFO)
strmhdlr.setFormatter(logging.Formatter(LOG_FORMAT))
flhdlr = logging.FileHandler("../logs/error.log", mode='a', encoding="utf-8", delay=False)
flhdlr.setLevel(logging.DEBUG)
flhdlr.setFormatter(logging.Formatter(LOG_FORMAT))
LOGGER.addHandler(strmhdlr)
LOGGER.addHandler(flhdlr)

class Core(threading.Thread):

    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue
        self.tags = set()
        self.stop = threading.Event()
        self.fetchTagsEvent = threading.Event()
        self.fetchAlbumEvent = threading.Event()
        self.fetchTagsEvent.clear()
        self.fetchAlbumEvent.clear()
        ##self.connector = Connector()
        ##self.connector.start()
        LOGGER.debug("Initialized %s" % self)


    def __del__(self):
        #self.connector.__del__()
        self.stop.set()


    def run(self):
        LOGGER.debug("Started run for %s" % self)
        while not self.stop.is_set():
            if self.fetchTagsEvent.is_set():
                if self.getTagsFromQ():
                    self.fetchTagsEvent.clear()
                    LOGGER.info("Got tags from queueueue")
            
            time.sleep(0.1)


    def getTagsFromQ(self):
        if not self.queue.empty():
            while not self.queue.empty():
                self.tags.add(self.queue.get())
            #LOGGER.debug(self.tags)
            return True
        else:
            return False


    def refresh(self, func, taglist):
        LOGGER.error("FNC: %s Tags: %s" % (taglist, func))
        #self.connector.set_taglist(taglist)
        #self.connector.set_fnc(func)
        #self.connector.get.set()
        #        albumlist.add(album)
        #return albumlist


    def get_genres(self):
        self.fetchTagsEvent.set()
        #return #self.connector.get_tags()


    def compare(self, taglist, albumlist):
        LOGGER.info("Comparing for tags: %r" % taglist)
        compareset = set()
        #taglist = set(taglist)
        dt = time.time()
        for album in albumlist:
            LOGGER.debug("%s - %s [%r]" % (album.name, album.genre, taglist))
            if taglist.issubset(album.genre):
                compareset.add(album)
                LOGGER.debug("Added %s after comparison" % album.name)
        dt1 = time.time()
        LOGGER.debug("Time spent comparing: %s" % (dt1-dt))
        return compareset

        
    def returnTags(self):
        if len(self.tags) > 0:
            return self.tags
        return None


def __main__():
    pass
    #alb = Album("GenericALbum.exe", {"nogenre", "gitgud"}, "https://github.com/whosmyname", "datboigud", "https://i.pinimg.com/originals/5e/40/5b/5e405be0320863d04c84b399dc2969ca.jpg")
    #LOGGER.info(alb)

if __name__ == "__main__":
    __main__()