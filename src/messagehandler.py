""" Base Msghandler Class to handle IPC """
import types
from multiprocessing.connection import Listener, Client, Connection
from threading import Thread

from helpers import safety_wrapper, HLogger
LOGGER = HLogger(name="rbmd.msghndlr")

class MessageHandler(Thread):
    """ the messagehandler class """

    @safety_wrapper
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

    @safety_wrapper
    def __init_subclass__(cls):
        """ subclass init to make sure that subclasses implement the analyze function """
        if "analyze" in cls.__dict__.keys():
            if not isinstance(cls.__dict__["analyze"], types.FunctionType):
                raise AttributeError("\"analyze\" must be a function")
        else:
            raise AttributeError("Function \"analyze\" must be defined")
        super().__init_subclass__()

    @safety_wrapper
    def __del__(self):
        """ delete dis """
        LOGGER.debug(f"{self} deleting...")
        if self.connection:
            self.connection.close()
        if self.listener:
            self.listener.close()

    @safety_wrapper
    def send(self, msg):
        """ sets metadata and sends the message """
        if self.connection:
            LOGGER.debug(f"{self.__class__.__name__} sent: {msg}")
            return self.connection.send(msg)

    @safety_wrapper
    def recieve(self):
        """ pulls message from socket connection """
        if self.connection and self.connection.poll(0.1):
            return self.connection.recv()

    @safety_wrapper
    def isConnected(self):
        if self.connection:
            return True
        return False

    @safety_wrapper
    def run(self) -> None:
        while self.connection == None: # reinit the listener
            try:
                self.connection = self.listener.accept()
            except Exception as excp:
                LOGGER.exception(f"Connector caught exception:\n{excp}")

    @safety_wrapper
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