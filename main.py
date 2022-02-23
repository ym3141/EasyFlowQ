import sys
from PyQt5 import QtWidgets
from PyQt5.QtCore import QPoint
from mainWindow import mainUi

from multiprocessing import Process

from os import getpid

windowList = []

def newWindowFunc(sessionSaveFile=None, pos=None):
    app = QtWidgets.QApplication(sys.argv)
    mainW = mainUi(newWindowProc, sessionSaveFile=sessionSaveFile, pos=pos)

    windowList.append(mainW)
    mainW.show()
    sys.exit(app.exec_())

def newWindowProc(sessionSaveFile=None, pos=None):
    newProcess = Process(target=newWindowFunc, args=(sessionSaveFile, pos))
    newProcess.start()

if __name__ == "__main__":
    newWindowFunc()
