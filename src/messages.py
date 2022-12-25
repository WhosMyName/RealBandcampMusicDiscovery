""" Lé big [x]mq rip off aka classes to replace old event based IPC system that didn't worked (redit: as expected :rollseyes:) """

# give this bic boii a gud think

class Msg():
    """ Base Class for all Msg-Types """

    def __init__(self, data=None):
        """ simple init """
        self.sender = None
        self.data = data

    def get_sender(self):
        """ returns sender """
        return self.sender

    def get_data(self):
        """ returns data """
        return self.data

    def __str__(self) -> str:
        "returns string representation of message object"
        return f"{self.sender} sent {self.__class__.__name__} with: {self.data}"


class MsgGetTags(Msg):
    """ class to set signal for getting all tags """

    def __init__(self, data=None):
        super().__init__(data)


class MsgPutTags(Msg):
    """ class to deliver tags """

    def __init__(self, data=None):
        super().__init__(data)


class MsgPutFetchTags(Msg):
    """ class to deliver fetch tags """

    def __init__(self, data=None):
        super().__init__(data)


class MsgPutAlbums(Msg):
    """ class to deliver albums """

    def __init__(self, data=None):
        super().__init__(data)


class MsgDownloadAlbums(Msg):
    """ class to download albums """

    def __init__(self, data=None):
        super().__init__(data)


class MsgFinishedDownloads(Msg):
    """ class to download albums """

    def __init__(self, data=None):
        super().__init__(data)


class MsgSetProgress(Msg):
    """indicator message to (re-)set progress of operations"""

    def __init__(self, curr: int = 0, max: int = 0, mes: str = ""):
        data: dict = {"curr": curr, "max": max, "message": mes}
        super().__init__(data)


class MsgPause(Msg):
    """ class to signal pause of current fetch cycle for albums """

    def __init__(self, data=None):
        super().__init__(data)


class MsgQuit(Msg):
    """ class to signal the stop of program execution """

    def __init__(self, data=None):
        super().__init__(data)