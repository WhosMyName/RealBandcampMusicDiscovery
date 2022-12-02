""" Base Msghandler Class to handle IPC """
import types
from multiprocessing.connection import Listener, Client, Connection
import logging
import sys
from threading import Thread
from os import name as os_name


if os_name == "nt":
    SLASH = "\\"
else:
    SLASH = "/"

LOGGER = logging.getLogger('rbmd.msghndlr')
LOG_FORMAT = "%(asctime)-15s | %(levelname)s | %(module)s %(name)s %(process)d %(thread)d | %(funcName)20s() - Line %(lineno)d | %(message)s"
LOGGER.setLevel(logging.DEBUG)
STRMHDLR = logging.StreamHandler(stream=sys.stdout)
STRMHDLR.setLevel(logging.INFO)
STRMHDLR.setFormatter(logging.Formatter(LOG_FORMAT))
FLHDLR = logging.FileHandler(f"..{SLASH}logs{SLASH}error.log", mode="a", encoding="utf-8", delay=False)
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

class MessageHandler(Thread):
    """ the messagehandler class """
    def __init__(self, connectionParams: dict, isClient: bool = False):
        Thread.__init__(self)
        self.address = connectionParams["address"]
        self.port = connectionParams["port"]
        self.authkey = connectionParams["key"]
        self.listener: Listener = None
        self.connection: Connection = None
        if isClient:
            self.connection = Client(address=(self.address, self.port), family="AF_INET", authkey=self.authkey)
        else:
            self.listener = Listener(address=(self.address, self.port), family="AF_INET", authkey=self.authkey)
        self.start()

    def __init_subclass__(cls):
        """ subclass init to make sure that subclasses implement the analyze function """
        if "analyze" in cls.__dict__.keys():
            if not isinstance(cls.__dict__["analyze"], types.FunctionType):
                raise AttributeError("\"analyze\" must be a function")
        else:
            raise AttributeError("Function \"analyze\" must be defined")
        super().__init_subclass__()

    def __del__(self):
        """ delete dis """
        LOGGER.info(f"{self} deleting...")
        if self.connection:
            self.connection.close()
        if self.listener:
            self.listener.close()

    def send(self, msg):
        """ sets metadata and sends the message """
        if self.connection:
            LOGGER.info(f"{self.__class__.__name__} sent: {msg}")
            return self.connection.send(msg)

    def recieve(self):
        """ pulls message from socket connection """
        if self.connection and self.connection.poll(0.1):
            return self.connection.recv()

    def isConnected(self):
        if self.connection:
            return True
        return False

    def run(self) -> None:
        while self.connection == None: # reinit the listener
            try:
                self.connection = self.listener.accept()
            except Exception as excp:
                LOGGER.exception(f"Connector caught exception:\n{excp}")

    def checkPortFree(port: int):
        from socket import socket, SOCK_STREAM, AF_INET
        tested : bool = False
        sock = socket(AF_INET, SOCK_STREAM)
        while not tested:
            try:
                sock.bind(("127.0.0.1", port))
                tested = True
            except:
                LOGGER.debug(f"Port {port} is already in use, retrying...")
                port = port + 1  
        sock.close()
        return port