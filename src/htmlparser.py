"""rewfew"""

import threading
from tags import Tag
from album import Album
import math

class HTMLParser(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.stop = threading.Event()
        pass

    def parse_tags(self, data):
        with open("tags.html", "w") as tagfd:
            tagfd.write(data)
        #figure out how subtags work
        #taglist = []
        #for blub in data:
        #parse
        #create new Tag()
        pass
    
    def parse_albums(self, data):
        with open("albums.html", "w") as albfd:
            albfd.write(data)
        #albumlist = []
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