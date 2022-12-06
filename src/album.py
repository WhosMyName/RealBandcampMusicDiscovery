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
        return f"{self.band} - {self.name}"

    def __repr__(self):
        return f"{self.__class__} - {str(self.__dict__)}"

    def __hash__(self):
        return hash((self.band, self.name))

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()
