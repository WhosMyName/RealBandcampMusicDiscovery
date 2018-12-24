""" generic class to hold all album related data """

class Album():
    def __init__(self, name, url, band, cover_url):
        self.name = name
        self.genre = set()
        self.url = url
        self.band = band
        self.cover_url = cover_url

    def __repr__(self):
        return "%s - %s" % (self.__class__, str(self.__dict__))

    def __hash__(self):
        return hash((self.band, self.name))

def __main__():
    alb = Album("GenericALbum.exe", {"nogenre", "gitgud"}, "https://github.com/whosmyname", "datboigud", "https://i.pinimg.com/originals/5e/40/5b/5e405be0320863d04c84b399dc2969ca.jpg")
    print(alb)

if __name__ == "__main__":
    __main__()