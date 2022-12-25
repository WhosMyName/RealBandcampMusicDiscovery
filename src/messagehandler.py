""" Base Msghandler Class to handle IPC """
import types
from multiprocessing.connection import Listener, Client, Connection
from threading import Thread

from helpers import safety_wrapper, HLogger
from messages import Msg
LOGGER = HLogger(name="rbmd.msghndlr")

class MessageHandler(Thread):
    """ the messagehandler class """

    @safety_wrapper
    def __init__(self, connectionParams: dict, moduleName: str, isClient: bool = False):
        Thread.__init__(self)
        self.moduleName: str = moduleName
        self.address: str = connectionParams["address"]
        self.port: int = connectionParams["port"]
        self.authkey: bytes = connectionParams["key"]
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
    def send(self, msg: Msg):
        """ sets metadata and sends the message """
        try:
            if self.connection:
                msg.set_sender(self.moduleName)
                LOGGER.debug(f"{msg}")
                return self.connection.send(msg)
        except ConnectionError as excp:
            LOGGER.exception(excp)
            self.__del__()

    @safety_wrapper
    def recieve(self) -> Msg:
        """ pulls message from socket connection """
        try:
            if self.connection and not self.connection.closed and self.connection.poll(0.1):
                return self.connection.recv()
        except ConnectionError as excp:
            LOGGER.exception(excp)
            self.__del__()

    @safety_wrapper
    def is_connected(self) -> bool:
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
    def check_port_free(port: int) -> int:
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