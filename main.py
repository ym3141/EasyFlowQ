import sys
from PyQt5 import QtWidgets
from PyQt5.QtCore import QPoint
from window_Main import mainUi
from os import path

from window_Settings import localSettings

from multiprocessing import Process

_excepthook = sys.excepthook
def myexcepthook(type, value, traceback):
    _excepthook(type, value, traceback)

def newWindowFunc(sessionSaveFile=None, pos=None):
    sys.excepthook = myexcepthook

    app = QtWidgets.QApplication(sys.argv)

    if path.exists('./localSettings.user.json'):
        # there is a user setting, load it
        setting = localSettings('./localSettings.user.json')
        mainW = mainUi(sessionSaveFile=sessionSaveFile, pos=pos, localSetting=setting)

    else:
        setting = localSettings('./localSettings.default.json')
        mainW = mainUi(sessionSaveFile=sessionSaveFile, pos=pos, localSetting=setting)
        mainW.handle_Settings(firstTime=True)

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
