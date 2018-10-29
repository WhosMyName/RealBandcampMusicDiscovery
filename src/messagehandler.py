""" Base Msghandler Class to reduce duplication """
import types
from time import sleep
from threading import Thread, Event
from multiprocessing import Queue
from messages import Msg

class MessageHandler(Thread):
    def __init__(self, queue=None, size=5000, interval=0.5):
        Thread.__init__(self)
        if queue == None:
            self.queue = Queue(size)
        else:
            self.queue = queue
        self.interval = interval
        self.stop = Event()
        self.stop.clear()


    def __init_subclass__(cls):
        if "analyze" in cls.__dict__.keys():
            if not isinstance(cls.__dict__["analyze"], types.FunctionType):
                raise AttributeError
        else:
            raise AttributeError
        super().__init_subclass__()


    def __del__(self):
        while not self.queue.empty():
            _ = self.queue.get()
        self.queue.close()


    def send(self, msg):
        self.queue.put(msg, block=True)


    def recieve(self):
        if not self.queue.empty():
            msg = self.queue.get(block=True)
            if isinstance(msg, Msg):
                if msg.sender == self.__class__.__name__:
                    self.send(msg)
                    return None
                return msg
