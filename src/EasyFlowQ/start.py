import sys
import platform
from os import path, chdir, environ

# detect what mode this program is running
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    chdir(sys._MEIPASS)
    print('running in a PyInstaller bundle')
else:
    print('running in a normal Python process')



from PySide6 import QtWidgets, QtCore, QtGui
from .window_Main import mainUi
from .window_Settings import localSettings
from . import __version__

from multiprocessing import Process, freeze_support
from traceback import format_exception

import argparse

import pandas as pd
import numpy as np
import matplotlib

print('Python version:', platform.python_version())
print('PySide6 version:', QtCore.__version__)
print('Matplotlib version:', matplotlib.__version__)
print('pandas version:', pd.__version__)
print('numpy version:', np.__version__)
print('EasyFlowQ version:', __version__)


# set up the excepthook so unhandled exception won't crash the program
_excepthook = sys.excepthook
def myexcepthook(type, value, traceback):
    except_msg = ''.join(format_exception(type, value, traceback))
    msgBox = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Critical, 'Unexpected exception',
                                   'A unexpected exception cncountered! \n\nThis likely won\'t crash EasyFlowQ, but we recommend save a copy of the session, and restart if anything looks off',
                                   QtWidgets.QMessageBox.Ok, None)
    msgBox.setDetailedText(except_msg)
    msgBox.exec_()

    _excepthook(type, value, traceback)

def newWindowFunc(sessionSaveFile=None, pos=None):
    sys.excepthook = myexcepthook
    freeze_support()

    app = QtWidgets.QApplication(sys.argv)

    # if sys.platform == "darwin":
    #     app.setAttribute(QtGui.Qt.ApplicationAttribute.AA_DontUseNativeMenuBar)

    # Force fusion style so that UI are consistant between different plateforms
    if 'Fusion' in QtWidgets.QStyleFactory.keys():
        app.setStyle('Fusion')

    settings = localSettings()
    mainW = mainUi(settings, sessionSaveFile=sessionSaveFile, pos=pos)
    mainW.requestNewWindow.connect(newWindowProc)
    mainW.show()

    if not settings.verEntryExists():
        mainW.handle_Settings(firstTime=True)

    sys.exit(app.exec())

def newWindowProc(sessionSaveFile, pos):

    if sessionSaveFile == '':
        sessionSaveFile = None

    newProcess = Process(target=newWindowFunc, args=(sessionSaveFile, pos))
    newProcess.start()

def startGUI():

    parser = argparse.ArgumentParser(prog='EasyFlowQ', description='Start EasyFlowQ')
    parser.add_argument('--version', action='version', help='Show the version number and exit', version='%(prog)s ' + __version__)
    parser.add_argument('--session', type=str, help='The session file to open when start the program')
    args = parser.parse_args()

    if args.session:
        sessionSaveFile = args.session
        newWindowFunc(sessionSaveFile=sessionSaveFile)
    else:
        newWindowFunc()

if __name__ == "__main__":
    newWindowFunc()
