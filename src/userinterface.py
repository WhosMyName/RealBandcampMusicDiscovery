""" class to display userinterface """

import sys
from time import sleep
import logging
import multiprocessing
import traceback

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from album import Album
from core import Core
from webconnector import Connector
from messages import *
from messagehandler import MessageHandler


LOG_FORMAT = '%(asctime)-15s | %(module)s %(name)s %(process)d %(thread)d | %(funcName)20s() - Line %(lineno)d | %(levelname)s | %(message)s'
LOGGER = logging.getLogger('rbmd.ui')
LOGGER.setLevel(logging.DEBUG)
strmhdlr = logging.StreamHandler(sys.stdout)
strmhdlr.setLevel(logging.INFO)
strmhdlr.setFormatter(logging.Formatter(LOG_FORMAT))
flhdlr = logging.FileHandler("../logs/error.log", mode="a", encoding="utf-8", delay=False)
flhdlr.setLevel(logging.DEBUG)
flhdlr.setFormatter(logging.Formatter(LOG_FORMAT))
LOGGER.addHandler(strmhdlr)
LOGGER.addHandler(flhdlr)
def uncaught_exceptions(type, value, tb):
    LOGGER.critical("Uncaught Exception of type %s was caught: %s\nTraceback:\n%s" % (type, value, traceback.print_tb(tb)))
sys.excepthook = uncaught_exceptions


##################################
#get exceptions into logs
##################################


