from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sys
import time
import logging
from album import Album
from core import Core

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

#maybe it makes sense to let this be a subclass of threading of some sort
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.core = Core()
        self.core.start()
        self.layout = QGridLayout()
        self.widget = QWidget()
        self.widget.setMinimumSize(800, 600)
        self.widget.setLayout(self.layout)
        self.setCentralWidget(self.widget)
        self.setWindowTitle("RealBandcampMusicDisc0very")
        self.setGeometry(QRect(0, 0, 1280, 720))
        self.albumlist = set()
        self.genrelist = self.core.get_genres()
        self.btnlist = []
        self.selectorlist = []

        self.statusBar()
        self.initMenu()
        self.initToolbar()
        self.show()

    def __del__(self):
        self.core.__del__()

    def initToolbar(self):
        self.toolbar = self.addToolBar("Generic Foobar")

        self.compare = self.toolbar.addAction("compare noods")
        self.compare.triggered.connect(self.comparison)
        self.compare.setStatusTip("Compare!")

        self.reload = self.toolbar.addAction("fresh noods")
        self.reload.triggered.connect(self.refresh)
        self.reload.setStatusTip("Apply")

        self.more = self.toolbar.addAction("more noods")
        self.more.triggered.connect(self.add_genre_selector)
        self.more.setStatusTip("Add an additional Selector")

        self.add_genre_selector()

    def refresh(self):
        LOGGER.info("refreshing selection")
        comp = []
        for selector in self.selectorlist:
            if selector != "":
                comp.append(selector.currentData(0))
        LOGGER.debug(comp)
        self.core.refresh(self.updateAlbums, comp)
        
    def updateAlbums(self, albums):
        LOGGER.info("Updating Albums")
        self.albumlist.update(albums)
        for album in self.albumlist:
            self.add_album(album) 
        self.updateLayout()

    def comparison(self):
        comp = set()
        for selector in self.selectorlist:
            comp.add(selector.currentData(0))
        LOGGER.debug(comp)
        self.albumlist = self.core.compare(comp, self.albumlist)
        self.updateLayout()
        LOGGER.info("%r" % self.albumlist)


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

def __main__():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.updateLayout()
    sys.exit(app.exec_())

__main__()