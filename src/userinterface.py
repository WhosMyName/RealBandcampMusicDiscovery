""" class to display userinterface """

import sys
from math import ceil
from time import sleep
import logging
import multiprocessing

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from album import Album
from webconnector import Connector
from messages import *
from messagehandler import MessageHandler


LOGGER = logging.getLogger('rbmd.ui')
LOG_FORMAT = '%(asctime)-15s | %(module)s %(name)s %(process)d %(thread)d | %(funcName)20s() - Line %(lineno)d | %(levelname)s | %(message)s'
LOGGER.setLevel(logging.DEBUG)
STRMHDLR = logging.StreamHandler(stream=sys.stdout)
STRMHDLR.setLevel(logging.INFO)
STRMHDLR.setFormatter(logging.Formatter(LOG_FORMAT))
FLHDLR = logging.FileHandler("../logs/error.log", mode="a", encoding="utf-8", delay=False)
FLHDLR.setLevel(logging.DEBUG)
FLHDLR.setFormatter(logging.Formatter(LOG_FORMAT))
LOGGER.addHandler(STRMHDLR)
LOGGER.addHandler(FLHDLR)
def uncaught_exceptions(exc_type, exc_val, exc_trace):
    """ injected function to log exceptions """
    import traceback
    if exc_type is None and exc_val is None and exc_trace is None:
        exc_type, exc_val, exc_trace = sys.exc_info()
    LOGGER.exception("Uncaught Exception of type %s was caught: %s\nTraceback:\n%s", exc_type, exc_val, traceback.print_tb(exc_trace))
    try:
        del exc_type, exc_val, exc_trace
    except Exception as excp:
        LOGGER.exception("Exception caught during tb arg deletion:\n%s", excp)
sys.excepthook = uncaught_exceptions


class MainWindow(QMainWindow, MessageHandler):
    """ Class that refelcts the "main-window" """

    # pylint: disable=too-many-instance-attributes

    def __init__(self):
        """ init """
        MessageHandler.__init__(self)
        LOGGER.info("Self: %s" % self)
        QMainWindow.__init__(self)
        LOGGER.info("Self: %s" % self)

        self.connector = Connector(self.queue)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.msgcapture)
        self.timer.start(5000)

        self.layout = QGridLayout()
        self.layout.setSizeConstraint(QLayout.SetMinimumSize)
        self.widget = QWidget()
        self.widget.setMinimumSize(800, 600)
        self.widget.setLayout(self.layout)

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidget(self.widget)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.setCentralWidget(self.scrollArea)


        self.setWindowTitle("RealBandcampMusicDisc0very")
        self.setGeometry(QRect(0, 0, 1280, 720))
        self.albumlist = set()
        self.genrelist = set()
        self.btnlist = []
        self.selectorlist = []
        self.fetchedAlbums = {}
        LOGGER.info("Self: %s" % self)

        self.closeEvent = self.close
        self.showEvent = self.show()
        self.statusBar()
        self.firstloaded = True
        self.initMenu()
        self.initToolbar()
        self.show()
        self.send(MsgGetTags())
        self.setStatusTip("Initializing...")
        self.msgbox = QMessageBox(self)
        self.msgbox.setText("Initializing...")
        self.msgbox.show()
        LOGGER.info("Self: %s" % self)


    def __del__(self):
        """ del """
        MessageHandler.__del__(self)
        self.connector.__del__()
        self.queue.close()


    def close(self, event):
        """ injection func for closing ther window """
        self.__del__()


############################################## QWindow Props ##################################################


    def finalizeInit(self):
        """ func to handle init finalization """
        self.msgbox.done(0)
        self.msgbox.destroy(True)
        self.clear.setEnabled(True)
        self.compare.setEnabled(True)
        self.reload.setEnabled(True)
        self.more.setEnabled(True)
        self.setStatusTip("Init done!")
        LOGGER.info("Init done")


    def initToolbar(self):
        """ toolbar's init func"""
        self.toolbar = self.addToolBar("Generic Foobar")

        self.clear = self.toolbar.addAction("clear")
        self.clear.triggered.connect(self.clearLayout)
        self.clear.setStatusTip("Clear All")
        self.clear.setEnabled(False)

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
        """ func that defines menu capabilities """
        self.menuBar = self.menuBar()
        self.helpMenu = self.menuBar.addMenu(" &Help")

        ###############MENU ACTIONS#################################
        self.saveAction = QAction(" &Save", self)
        self.saveAction.setShortcut("Ctrl+S")
        self.saveAction.setStatusTip("Save results to file")
        self.saveAction.triggered.connect(self.saveToFile)

        self.helpAction = QAction(" &Help", self)
        self.helpAction.setShortcut("F1")
        self.helpAction.setStatusTip("Show the help")
        self.helpAction.triggered.connect(self.showHelp)

        self.quitAction = QAction(" &Quit", self)
        self.quitAction.setShortcut("Crtl+Q")
        self.quitAction.setStatusTip("Quit this Application")
        self.quitAction.triggered.connect(self.quitApplication)

        self.helpMenu.addAction(self.saveAction)
        self.helpMenu.addAction(self.helpAction)
        self.helpMenu.addAction(self.quitAction)


    def saveToFile(self):
        """ saves current albums with tags to file """
        genre = ""
        for action in self.selectorlist:
            selector = self.toolbar.widgetForAction(action)
            genre = genre + " " + selector.currentData(0) + " #"
        with open("save.txt", "a") as save:
            save.write("\n##################%s#################\n" % genre)
            for album in self.albumlist:
                save.write("%s - %s\t%s\n" % (album.band, album.name, album.url))
        self.setStatusTip("Data saved to file!")


    def quitApplication(self):
        """ quit """
        print("####################################Quit!############################################")


    def showHelp(self):
        """ help """
        print("####################################Help!############################################")

