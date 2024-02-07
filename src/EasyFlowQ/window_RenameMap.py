import sys
from PyQt5 import QtWidgets, QtCore, QtGui, uic
from matplotlib.colors import to_hex
from os import path, getcwd

import pandas as pd
import numpy as np
from .backend.qtModels import pandasTableModel

__location__ = path.realpath(path.join(getcwd(), path.dirname(__file__)))
wUi, wBase = uic.loadUiType(path.join(__location__, 'uiDesigns/RenameWindow_Map.ui')) # Load the .ui file

class renameWindow_Map(wUi, wBase):
    renameConfirmed = QtCore.pyqtSignal(dict)

    def __init__(self, dir4Save, smplNameList) -> None:
        wBase.__init__(self)
        self.setupUi(self)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        
        self.smplNameList = smplNameList
        self.fileRoot = dir4Save
        self.renameTableModel = pandasTableModel(pd.DataFrame())

        self.renamePB.clicked.connect(self.handle_renameConfirm)
        self.reloadPB.clicked.connect(self.handle_reloadXlsx)

    def showEvent(self, event):
        openFileDir, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Load xlsx file for renaming', self.fileRoot, filter='*.xlsx')
        if not openFileDir:
            return

        self.loadRenameFile(openFileDir)

    def handle_renameConfirm(self):
        renameDict = dict()
        for idx, row in self.renameTableModel.dfData.iterrows():
            if row['Old names'] in renameDict:
                pass
            else:
                renameDict[row['Old names']] = row['New names']
                pass

        self.renameConfirmed.emit(renameDict)
        self.close()

    def handle_reloadXlsx(self):
        openFileDir, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Load xlsx file for renaming', self.fileRoot, filter='*.xlsx')
        if not openFileDir:
            return

        self.loadRenameFile(openFileDir)

    def loadRenameFile(self, renamingFileDir):

        renamesInput = pd.read_excel(renamingFileDir, header=None).iloc[:, 0:2]
        renamesInput.fillna('').astype(str)
        renamesInput.columns = ['smplName', 'smplRename']

        renames = pd.DataFrame(columns=['Old names', 'New names'])

        for smplName in self.smplNameList:
            matches = renamesInput.loc[renamesInput['smplName'] == smplName]
            if matches.shape[0] == 0:
                renames.loc[renames.shape[0]] = [smplName, smplName]
            else:
                renames.loc[renames.shape[0]] = [smplName, matches['smplRename'].iloc[0]]

        self.renameTableModel = pandasTableModel(renames)
        self.tableView1.setModel(self.renameTableModel)
        pass


def findDups(renamePlates):
    renames = np.vstack([renamePlate.iloc[0:8].to_numpy() for renamePlate in renamePlates])
    allNameFlat = list(renames.flatten())
    allNameFlat = list(filter(lambda x: x!='', allNameFlat))
    duplicates = set([name for name in allNameFlat if allNameFlat.count(name) > 1])

    return duplicates

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = renameWindow_Map(dir4Save='./demoSamples', 
                             smplNameList=['01-Well-A10', '01-Well-A3', '01-Well-B3', '01-Well-C5', '01-Well-D12', '01-Well-E2','01-Well-H7'])
    window.show()
    sys.exit(app.exec_())