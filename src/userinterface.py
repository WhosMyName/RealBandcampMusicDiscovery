import sys
import time
import logging
import multiprocessing
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from album import Album
from core import Core
from webconnector import Connector


LOG_FORMAT = '%(asctime)-15s | %(module)s %(name)s %(process)d %(thread)d | %(funcName)20s() - Line %(lineno)d | %(levelname)s | %(message)s'
LOGGER = logging.getLogger('rbmd.ui')
LOGGER.setLevel(logging.DEBUG)
strmhdlr = logging.StreamHandler(sys.stdout)
strmhdlr.setLevel(logging.INFO)
strmhdlr.setFormatter(logging.Formatter(LOG_FORMAT))
flhdlr = logging.FileHandler("../logs/error.log", mode='a', encoding="utf-8", delay=False)
flhdlr.setLevel(logging.DEBUG)
flhdlr.setFormatter(logging.Formatter(LOG_FORMAT))
LOGGER.addHandler(strmhdlr)
LOGGER.addHandler(flhdlr)


##################################
#do an init screen 
#make all close correctly if closed manually
#get exceptions into logs
##################################


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.queue = multiprocessing.Queue(5000)
        self.core = Core(self.queue)
        self.core.start()
        self.core.setUpdateAlbumsCallBack(self.updateAlbums)
        self.core.setFetchedAlbumsCallback(self.updateFetchedAlbums)
        self.core.fetchTagsEvent.set()
        self.connector = Connector(self.queue)
        self.connector.start()

        self.timer = QTimer(self)
        self.timer.start(5000)
        self.timer.timeout.connect(self.syncCoreWithConnector)

        self.layout = QGridLayout()
        self.widget = QWidget()
        self.widget.setMinimumSize(800, 600)
        self.widget.setLayout(self.layout)
        self.setCentralWidget(self.widget)
        self.setWindowTitle("RealBandcampMusicDisc0very")
        self.setGeometry(QRect(0, 0, 1280, 720))
        self.albumlist = set()
        self.genrelist = set()
        self.btnlist = []
        self.selectorlist = []
        self.fetchedAlbums = {}

        self.closeEvent = self.close
        self.statusBar()
        self.setStatusTip("Initializing...")
        self.initMenu()
        self.initToolbar()
        self.show()
        self.waitForInit()


    def __del__(self):
        self.core.__del__()
        self.connector.__del__()
        self.queue.close()


    def close(self, event):
        self.__del__()


    def waitForInit(self):
        msgbox = QMessageBox(self)
        msgbox.setText("Initializing...")
        msgbox.show()
        while len(self.genrelist) == 0:
            self.getTags()
            time.sleep(0.1)
        msgbox.done(0)
        msgbox.destroy(True)
        LOGGER.info("Init done")
        self.setStatusTip("Init done!")
        self.compare.setEnabled(True)
        self.reload.setEnabled(True)
        self.more.setEnabled(True)


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
            if selector == "":
                self.selectorlist.remove(selector)
                self.toolbar.removeWidget(selector)
            elif selector not in self.fetchedAlbums.keys():
                comp.add(selector.currentData(0))
            else:
                self.albumlist.append(self.fetchedAlbums[selector])
        LOGGER.debug(comp)
        self.core.putFetchTagsToQ(comp)
        #self.core.fetchAlbumEvent.set()
        #check this condition in set intervals
        LOGGER.info("DONE")


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
        comp = set()
        for selector in self.selectorlist:
            comp.add(selector.currentData(0))
        LOGGER.debug(comp)
        self.albumlist = self.core.compare(comp, self.albumlist)
        self.updateLayout()
        LOGGER.info("%r" % self.albumlist)


    def getTags(self):
        LOGGER.info("Getting Tags from Core") # debug
        tags = self.core.returnTags()
        if tags is not None:
            for tag in tags:
                if tag is not "" and tag is not None:
                    self.genrelist.add(tag)


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
            LOGGER.debug("Adding Album %s" % album.name)
            btn = QPushButton("%s - %s" % (album.band, album.name))
            icn = QIcon() # see ref doc
            btn.setIcon(icn)
            btn.setIconSize(QSize(200, 200))
            self.btnlist.append(btn)
        else:
            LOGGER.error("Wanted to add %s, but it's not an Album")
            #self.updateLayout()


    def updateLayout(self):
        LOGGER.info("Refreshing Layout")
        for btn in self.btnlist:
            self.layout.removeWidget(btn)
        positions = [ (x,y) for x in range(int(len(self.btnlist)/5)) for y in range(5) ]
        for position, btn in zip(positions, self.btnlist):
            self.layout.addWidget(btn, *position)


    def syncCoreWithConnector(self):
        LOGGER.error("Timer done")


def __main__():
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    __main__()
