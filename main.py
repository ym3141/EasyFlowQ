import sys
from os import path, chdir, environ

# detect what mode this program is running
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    chdir(sys._MEIPASS)
    print('running in a PyInstaller bundle')
else:
    print('running in a normal Python process')

from PyQt5 import QtWidgets, QtCore
from window_Main import mainUi

from window_Settings import localSettings

from multiprocessing import Process
from traceback import format_exception

# set up the excepthook so unhandled exception won't crash the program
_excepthook = sys.excepthook
def myexcepthook(type, value, traceback):
    except_msg = ''.join(format_exception(type, value, traceback))
    QtWidgets.QMessageBox.critical(None, 'Unexpected exception encountered', 
        '{0} \n\nThis likely won\'t crash EasyFlowQ, but we recommend save a copy of the session, and restart if anything looks off'.format(except_msg))
    _excepthook(type, value, traceback)

def newWindowFunc(sessionSaveFile=None, pos=None):
    sys.excepthook = myexcepthook

    app = QtWidgets.QApplication(sys.argv)
    # app.setAttribute(QtCore.Qt.AA_DisableHighDpiScaling, True)

    settings = localSettings()
    mainW = mainUi(settings, sessionSaveFile=sessionSaveFile, pos=pos)
    mainW.requestNewWindow.connect(newWindowProc)
    mainW.show()

    if not settings.verEntryExists():
        mainW.handle_Settings(firstTime=True)

    sys.exit(app.exec_())

def newWindowProc(sessionSaveFile, pos):

    if sessionSaveFile == '':
        sessionSaveFile = None

    newProcess = Process(target=newWindowFunc, args=(sessionSaveFile, pos))
    newProcess.start()

if __name__ == "__main__":
    newWindowFunc()
