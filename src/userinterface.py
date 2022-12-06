""" class to display userinterface """

import sys
from math import ceil
from hashlib import sha256
from datetime import datetime
from multiprocessing import freeze_support


from PySide6.QtWidgets import QMainWindow, QGridLayout, QLayout, QWidget, QMessageBox, QComboBox, QCompleter, QToolButton, QApplication, QScrollArea
from PySide6.QtCore import QTimer, QRect, QSortFilterProxyModel, QSize, Qt
from PySide6.QtGui import QIcon, QAction, QPixmap

from helpers import safety_wrapper, HLogger
from album import Album
from webconnector import Connector
from messages import MsgGetTags, MsgPutFetchTags, MsgPutTags, MsgPutAlbums, MsgDownloadAlbums, MsgFinishedDownloads, MsgPause, MsgQuit
from messagehandler import MessageHandler

LOGGER = HLogger(name="rbmd.ui")

class MainWindow(QMainWindow):
    """ Class that refelcts the "main-window" """

    # pylint: disable=too-many-instance-attributes
    @safety_wrapper
    def __init__(self):
        """ init """
        super().__init__()
        port = MessageHandler.checkPortFree(10666)
        authkey = bytes(sha256(str(datetime.now()).encode()).hexdigest(), encoding="utf-8")
        connParams = {"address": "127.0.0.1", "port": port, "key": authkey}
        self.messagehandler = MessageHandler(connParams)
        LOGGER.debug(f"Self: {self}")

        self.connector = Connector(connectionParams=connParams)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.msgcapture)
        self.timer.start(100)  

        self.layout = QGridLayout()
        self.layout.setSizeConstraint(QLayout.SetMinimumSize)
        self.widget = QWidget()
        self.widget.setMinimumSize(800, 700)
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
        
        self.tagTimer = QTimer(self)
        self.tagTimer.timeout.connect(self.getTags)
        self.tagTimer.setSingleShot(True)
        self.tagTimer.start(1000)
        self.closeEvent = self.close
        self.statusBar()
        self.firstloaded = True
        self.init_menu()
        self.init_toolbar()
        self.show()
        self.setStatusTip("Initializing...")
        self.msgbox = QMessageBox(self)
        self.msgbox.setText("Initializing...")
        self.msgbox.show()
        LOGGER.debug(f"Init done...")

    @safety_wrapper
    def __del__(self):
        """ del """
        self.messagehandler.__del__()

    @safety_wrapper
    def close(self, event):
        """ injection func for closing ther window """
        # display "shutting down..." window
        self.messagehandler.send(MsgQuit(None))
        LOGGER.debug(f"Close event:\n{event}")
        self.__del__()


