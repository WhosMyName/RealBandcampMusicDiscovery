""" generic class to hold all album related data """


class Album():
    """ generic class to reflect all album relevant data """

    def __init__(self, name: str, url: str, band: str, cover_url: str):
        self.name: str = name
        self.genre: set = set()
        self.url: str = url
        self.band: str = band
        self.cover = None
        self.cover_url: str = cover_url

    def __str__(self):
        return "%s - %s" % (self.band, self.name)

    def __repr__(self):
        return "%s - %s" % (self.__class__, str(self.__dict__))

    def __hash__(self):
        return hash((self.band, self.name))

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()


def __main__():
    alb = Album("GenericALbum.exe", "https://github.com/whosmyname", "datboigud",
                "https://i.pinimg.com/originals/5e/40/5b/5e405be0320863d04c84b399dc2969ca.jpg")
    alb2 = Album("GenericALbum.exe", "https://github.com/whosmyname", "datboigud",
                 "https://i.pindfzguhiojkplöimg.com/originals/5e/40/5b/5e405be0320863d04c84b399dc2969ca.jpg")
    print(alb.__hash__())
    print(alb2.__hash__())
    print(alb.__hash__() == alb2.__hash__())
    sed = set()
    sed.add(alb)
    sed.add(alb2)
    print(sed)


if __name__ == "__main__":
    __main__()
