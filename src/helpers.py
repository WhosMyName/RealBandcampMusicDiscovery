import sys
from types import FunctionType
import logging
from os import name, path, makedirs
from datetime import datetime as dt


################################### OS Path Separators + and other things
if name == "nt":
    PATHSEP = "\\"
else:
    PATHSEP = "/"

CWD = f"{path.dirname(path.realpath(__file__))}{PATHSEP}"

# define dangerous chars that might cause issues in FS
# substitute with
# from re import sub as re_sub
# re_sub(DANGER_CHARS, '_', *STRINGHERE*).strip('.')
DANGER_CHARS = "[\[\/\\\*\?:\"<>\|~°\^\]]"


################################### Helper Logger
LOG_FORMAT = "%(asctime)-15s | %(levelname)s | %(module)s %(name)s %(process)d %(thread)d | %(funcName)20s() - Line %(lineno)d | %(message)s"
class HLogger(logging.Logger):
    
    def __init__(self, name, level=logging.DEBUG):
        super().__init__(name=name, level=level)
        loggingPath = f"logs{PATHSEP}"
        loggingFile = f"{loggingPath}error.log"
        if not path.exists(loggingPath):
            makedirs(loggingPath)
        self.strmhndlr: logging.StreamHandler = logging.StreamHandler(stream=sys.stdout)
        self.strmhndlr.setLevel(logging.INFO)
        self.strmhndlr.setFormatter(logging.Formatter(LOG_FORMAT))
        self.addHandler(self.strmhndlr)
        self.flhndlr: logging.FileHandler = logging.FileHandler(filename=loggingFile, mode="a", encoding="utf-8", delay=False)
        self.flhndlr.setLevel(logging.DEBUG)
        self.flhndlr.setFormatter(logging.Formatter(LOG_FORMAT))
        self.addHandler(self.flhndlr)

    def set_file_handler_level(self, level: int = logging.INFO):
        self.flhndlr.setLevel(level=level)

    def set_stream_handler_level(self, level: int = logging.INFO):
        self.strmhndlr.setLevel(level=level)

    def set_log_location(self, filename: str):
        logLevel = self.flhndlr.level
        encoding = self.flhndlr.encoding
        mode = self.flhndlr.mode
        self.flhndlr = logging.FileHandler(filename=filename, mode=mode, encoding=encoding, delay=False)
        self.flhndlr.setLevel(logLevel)
        self.flhndlr.setFormatter(logging.Formatter(LOG_FORMAT))


################################### Exception Handler Decorator
LOGGER = HLogger("ExceptionHelper")

def safety_wrapper(func: FunctionType):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as excp:
            LOGGER.exception(f"Caught excpetion:\n{excp}")
    return wrapper

def speedtest_wrapper(func: FunctionType):
    def wrapper(*args, **kwargs):
        try:
            dt0 = dt.now()
            retval = func(*args, **kwargs)
            dt1 = dt.now()
            print(f"Execution of Function {func.__name__} took {dt1-dt0} seconds.")
            return retval
        except Exception as excp:
            LOGGER.exception(f"Caught excpetion:\n{excp}")
    return wrapper