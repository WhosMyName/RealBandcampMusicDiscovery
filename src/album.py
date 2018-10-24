""" generic class to hold allalbum related data """

import sys
import logging

LOG_FORMAT = '%(asctime)-15s | %(module)s %(name)s %(process)d %(thread)d | %(funcName)20s() - Line %(lineno)d | %(levelname)s | %(message)s'
LOGGER = logging.getLogger('rbmd.album')
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