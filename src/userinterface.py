""" class to display userinterface """

import sys
from math import ceil
import logging

from PyQt5.QtWidgets import QMainWindow, QGridLayout, QLayout, QWidget, QMessageBox, QAction, QComboBox, QCompleter, QToolButton, QApplication, QScrollArea
from PyQt5.QtCore import QTimer, QRect, QSortFilterProxyModel, QSize, Qt
from PyQt5.QtGui import QIcon, QPixmap

from album import Album
from webconnector import Connector
from messages import MsgGetTags, MsgPutFetchTags, MsgPutTags, MsgPutAlbums, MsgDownloadAlbums, MsgFinishedDownloads, MsgQuit, MsgPause
from messagehandler import MessageHandler


LOGGER = logging.getLogger('rbmd.ui')
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


class MainWindow(QMainWindow, MessageHandler):
    """ Class that refelcts the "main-window" """

    # pylint: disable=too-many-instance-attributes

    def __init__(self):
        """ init """
        MessageHandler.__init__(self)
        LOGGER.info("Self: %s", self)
        QMainWindow.__init__(self)
        LOGGER.info("Self: %s", self)

        self.connector = Connector(self.queue)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.msgcapture)
        self.timer.start(1000)

        self.layout = QGridLayout()
        self.layout.setSizeConstraint(QLayout.SetMinimumSize)
        self.widget = QWidget()
        self.widget.setMinimumSize(800, 600)
        self.widget.setLayout(self.layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarAlwaysOn)
        self.setCentralWidget(self.scroll_area)

        self.setWindowTitle("RealBandcampMusicDisc0very")
        self.setGeometry(QRect(0, 0, 1280, 720))
        self.albumlist = set()
        self.genrelist = set()
        self.btnlist = []
        self.selectorlist = []
        self.fetched_albums = {}
        LOGGER.info("Self: %s", self)

        self.closeEvent = self.close
        self.statusBar()
        self.firstloaded = True
        self.init_menu()
        self.init_toolbar()
        self.show()
        self.send(MsgGetTags(None))
        self.setStatusTip("Initializing...")
        self.msgbox = QMessageBox(self)
        self.msgbox.setText("Initializing...")
        self.msgbox.show()
        LOGGER.info("Self: %s", self)

    def __del__(self):
        """ del """
        MessageHandler.__del__(self)

    def close(self, event):
        """ injection func for closing ther window """
        self.send(MsgPause(None))
        self.send(MsgQuit(None))
        #LOGGER.debug("Close event:\n%s", event)
        self.__del__()


