""" Base Msghandler Class to reduce duplication """
import types
from time import sleep
from multiprocessing import Queue
import logging
import sys

from messages import Msg

LOG_FORMAT = '%(asctime)-15s | %(module)s %(name)s %(process)d %(thread)d | %(funcName)20s() - Line %(lineno)d | %(levelname)s | %(message)s'
LOGGER = logging.getLogger('rbmd.msghndlr')
LOGGER.setLevel(logging.DEBUG)
strmhdlr = logging.StreamHandler(sys.stdout)
strmhdlr.setLevel(logging.INFO)
strmhdlr.setFormatter(logging.Formatter(LOG_FORMAT))
flhdlr = logging.FileHandler("../logs/error.log", mode="a", encoding="utf-8", delay=False)
flhdlr.setLevel(logging.DEBUG)
flhdlr.setFormatter(logging.Formatter(LOG_FORMAT))
LOGGER.addHandler(strmhdlr)
LOGGER.addHandler(flhdlr)
def uncaught_exceptions(exc_type, exc_val, exc_trace):
    import traceback
    if exc_type is None and exc_val is None and exc_trace is None:
        exc_type, exc_val, exc_trace = sys.exc_info()
    LOGGER.exception("Uncaught Exception of type %s was caught: %s\nTraceback:\n%s" % (exc_type, exc_val, traceback.print_tb(exc_trace)))
    try:
        del exc_type, exc_val, exc_trace
    except:
        LOGGER.exception(Exception("Exception args could not be deleted"))
sys.excepthook = uncaught_exceptions


class MessageHandler():
    def __init__(self, queue=None, size=5000, interval=0.5):
        if queue == None:
            self.queue = Queue(size)
        else:
            self.queue = queue


    def __init_subclass__(cls):
        if "analyze" in cls.__dict__.keys():
            if not isinstance(cls.__dict__["analyze"], types.FunctionType):
                raise AttributeError("Function \"analyze\" must be a function")
        else:
            raise AttributeError("Function \"analyze\" must be defined")
        super().__init_subclass__()


    def __del__(self):
        self.queue.cancel_join_thread()
        self.queue.close()


    def send(self, msg):
        msg.sender = self.__class__.__name__
        LOGGER.info("%s sent: %s" % (msg.sender, msg))
        self.queue.put(msg, block=True)


    def recieve(self):
        if not self.queue.empty():
            msg = self.queue.get(block=True)
            if isinstance(msg, Msg):
                if msg.sender == self.__class__.__name__:
                    self.send(msg)
                    return None
                return msg