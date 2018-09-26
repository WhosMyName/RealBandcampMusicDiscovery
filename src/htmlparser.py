"""rewfew"""

import threading
import logging
from tags import Tag
from album import Album
import math

LOG_FORMAT = '%(asctime)-15s | %(module)s %(name)s %(process)d %(thread)d | %(funcName)20s() - Line %(lineno)d | %(levelname)s | %(message)s'
logging.basicConfig(format=LOG_FORMAT, level=logging.DEBUG)
LOGGER = logging.getLogger('rbmd.webconnector')

class HTMLParser(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.stop = threading.Event()
        LOGGER.debug("Initialized %s" % self)

    def parse_tags(self, data):
        LOGGER.info("Parsing Tags")
        with open("tags.html", "w") as tagfd:
            tagfd.write(data)
        #figure out how subtags work
        #taglist = []
        #for blub in data:
        #parse
        #create new Tag()
        pass
    
    def parse_albums(self, data):
        #with open("albums.html", "w") as albfd:
        #    albfd.write(data)
        albumlist = []
        data = data["items"]
        for key, value in data.items():
            albumlist.append(value)

        #for blub in data:
        #parse
        #create new Album()
        pass

    def parse_maxpages(self, data):
        maxentries = data["total_count"]
        maxpages = math.ceil(maxentries/48)

    def run(self):
        while not self.stop.is_set():
            time.sleep(1)