class MainWindow(QMainWindow, MessageHandler):

    def __init__(self):
        QMainWindow.__init__(self)
        MessageHandler.__init__(self)

        #super().__init__()

        #self.queue = multiprocessing.Queue(5000)
        #self.core = Core(self.queue, self)
        #self.core.start()
        #self.core.setUpdateAlbumsCallBack(self.updateAlbums)
        #self.core.setFetchedAlbumsCallback(self.updateFetchedAlbums)
        #self.core.fetchTagsEvent.set()
        self.connector = Connector(self.queue)
        #self.connector.start()

        self.timer = QTimer(self)
        self.timer.start(750)
        self.timer.timeout.connect(self.syncCoreWithConnector)

        self.layout = QGridLayout()
        self.widget = QWidget()
        self.widget.setMinimumSize(800, 600)
        self.widget.setLayout(self.layout)
        self.setCentralWidget(self.widget)
        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.widget)
        self.setWindowTitle("RealBandcampMusicDisc0very")
        self.setGeometry(QRect(0, 0, 1280, 720))
        self.albumlist = set()
        self.genrelist = set()
        self.btnlist = []
        self.selectorlist = []
        self.fetchedAlbums = {}

        self.updateEvent = multiprocessing.Event()
        self.updateEvent.clear()

        self.fetchTagsInQ = multiprocessing.Event()

        self.closeEvent = self.close
        self.showEvent = self.show()
        self.statusBar()
        self.firstloaded = True
        self.initMenu()
        self.initToolbar()
        self.show()
        self.start()


    def __del__(self):
        #self.core.__del__()
        self.connector.__del__()
        self.queue.close()


    def close(self, event):
        self.__del__()


    def initInit(self):
        self.setStatusTip("Initializing...")
        self.msgbox = QMessageBox(self)
        self.msgbox.setText("Initializing...")
        self.msgbox.show()


    def finalizeInit(self):
        self.msgbox.done(0)
        self.msgbox.destroy(True)
        self.compare.setEnabled(True)
        self.reload.setEnabled(True)
        self.more.setEnabled(True)
        self.setStatusTip("Init done!")
        LOGGER.info("Init done")


    def storeTagsFromMsg(self, msg):
        if msg.data is not None:
            self.genrelist = set(msg.data)


    def initToolbar(self):
        self.toolbar = self.addToolBar("Generic Foobar")

        self.compare = self.toolbar.addAction("compare noods")
        self.compare.triggered.connect(self.comparison)
        self.compare.setStatusTip("Compare!")
        self.compare.setEnabled(False)

        self.reload = self.toolbar.addAction("fresh noods")
        self.reload.triggered.connect(self.refresh)
        self.reload.setStatusTip("Apply")
        self.reload.setEnabled(False)

        self.more = self.toolbar.addAction("more noods")
        self.more.triggered.connect(self.add_genre_selector)
        self.more.setStatusTip("Add an additional Selector")
        self.more.setEnabled(False)


    def initMenu(self):
        self.menuBar = self.menuBar()
        self.helpMenu = self.menuBar.addMenu(" &Help")

        ###############MENU ACTIONS#################################
        self.helpAction = QAction(" &Help", self)
        self.helpAction.setShortcut("F1")
        self.helpAction.setStatusTip("Show the help")
        self.helpAction.triggered.connect(self.showHelp)

        self.quitAction = QAction(" &Quit", self)
        self.quitAction.setShortcut("Crtl+Q")
        self.quitAction.setStatusTip("Quit this Application")
        self.quitAction.triggered.connect(self.quitApplication)

        self.helpMenu.addAction(self.helpAction)
        self.helpMenu.addAction(self.quitAction)


    def quitApplication(self):
        print("####################################Quit!############################################")


    def showHelp(self):
        print("####################################Help!############################################")


    def refresh(self):
        LOGGER.info("refreshing selection")
        comp = set()
        for selector in self.selectorlist:
            if selector == '':
                self.selectorlist.remove(selector)
                self.toolbar.removeWidget(selector)
            elif selector not in self.fetchedAlbums.keys():
                comp.add(selector.currentData(0))
            else:
                self.albumlist.append(self.fetchedAlbums[selector])
        LOGGER.debug(comp)
        if self.queue.empty():
            for tag in comp:
                self.queue.put(tag) # set event for connector
        self.fetchTagsInQ.set()
        self.setStatusTip("Fetching Albums...")
            

    def getAlbumsFromQ(self):
        LOGGER.debug("Getting Albums from Q")
        if not self.queue.empty():
            while not self.queue.empty():
                albums = self.queue.get()
                LOGGER.debug(albums)
                for value in albums.values():
                    self.updateAlbums(value)
            self.updateFetchedAlbums(albums)
            LOGGER.info("Got Albums from Q")
        else:
            LOGGER.warning("Tried to get Albums from Q but it's empty")


    def updateAlbums(self, albums):
        LOGGER.info("Updating Albums")
        self.albumlist.update(albums)
        for album in self.albumlist:
            self.add_album(album)
        self.updateLayout()


    def updateFetchedAlbums(self, albumsdict):
        for key, value in albumsdict.items():
            if key in self.fetchedAlbums.keys():
                albumsfetched = self.fetchedAlbums[key]
                albumsfetched.update(value)
                self.fetchedAlbums[key] = albumsfetched
            else:
                self.fetchedAlbums[key] = value


    def comparison(self):
        self.setStatusTip("Comparing Albums...")
        comp = set()
        for selector in self.selectorlist:
            comp.add(selector.currentData(0))
        LOGGER.debug(comp)
        compareset = set()
        dt = time()
        for album in self.albumlist:
            LOGGER.debug("%s - %s [%r]" % (album.name, album.genre, taglist))
            if comp.issubset(album.genre):
                compareset.add(album)
                LOGGER.debug("Added %s after comparison" % album.name)
        dt1 = time()
        LOGGER.debug("Time spent comparing: %s" % (dt1-dt))
        self.albumlist = compareset
        self.updateLayout()
        self.setStatusTip("Comparison done!")


    def add_genre_selector(self):
        dd = QComboBox(parent=self)
        compfilter = QSortFilterProxyModel(dd)
        compfilter.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        compfilter.setSourceModel(dd.model())
        comp = QCompleter(compfilter, dd)
        comp.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        comp.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        comp.setFilterMode(QtCore.Qt.MatchContains)
        dd.setCompleter(comp)
        dd.addItems(self.genrelist)
        self.toolbar.addWidget(dd)
        self.selectorlist.append(dd)


    def add_album(self, album):
        if isinstance(album, Album):
            btn = QPushButton("%s - %s" % (album.band, album.name))
            icn = QIcon() # see ref doc
            btn.setIcon(icn)
            btn.setIconSize(QSize(20, 20))
            LOGGER.debug("Adding Album %s" % album.name)
            self.btnlist.append(btn)
        else:
            LOGGER.error("Wanted to add %s, but it's not an Album" % album)
            #self.updateLayout()


    def updateLayout(self):
        LOGGER.info("Refreshing Layout")
        for btn in self.btnlist:
            self.layout.removeWidget(btn)
        positions = [ (x,y) for x in range(int(len(self.btnlist)/5)) for y in range(5) ]
        for position, btn in zip(positions, self.btnlist):
            self.layout.addWidget(btn, *position)


    def syncCoreWithConnector(self):
        LOGGER.info("Syncing...")
        if self.firstloaded:
            self.send(MsgGetTags(sender=self.__class__.__name__))
            self.firstloaded = False
            self.timer.stop()
            self.timer.start(5000)
            self.initInit()
        ###############
        #self.analyze(self.recieve())
        #change all this to fit new arch
        #if self.fetchTagsInQ.is_set():
        #    LOGGER.info("should've put tags in Q")
        #    self.connector.getFetchTagsFromQ.set()
        #    self.fetchTagsInQ.clear()
        #elif self.connector.albumsReadyEvent.is_set():
        #    self.connector.albumsReadyEvent.clear()
        #    self.getAlbumsFromQ()
        #LOGGER.info(self.connector.albumsReadyEvent.is_set())


    def run(self):
        while not self.stop.is_set():
            self.analyze(self.recieve())
            sleep(self.interval)


    def analyze(self, msg): # WIP
        if msg is not None:
            LOGGER.info("Received Msg: %s in Q: %s" % (msg, self.queue))
            if isinstance(msg, MsgPutTags):
                self.storeTagsFromMsg(msg)
                self.finalizeInit()
            elif isinstance(msg, MsgPutAlbums):
                pass
                #set event for albums
            else:
                LOGGER.error("Unknown Message:\n%s" % msg)        


def __main__():
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    __main__()
