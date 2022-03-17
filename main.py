import sys
from PyQt5 import QtWidgets
from PyQt5.QtCore import QPoint
from window_Main import mainUi

from multiprocessing import Process

def newWindowFunc(sessionSaveFile=None, pos=None):
    app = QtWidgets.QApplication(sys.argv)
    mainW = mainUi(sessionSaveFile=sessionSaveFile, pos=pos)
    mainW.requestNewWindow.connect(newWindowProc)

    mainW.show()
    sys.exit(app.exec_())

def newWindowProc(sessionSaveFile, pos):

    if sessionSaveFile == '':
        sessionSaveFile = None

    newProcess = Process(target=newWindowFunc, args=(sessionSaveFile, pos))
    newProcess.start()

if __name__ == "__main__":
    newWindowFunc()