############################################## QWindow Props ##################################################

    @safety_wrapper
    def getTags(self):
        """"""
        if self.messagehandler.isConnected():
            self.messagehandler.send(MsgGetTags(None))
            self.tagTimer.setSingleShot(False)

    @safety_wrapper
    def finalize_init(self):
        """ func to handle init finalization """
        self.msgbox.done(0)
        self.msgbox.destroy(True)
        self.clear.setEnabled(True)
        self.compare.setEnabled(True)
        self.reload.setEnabled(True)
        self.more.setEnabled(True)
        self.setStatusTip("Init done!")
        LOGGER.debug("Init done")

    @safety_wrapper
    def show_download_finished(self):
        """ quick messagebox to notify user about finished downloads """
        self.msgbox.setText("Finished Downloading!")
        self.msgbox.setStandardButtons(QMessageBox.Ok)
        self.msgbox.button(QMessageBox.Ok).animateClick()
        self.msgbox.show()
        self.setStatusTip("Downloads finished...")

    @safety_wrapper
    def init_toolbar(self):
        """ toolbar's init func"""
        self.toolbar = self.addToolBar("Toolbar")

        self.clear = self.toolbar.addAction("clear")
        self.clear.triggered.connect(self.clear_layout)
        self.clear.setStatusTip("Clear All")
        self.clear.setEnabled(False)

        self.compare = self.toolbar.addAction("Compare")
        self.compare.triggered.connect(self.comparison)
        self.compare.setStatusTip("Compare!")
        self.compare.setEnabled(False)

        self.reload = self.toolbar.addAction("Refresh")
        self.reload.triggered.connect(self.refresh)
        self.reload.setStatusTip("Apply")
        self.reload.setEnabled(False)

        self.more = self.toolbar.addAction("Add Selector")
        self.more.triggered.connect(self.add_genre_selector)
        self.more.setStatusTip("Add an additional Selector")
        self.more.setEnabled(False)

    @safety_wrapper
    def init_menu(self):
        """ func that defines menu capabilities """
        self.menu_bar = self.menuBar()

        ###############MENU ACTIONS#################################
        ### Quit ###
        self.quit_action = QAction(" &Quit", self)
        self.quit_action.setShortcut("Crtl+Q")
        self.quit_action.setStatusTip("Quit this Application")
        self.quit_action.triggered.connect(self.quit_application)
        self.menu_bar.addAction(self.quit_action)

        ### Help ###
        self.help_action = QAction(" &Help", self)
        self.help_action.setShortcut("F1")
        self.help_action.setStatusTip("Show the help")
        self.help_action.triggered.connect(self.show_help)
        self.menu_bar.addAction(self.help_action)

        ### Save All ###
        self.save_action = QAction(" &Save", self)
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.setStatusTip("Save results to file")
        self.save_action.triggered.connect(self.save_to_file)
        self.menu_bar.addAction(self.save_action)

        ### Save Selected ###
        self.save_selected_action = QAction(" &Save selected", self)
        self.save_selected_action.setShortcut("Ctrl+Shift+S")
        self.save_selected_action.setStatusTip("Save selected to file")
        self.save_selected_action.triggered.connect(self.save_selected)
        self.menu_bar.addAction(self.save_selected_action)

        ### Download Selected ###
        self.download_selected_action = QAction(" &Download selected", self)
        self.download_selected_action.setShortcut("Ctrl+Shift+D")
        self.download_selected_action.setStatusTip("Download selected Albums")
        self.download_selected_action.triggered.connect(self.download_selected)
        self.menu_bar.addAction(self.download_selected_action)

        ### Pause ###
        self.pause_action = QAction(" &Pause", self)
        self.pause_action.setShortcut("Ctrl+P")
        self.pause_action.setStatusTip("Pause current fetch cycle")
        self.pause_action.triggered.connect(self.pause_fetch)
        self.menu_bar.addAction(self.pause_action)

    @safety_wrapper
    def save_to_file(self):
        """ saves current albums with tags to file """
        genre = ""
        for action in self.selectorlist:
            selector = self.toolbar.widgetForAction(action)
            genre = f"{genre} {selector.currentData(0)} x"
        with open("save.txt", "a") as save:
            save.write(f"\n################## All:{genre}#################\n")
            for album in self.albumlist:
                save.write(f"{album.band} - {album.name}\t{album.url}\n")
        self.setStatusTip("Data saved to file!")

    @safety_wrapper
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
            genre = f"{genre} {selector.currentData(0)} x"
        genre = genre.rstrip("x")
        with open("save.txt", mode="a", encoding="utf-8") as save:
            save.write(f"\n################## Selection:{genre}#################\n")
            LOGGER.debug("Saving to file")
            for metaalbum in albums:
                for album in self.albumlist:
                    if metaalbum == album.__str__():
                        save.write(f"{album.band} - {album.name}\n\t{album.url}\n")
        self.setStatusTip("Selected saved to file!")

    @safety_wrapper
    def download_selected(self):
        """ Downloads selected albums """
        LOGGER.debug(f"Downloading selected Albums")
        albums = []
        for child in self.widget.children():
            if isinstance(child, QToolButton):
                if child.isChecked():
                    albums.append(child.statusTip())
        downloadlist = []
        for metaalbum in albums:
            for album in self.albumlist:
                if metaalbum == album.__str__():
                    downloadlist.append(album)
        self.messagehandler.send(MsgDownloadAlbums(downloadlist))
        self.setStatusTip("Downloading Albums!")

    @safety_wrapper
    def pause_fetch(self):
        self.messagehandler.send(MsgPause(None))
        self.setStatusTip("Aborting fetch cycle...")

    @safety_wrapper
    def quit_application(self):  # implement this
        """ quit """
        print("####################################Quit!############################################")

    @safety_wrapper
    def show_help(self):  # implement this
        """ help """
        print("####################################Help!############################################")

