import sys
from PyQt5 import QtWidgets, QtCore, QtGui, uic
from matplotlib.colors import to_hex
from os import path

from src.efio import getSysDefaultDir

import json

wUi, wBase = uic.loadUiType('./uiDesigns/settingsWindow.ui') # Load the .ui file

userSettingDir = './localSettings.user.json'
defaultSettingDir = './localSettings.default.json'

class localSettings:
    def __init__(self, jsonDir) -> None:
        with open(jsonDir) as jFile:
            jSettings = json.load(jFile)

        self.settingDict = jSettings
    
    def saveToUserJson(self, parentWedget=None):
        try:
            with open(userSettingDir, 'w+') as f:
                json.dump(self.settingDict, f, sort_keys=True, indent=4)
                pass
        except PermissionError:
            QtWidgets.QMessageBox.warning(parentWedget, 'Permission Error', 
                                          'Cannot write settings to the directory. It is likely you do not have permission to write to the directory. \n \
                                           Settings that does not require restart are applied, but will lost on when you restart')
        
        except Exception:
            QtWidgets.QMessageBox.warning(parentWedget, 'Unknown Error', 
                                          'Unknown error encountered while writting the settings. It is likely you do not have permission to write to the directory. \n \
                                           Settings that does not require restart are applied, but will lost on when you restart')


class settingsWindow(wUi, wBase):
    newLocalSettingConfimed = QtCore.pyqtSignal(localSettings)

    def __init__(self, firstTime=False) -> None:

        wBase.__init__(self)
        self.setupUi(self)

        if firstTime:
            self.firstTimeMsg.setVisible(True)
            self.resize(self.size().width(), 330)

            self.setWindowTitle(self.windowTitle() + ' - First time setup!')
        else:
            self.firstTimeMsg.setVisible(False)

        self.dotNEdit.setValidator(QtGui.QIntValidator(100, 1e6, self.dotNEdit))

        if path.exists(userSettingDir):
            self.settings = localSettings(userSettingDir)
        else:
            self.settings = localSettings(defaultSettingDir)

        self.jsonLoadSettings()

        self.browsePB.clicked.connect(self.handle_Browse)
        self.OKPB.clicked.connect(self.handle_return)
        self.defaultPB.clicked.connect(self.handle_restoreDefault)

    def jsonLoadSettings(self):
        jSettings = self.settings.settingDict

        if path.isdir(jSettings['default dir']):
            self.dirEdit.setText(path.abspath(jSettings['default dir']))
        else:
            self.dirEdit.setText(getSysDefaultDir())

        self.dotNEdit.setText('{0:d}'.format(jSettings['dot N in perf mode']))
        self.dpiSpinBox.setValue(jSettings['plot dpi scale'])


    def handle_Browse(self):
        defaultDir = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select the default directory', './')

        if not defaultDir:
            return

        self.dirEdit.setText(defaultDir)

    def handle_return(self):

        self.settings.settingDict['default dir'] = self.dirEdit.text()
        self.settings.settingDict['dot N in perf mode'] = int(self.dotNEdit.text())
        self.settings.settingDict['plot dpi scale'] = self.dpiSpinBox.value()

        self.settings.saveToUserJson(parentWedget = self)

        self.newLocalSettingConfimed.emit(self.settings)
        self.close()

    def handle_restoreDefault(self):
        self.settings = localSettings(defaultSettingDir)
        self.jsonLoadSettings()
        pass

if __name__ == '__main__':
    pass