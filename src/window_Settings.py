import sys
from PyQt5 import QtWidgets, QtCore, QtGui, uic
from matplotlib.colors import to_hex
from os import path, getcwd

from backend.efio import getSysDefaultDir

import json

__location__ = path.realpath(path.join(getcwd(), path.dirname(__file__)))
wUi, wBase = uic.loadUiType(path.join(__location__, 'uiDesigns/SettingsWindow.ui')) # Load the .ui file

class localSettings(QtCore.QSettings):

    with open(path.join(__location__, './localSettings.default.json')) as jFile:
        default_jSetting = json.load(jFile)

    def __init__(self, testMode=False) -> None:
        super().__init__(QtCore.QSettings.IniFormat, QtCore.QSettings.UserScope,'EasyFlowQ', 'EasyFlowQ_v1')
        # print(self.format(), self.fileName(), sep='\t')
        self.testMode = testMode
    
    def __getitem__(self, key):
        qValue = self.value(key, defaultValue=self.default_jSetting[key])

        if self.testMode and (key == 'default dir'):
            return path.abspath('./demoSamples')

        if key in ["dot N in perf mode"]:
            return int(qValue)
        elif key in ["plot dpi scale", "version"]:
            return float(qValue)
        else:
            return qValue

    def __setitem__(self, key, value):
        self.setValue(key, value)

    def verEntryExists(self):
        if not self.contains('version'):
            self.setValue('version', self.default_jSetting['version'])
            return False
        return True

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

        self.dotNEdit.setValidator(QtGui.QIntValidator(int(100), int(1e6), self.dotNEdit))

        self.settings = localSettings()

        self.loadSettings()

        self.browsePB.clicked.connect(self.handle_Browse)
        self.OKPB.clicked.connect(self.handle_return)
        self.defaultPB.clicked.connect(self.handle_restoreDefault)

    def loadSettings(self):

        if path.isdir(self.settings['default dir']):
            self.dirEdit.setText(path.abspath(self.settings['default dir']))
        else:
            self.dirEdit.setText(getSysDefaultDir())

        self.dotNEdit.setText('{0:d}'.format(self.settings['dot N in perf mode']))
        self.dpiSpinBox.setValue(self.settings['plot dpi scale'])


    def handle_Browse(self):
        defaultDir = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select the default directory', './')
        if not defaultDir:
            return

        self.dirEdit.setText(defaultDir)

    def handle_return(self):

        self.settings['default dir'] = self.dirEdit.text()
        self.settings['dot N in perf mode'] = int(self.dotNEdit.text())
        self.settings['plot dpi scale'] = self.dpiSpinBox.value()

        self.newLocalSettingConfimed.emit(self.settings)
        self.close()

    def handle_restoreDefault(self):
        if path.isdir(self.settings.default_jSetting['default dir']):
            self.dirEdit.setText(path.abspath(self.settings.default_jSetting['default dir']))
        else:
            self.dirEdit.setText(getSysDefaultDir())

        self.dotNEdit.setText('{0:d}'.format(self.settings.default_jSetting['dot N in perf mode']))
        self.dpiSpinBox.setValue(self.settings.default_jSetting['plot dpi scale'])

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    settings = localSettings()
    sWindow = settingsWindow()
    sWindow.show()
    sys.exit(app.exec_())
    pass
