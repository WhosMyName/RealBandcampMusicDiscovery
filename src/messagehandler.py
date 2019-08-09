""" Base Msghandler Class to handle IPC """
import types
from multiprocessing import Queue
import logging
import sys

from messages import Msg

LOGGER = logging.getLogger('rbmd.msghndlr')
LOG_FORMAT = "%(asctime)-15s | %(levelname)s | %(module)s %(name)s %(process)d %(thread)d | %(funcName)20s() - Line %(lineno)d | %(message)s"
LOGGER.setLevel(logging.DEBUG)
STRMHDLR = logging.StreamHandler(stream=sys.stdout)
STRMHDLR.setLevel(logging.INFO)
STRMHDLR.setFormatter(logging.Formatter(LOG_FORMAT))
FLHDLR = logging.FileHandler(
    "../logs/error.log", mode="a", encoding="utf-8", delay=False)
FLHDLR.setLevel(logging.DEBUG)
FLHDLR.setFormatter(logging.Formatter(LOG_FORMAT))
LOGGER.addHandler(STRMHDLR)
LOGGER.addHandler(FLHDLR)


def uncaught_exceptions(exc_type, exc_val, exc_trace):
    """ injected function to log exceptions """
    import traceback
    if exc_type is None and exc_val is None and exc_trace is None:
        exc_type, exc_val, exc_trace = sys.exc_info()
    LOGGER.exception("Uncaught Exception of type %s was caught: %s\nTraceback:\n%s",
                     exc_type, exc_val, traceback.print_tb(exc_trace))
    try:
        del exc_type, exc_val, exc_trace
    except Exception as excp:
        LOGGER.exception("Exception caught during tb arg deletion:\n%s", excp)


sys.excepthook = uncaught_exceptions


class MessageHandler():
    """ the messagehandler class """
    def __init__(self, queue=None, size=5000):
        LOGGER.debug("%s init", self)
        if queue is None:
            self.queue = Queue(size)
        else:
            self.queue = queue

    def __init_subclass__(cls):
        """ subclass init to make sure that subclasses implement the analyze function """
        if "analyze" in cls.__dict__.keys():
            if not isinstance(cls.__dict__["analyze"], types.FunctionType):
                raise AttributeError("Function \"analyze\" must be a function")
        else:
            raise AttributeError("Function \"analyze\" must be defined")
        super().__init_subclass__()

    def __del__(self):
        """ delete dis """
        self.queue.cancel_join_thread()
        self.queue.close()

    def send(self, msg):
        """ sets metadata and enqueues message """
        msg.sender = self.__class__.__name__
        LOGGER.debug("%s sent: %s", msg.sender, msg)
        self.queue.put(msg, block=True)

    def recieve(self):
        """ pulls message from queue and returns it from queue if it's originator """
        if not self.queue.empty():
            msg = self.queue.get(block=False)
            if isinstance(msg, Msg):
                LOGGER.debug("%s received Msg: %s in Q from: %s", self.__class__.__name__, msg, msg.sender)
                if msg.sender == self.__class__.__name__:
                    LOGGER.debug("Resent Message to Queue")
                    self.send(msg)
                    return None
                return msg #Either all return statements in a function should return an expression, or none of them should. (inconsistent-return-statements)
        else:
            pass
            #LOGGER.debug("%s is empty", self.queue)