# WIP - add help menu that displays infos about the "program" and an updater button

########################################## End QWindow Props ##################################################
############################################## Logikz #########################################################

    @safety_wrapper
    def refresh(self):
        """ func to grab albums based on current selectors """
        LOGGER.debug("refreshing selection")
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
        self.messagehandler.send(MsgPutFetchTags(data=comp))
        self.setStatusTip("Fetching Albums...")
        self.update_layout()

    @safety_wrapper
    def comparison(self):
        """ compares based on current selectors """
        self.setStatusTip("Comparing Albums...")
        comp = set()
        for action in self.selectorlist:
            selector = self.toolbar.widgetForAction(action)
            comp.add(selector.currentData(0))
        LOGGER.debug(comp)
        compareset = set()
        # for album in self.albumlist: #set().intersection lambda key: comp.issubset(album.genre)
        for album in self.albumlist:
            if comp.issubset(album.genre):
                compareset.add(album)
                LOGGER.debug(f"Added {album.name} after comparison")
        self.albumlist = compareset
        self.update_layout()
        self.setStatusTip("Comparison done!")

    @safety_wrapper
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

    @safety_wrapper
    def add_genre_selector(self):
        """ creates a dropdown QComboBox """
        tempcombobox = QComboBox(parent=self)
        tempcombobox.setEditable(True)
        tempcombobox.setInsertPolicy(QComboBox.InsertPolicy.InsertAtBottom)
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

    @safety_wrapper
    def add_album(self, album):
        """ creates an album button """
        if isinstance(album, Album):
            btn = QToolButton()
            btn.setText(f"Artist: {album.band}\nAlbum: {album.name}")
            btn.setStatusTip(f"{album.band} - {album.name}")
            if album.cover:
                pix = QPixmap()
                pix.loadFromData(album.cover)
                icn = QIcon(pix)
                btn.setIcon(icn)
                btn.setIconSize(QSize(200, 200))
            btn.setMaximumWidth(250)
            btn.setFixedWidth(250)
            btn.setCheckable(True)
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            LOGGER.debug(f"Adding Album {album.name}")
            self.btnlist.append(btn)
        else:
            LOGGER.error(f"Wanted to add {album}, but it's not an Album")

    @safety_wrapper
    def clear_layout(self):
        """ clears current layout """
        self.albumlist = set()
        self.update_layout()

    @safety_wrapper
    def update_layout(self):
        """ refreshes/updates current layout and adds all the albums to the layout """
        LOGGER.debug("Refreshing Layout")

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

    @safety_wrapper
    def msgcapture(self):
        """ RUN """
        self.analyze(self.messagehandler.recieve())

    @safety_wrapper
    def analyze(self, msg):
        """ generic "callback" to check msgs and set flags and call functions """
        if msg:
            if isinstance(msg, MsgPutTags):
                self.store_tags_from_msg(msg)
                self.finalize_init()
            elif isinstance(msg, MsgPutAlbums):
                self.process_albums(msg)
            elif isinstance(msg, MsgFinishedDownloads):
                self.show_download_finished()
            else:
                LOGGER.error(f"Unknown Message:\n{msg}")

    @safety_wrapper
    def store_tags_from_msg(self, msg):
        """ stores default tags from msg """
        if msg.data is not None:
            self.genrelist = msg.data


############################################## End Logikz #####################################################

def __main__():
    """ main """
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    freeze_support()
    __main__()
