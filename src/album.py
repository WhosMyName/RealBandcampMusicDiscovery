"""defcdw"""

import sys
import logging
from tags import Tag

LOG_FORMAT = '%(asctime)-15s | %(module)s %(name)s %(process)d %(thread)d | %(funcName)20s() - Line %(lineno)d | %(levelname)s | %(message)s'
logging.basicConfig(format=LOG_FORMAT, level=logging.DEBUG, filename="../logs/error.log")
strmhdlr = logging.StreamHandler(sys.stdout)
strmhdlr.setLevel(logging.INFO)
strmhdlr.setFormatter(logging.Formatter(LOG_FORMAT))
LOGGER = logging.getLogger('rbmd.htmlparser')
LOGGER.addHandler(strmhdlr)


class Album():
    def __init__(self, name, url, band, cover_url):
        self.name = name
        self.genre = set()
        self.url = url
        self.band = band
        self.cover_url = cover_url

    def __repr__(self):
        return "%s - %s" % (self.__class__, str(self.__dict__))

def __main__():
    alb = Album("GenericALbum.exe", {"nogenre", "gitgud"}, "https://github.com/whosmyname", "datboigud", "https://i.pinimg.com/originals/5e/40/5b/5e405be0320863d04c84b399dc2969ca.jpg")
    LOGGER.info(alb)

if __name__ == "__main__":
    __main__()