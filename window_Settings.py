import sys
from PyQt5 import QtWidgets, QtCore, QtGui, uic
from matplotlib.colors import to_hex
from os import path

import pandas as pd
import numpy as np
from src.qtModels import pandasTableModel

import json

wUi, wBase = uic.loadUiType('./uiDesigns/settingsWindow.ui') # Load the .ui file

userSettingDir = './localSettings.user.json'
defaultSettingDir = './localSettings.default.json'

class settingsWindow(wUi, wBase):
    def __init__(self) -> None:

        wBase.__init__(self)
        self.setupUi(self)

        self.dotNEdit.setValidator(QtGui.QIntValidator(100, 1e6, self.dotNEdit))

        if path.exists(userSettingDir):
            with open(userSettingDir) as jFile:
                jSettings = json.load(jFile)
        else:
            with open(defaultSettingDir) as jFile:
                jSettings = json.load(jFile)

        self.jsonLoadSettings(jSettings)

        self.browsePB.clicked.connect(self.handle_Browse)
        self.OKPB.clicked.connect(self.handle_return)
        self.defaultPB.clicked.connect(self.handle_restoreDefault)

    def jsonLoadSettings(self, jSettings):
        if path.isdir(jSettings['defaultDir']):
            self.dirEdit.setText(path.abspath(jSettings['defaultDir']))
        else:
            self.dirEdit.setText(path.abspath('./'))

        self.dotNEdit.setText('{0:d}'.format(jSettings['dotNinPerf']))
        self.dpiSpinBox.setValue(jSettings['plotDpiScale'])


    def handle_Browse(self):
        defaultDir = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select the default directory', './')

        if not defaultDir:
            return

        self.dirEdit.setText(defaultDir)

    def handle_return(self):
        pass

    def handle_restoreDefault(self):
        pass

if __name__ == '__main__':
    pass