############################################## QWindow Props ##################################################

    def finalize_init(self):
        """ func to handle init finalization """
        self.msgbox.done(0)
        self.msgbox.destroy(True)
        self.clear.setEnabled(True)
        self.compare.setEnabled(True)
        self.reload.setEnabled(True)
        self.more.setEnabled(True)
        self.setStatusTip("Init done!")
        LOGGER.info("Init done")

    def show_download_finished(self):
        """ quick messagebox to notify user about finished downloads """
        self.msgbox.setText("Finished Downloading!")
        self.msgbox.setStandardButtons(QMessageBox.Ok)
        self.msgbox.button(QMessageBox.Ok).animateClick(3000)
        self.msgbox.show()
        self.setStatusTip("Downloads finished...")

    def init_toolbar(self):
        """ toolbar's init func"""
        self.toolbar = self.addToolBar("Toolbar")

        self.clear = self.toolbar.addAction("clear")
        self.clear.triggered.connect(self.clear_layout)
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

    def init_menu(self):
        """ func that defines menu capabilities """
        self.menu_bar = self.menuBar()
        self.help_menu = self.menu_bar.addMenu(" &Help")

        ###############MENU ACTIONS#################################
        ### Help ###
        self.save_action = QAction(" &Save", self)
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.setStatusTip("Save results to file")
        self.save_action.triggered.connect(self.save_to_file)

        self.help_action = QAction(" &Help", self)
        self.help_action.setShortcut("F1")
        self.help_action.setStatusTip("Show the help")
        self.help_action.triggered.connect(self.show_help)

        self.quit_action = QAction(" &Quit", self)
        self.quit_action.setShortcut("Crtl+Q")
        self.quit_action.setStatusTip("Quit this Application")
        self.quit_action.triggered.connect(self.quit_application)

        self.save_selected_action = QAction(" &Save selected", self)
        self.save_selected_action.setShortcut("Ctrl+Shift+S")
        self.save_selected_action.setStatusTip("Save selected to file")
        self.save_selected_action.triggered.connect(self.save_selected)

        self.download_selected_action = QAction(" &Download selected", self)
        self.download_selected_action.setShortcut("Ctrl+Shift+D")
        self.download_selected_action.setStatusTip("Download selected Albums")
        self.download_selected_action.triggered.connect(self.download_selected)

        self.help_menu.addAction(self.save_action)
        self.help_menu.addAction(self.save_selected_action)
        self.help_menu.addAction(self.download_selected_action)
        self.help_menu.addAction(self.help_action)
        self.help_menu.addAction(self.quit_action)
        ### Help End ###

        ### Pause ###
        self.pause_action = QAction(" &Pause", self)
        self.pause_action.setShortcut("Ctrl+P")
        self.pause_action.setStatusTip("Pause current fetch cycle")
        self.pause_action.triggered.connect(self.pause_fetch)
        self.menu_bar.addAction(self.pause_action)
        ### Pause End ###

    ### Menu Functions ###

    def save_to_file(self):
        """ saves current albums with tags to file """
        genre = ""
        for action in self.selectorlist:
            selector = self.toolbar.widgetForAction(action)
            genre = genre + " " + selector.currentData(0) + " #"
        with open("save.txt", "a") as save:
            save.write("\n##################%s#################\n" % genre)
            for album in self.albumlist:
                save.write("%s - %s\t%s\n" %
                           (album.band, album.name, album.url))
        self.setStatusTip("Data saved to file!")

    def save_selected(self):
        """ saves current albums with tags to file """
        albums = []
        for child in self.widget.children():
            LOGGER.debug(child)
            if isinstance(child, QToolButton):
                if child.isChecked():
                    albums.append(child.statusTip())
        genre = ""
        LOGGER.debug(albums)
        for action in self.selectorlist:
            selector = self.toolbar.widgetForAction(action)
            genre = genre + " " + selector.currentData(0) + " #"
        with open("save.txt", "a") as save:
            save.write("\n##################%s#################\n" % genre)
            LOGGER.info("Saving to file")
            for metaalbum in albums:
                for album in self.albumlist:
                    LOGGER.error("%s\t%s", metaalbum, album.__str__())
                    if metaalbum == album.__str__():
                        save.write("%s - %s\t%s\n" %
                                   (album.band, album.name, album.url))
        self.setStatusTip("Selected saved to file!")

    def download_selected(self):
        """ Downloads selected albums """
        albums = []
        for child in self.widget.children():
            LOGGER.debug(child)
            if isinstance(child, QToolButton):
                if child.isChecked():
                    albums.append(child.statusTip())
        downloadlist = []
        for metaalbum in albums:
            for album in self.albumlist:
                if metaalbum == album.__str__():
                    downloadlist.append(album)
        self.send(MsgDownloadAlbums(downloadlist))
        self.setStatusTip("Downloading Albums!")

    def pause_fetch(self):
        self.send(MsgPause(None))
        self.setStatusTip("Aborting fetch cycle...")

    def quit_application(self):  # implement this
        """ quit """
        print("####################################Quit!############################################")

    def show_help(self):  # implement this
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
            if selector.currentData(0) in self.fetched_albums.keys():
                self.albumlist.update(
                    self.fetched_albums[selector.currentData(0)])
            elif selector.currentData(0) == "None":
                self.toolbar.removeAction(action)
                self.selectorlist.remove(action)
            else:
                comp.add(selector.currentData(0))
        LOGGER.debug(comp)
        self.send(MsgPutFetchTags(data=comp))
        self.setStatusTip("Fetching Albums...")
        self.update_layout()

    def comparison(self):
        """ compares based on current selectors """
        self.setStatusTip("Comparing Albums...")
        comp = set()
        for action in self.selectorlist:
            selector = self.toolbar.widgetForAction(action)
            comp.add(selector.currentData(0))
        LOGGER.debug(comp)
        compareset = set()
        for album in self.albumlist:
            if comp.issubset(album.genre):
                compareset.add(album)
                LOGGER.debug("Added %s after comparison", album.name)
        self.albumlist = compareset
        self.update_layout()
        self.setStatusTip("Comparison done!")

    def process_albums(self, msg):
        """ parses albums from msg and distributes them to corresponding structures """
        albumsdict = msg.data
        for key, value in albumsdict.items():
            if key in self.fetched_albums.keys():
                albumsfetched = self.fetched_albums[key]
                albumsfetched.update(value)
                self.fetched_albums[key] = albumsfetched
            else:
                self.fetched_albums[key] = value
            self.albumlist.update(value)
        self.update_layout()

    def add_genre_selector(self):
        """ creates a dropdown QComboBox """
        tempcombobox = QComboBox(parent=self)
        tempcombobox.setEditable(True)
        tempcombobox.setInsertPolicy(3)
        compfilter = QSortFilterProxyModel(tempcombobox)
        compfilter.setFilterCaseSensitivity(Qt.CaseInsensitive)
        compfilter.setFilterKeyColumn(1)
        compfilter.setSourceModel(tempcombobox.model())
        comp = QCompleter(compfilter, tempcombobox)
        comp.setCaseSensitivity(Qt.CaseInsensitive)
        comp.setCompletionMode(QCompleter.PopupCompletion)
        comp.setFilterMode(Qt.MatchContains)
        tempcombobox.setCompleter(comp)
        tempcombobox.addItems(self.genrelist)
        self.selectorlist.append(self.toolbar.addWidget(tempcombobox))

    def add_album(self, album):
        """ creates an album button """
        if isinstance(album, Album):
            btn = QToolButton()
            btn.setText("Artist: %s\nAlbum: %s" % (album.band, album.name))
            btn.setStatusTip("%s - %s" % (album.band, album.name))
            pix = QPixmap()
            pix.loadFromData(album.cover)
            btn.setIcon(QIcon(pix))
            btn.setIconSize(QSize(200, 200))
            btn.setMaximumWidth(225)
            btn.setFixedWidth(250)
            btn.setCheckable(True)
            btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            LOGGER.debug("Adding Album %s", album.name)
            self.btnlist.append(btn)
        else:
            LOGGER.error("Wanted to add %s, but it's not an Album", album)

    def clear_layout(self):
        """ clears current layout """
        self.albumlist = set()
        self.update_layout()

    def update_layout(self):
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

        positions = [(x, y) for x in range(int(ceil(len(self.btnlist)/5)))
                     for y in range(1, 6)]
        for position, btn in zip(positions, self.btnlist):
            self.layout.addWidget(btn, *position)

    def msgcapture(self):
        """ RUN """
        self.analyze(self.recieve())

    def analyze(self, msg):
        """ generic "callback" to check msgs and set flags and call functions """
        if msg != None:
            if isinstance(msg, MsgPutTags):
                self.store_tags_from_msg(msg)
                self.finalize_init()
            elif isinstance(msg, MsgPutAlbums):
                self.process_albums(msg)
            elif isinstance(msg, MsgFinishedDownloads):
                self.show_download_finished()
            else:
                LOGGER.debug("Unused Message:\n%s", msg)

    def store_tags_from_msg(self, msg):
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
