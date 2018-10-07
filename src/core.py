import logging
import sys
import threading
import time
from webconnector import Connector

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
    def __init__(self):
        threading.Thread.__init__(self)
        self.stop = threading.Event()
        self.connector = Connector()
        self.connector.start()
        LOGGER.debug("Initialized %s" % self)

    def __del__(self):
        self.connector.__del__()
        self.stop.set()

    def run(self):
        while not self.stop.is_set():
            time.sleep(0.1)

    def refresh(self, func, taglist):
        #albumlist = set()
        for tag in taglist:
            self.connector.get_albums(func, tag)
        #        albumlist.add(album)
        #return albumlist

    def get_genres(self):
        return self.connector.get_tags()

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

        

    