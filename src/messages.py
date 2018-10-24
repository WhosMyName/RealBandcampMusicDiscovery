""" Lé big [x]mq rip off aka classes to replace old event based IPC system that didn't worked """

#give this bic boii a gud think

class Msg():
    """Base Class for all Msg-Types"""
    def __init__(self, sender=None, data=None):
        """simple init"""
        self.sender = sender
        self.data = data

class MsgGetTags(Msg):
    """ class to set signal for getting all tags """
    def __init__(self, sender, data=None):
        super().__init__(sender, data)

class MsgPutTags(Msg):
    """ class to deliver tags """
    def __init__(self, sender, data):
        super().__init__(sender, data)

class MsgPutFetchTags(Msg):
    """ class to deliver fetch tags """
    def __init__(self, sender, data):
        super().__init__(sender, data)

class MsgPutAlbums(Msg):
    """ class to deliver albums """
    def __init__(self, sender, data):
        super().__init__(sender, data)

class MsgStop(Msg):
    """ class to signal the stop of album fetching """
    def __init__(self, sender, data):
        super().__init__(sender, data)