# WIP - add help menu that displays infos about the "program" and an updater button

########################################## End QWindow Props ##################################################
############################################## Logikz #########################################################

    def refresh(self):
        """ func to grab albums based on current selectors """
        LOGGER.info("refreshing selection")
        comp = set()
        for action in self.selectorlist:
            selector = self.toolbar.widgetForAction(action)
            if selector.currentData(0) in self.fetchedAlbums.keys():
                self.albumlist.update(self.fetchedAlbums[selector.currentData(0)])
            elif selector.currentData(0) == "None":
                self.toolbar.removeAction(action)
                self.selectorlist.remove(action)
            else:
                comp.add(selector.currentData(0))
        LOGGER.debug(comp)
        self.send(MsgPutFetchTags(data=comp))
        self.setStatusTip("Fetching Albums...")
        self.updateLayout()


    def comparison(self):
        """ compares based on current selectors """
        self.setStatusTip("Comparing Albums...")
        comp = set()
        for action in self.selectorlist:
            selector = self.toolbar.widgetForAction(action)
            comp.add(selector.currentData(0))
        LOGGER.debug(comp)
        compareset = set()
        #for album in self.albumlist: #set().intersection lambda key: comp.issubset(album.genre)
        for album in self.albumlist:
            if comp.issubset(album.genre):
                compareset.add(album)
                LOGGER.debug("Added %s after comparison", album.name)
        self.albumlist = compareset
        self.updateLayout()
        self.setStatusTip("Comparison done!")


    def processAlbums(self, msg):
        """  """
        albumsdict = msg.data
        for key, value in albumsdict.items():
            if key in self.fetchedAlbums.keys():
                albumsfetched = self.fetchedAlbums[key]
                albumsfetched.update(value)
                self.fetchedAlbums[key] = albumsfetched
            else:
                self.fetchedAlbums[key] = value
            self.albumlist.update(value)
        self.updateLayout()


    def add_genre_selector(self):
        """ creates a dropdown QComboBox """
        dd = QComboBox(parent=self)
        dd.setEditable(True)
        dd.setInsertPolicy(3)
        compfilter = QSortFilterProxyModel(dd)
        compfilter.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        compfilter.setFilterKeyColumn(1)
        compfilter.setSourceModel(dd.model())
        comp = QCompleter(compfilter, dd)
        comp.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        comp.setCompletionMode(QCompleter.PopupCompletion)
        comp.setFilterMode(QtCore.Qt.MatchContains)
        dd.setCompleter(comp)
        dd.addItems(self.genrelist)
        self.selectorlist.append(self.toolbar.addWidget(dd))


    def add_album(self, album):
        """ creates an album button """
        if isinstance(album, Album):
            btn = QPushButton("Artist: %s\nAlbum: %s" % (album.band, album.name), None)
            icn = QIcon() # see ref doc
            btn.setIcon(icn)
            btn.setIconSize(QSize(20, 20))
            LOGGER.debug("Adding Album %s" % album.name)
            self.btnlist.append(btn)
        else:
            LOGGER.error("Wanted to add %s, but it's not an Album" % album)


    def clearLayout(self):
        """ clears current layout """
        self.albumlist = set()
        self.updateLayout()


    def updateLayout(self):
        """ refreshes/updates current layout and adds all the albums to the layout """
        LOGGER.info("Refreshing Layout")

        for widget in self.layout.children():
            self.layout.removeWidget(widget)

        while self.layout.count() != 0:
            useless = self.layout.takeAt(0)
            del useless

        for child in self.widget.children():
            if not isinstance(child, QGridLayout):
                child.deleteLater()

        self.btnlist = []

        for album in self.albumlist:
            self.add_album(album)

        positions = [(x, y) for x in range(int(ceil(len(self.btnlist)/5))) for y in range(1, 6)]
        for position, btn in zip(positions, self.btnlist):
            self.layout.addWidget(btn, *position)


    def msgcapture(self):
        """"""
        self.analyze(self.recieve())


    def analyze(self, msg):
        """ generic "callback" to check msgs and set flags and call functions """
        if msg is not None:
            LOGGER.info("Received Msg: %s in Q: %s" % (msg, self.queue))
            if isinstance(msg, MsgPutTags):
                self.storeTagsFromMsg(msg)
                self.finalizeInit()
            elif isinstance(msg, MsgPutAlbums):
                self.processAlbums(msg)
            else:
                LOGGER.error("Unknown Message:\n%s" % msg)


    def storeTagsFromMsg(self, msg):
        """ stores default tags from msg """
        if msg.data is not None:
            self.genrelist = sorted(msg.data)


############################################## End Logikz #####################################################

def __main__():
    """ main """
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    __main__()
