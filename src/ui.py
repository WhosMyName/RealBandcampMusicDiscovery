from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sys
import time
from album import Album

#maybe it makes sense to let this a subclass of some sort
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.layout = QGridLayout()
        self.widget = QWidget()
        self.widget.setMinimumSize(800, 600)
        self.widget.setLayout(self.layout)
        self.setCentralWidget(self.widget)
        self.setWindowTitle("RealBandcampMusicDisc0very")
        self.setGeometry(QRect(0, 0, 1280, 720))
        self.albumlist = set()
        self.btnlist = []
        self.show()

    #da gud shit
    #add toolbar
    #add dynamic drop-downs (list?) - qwq
    #add btn for more filters
    #add content to those lists
    #eval
    #def add_

    def add_album(self, album):
        if isinstance(album, Album):
            btn = QPushButton("%s - %s" % (album.band, album.name))
            icn = QIcon() # see ref doc
            btn.setIcon(icn)
            btn.setIconSize(QSize(200, 200))
            self.btnlist.append(btn)
            self.updateLayout()

    def updateLayout(self):
        for btn in self.btnlist:
            self.layout.removeWidget(btn)
        positions = [ (x,y) for x in range(int(len(self.btnlist)/5)) for y in range(5) ]
        for position, btn in zip(positions, self.btnlist):
            self.layout.addWidget(btn, *position)

def __main__():
    app = QApplication(sys.argv)
    window = MainWindow()
    for num in range(0, 15):
        window.btnlist.append(QPushButton(str(num)))
    window.updateLayout()
    sys.exit(app.exec_())

__main__()