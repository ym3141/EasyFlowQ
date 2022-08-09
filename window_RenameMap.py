import sys
from PyQt5 import QtWidgets, QtCore, QtGui, uic
from matplotlib.colors import to_hex
from os import path

import pandas as pd
import numpy as np
from src.qtModels import pandasTableModel

import re

wUi, wBase = uic.loadUiType('./uiDesigns/RenameWindow_Map.ui') # Load the .ui file

class renameWindow_Map(wUi, wBase):
    renameConfirmed = QtCore.pyqtSignal(dict)

    def __init__(self, dir4Save, smplNameList) -> None:
        wBase.__init__(self)
        self.setupUi(self)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        
        self.smplNameList = smplNameList
        self.fileRoot = path.dirname(dir4Save)

        self.renamePB.clicked.connect(self.handle_renameConfirm)
        self.reloadPB.clicked.connect(self.handle_reloadXlsx)

    def showEvent(self, event):
        openFileDir, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Load xlsx file for renaming', self.fileRoot, filter='*.xlsx')
        if not openFileDir:
            return

        self.loadRenameFile(openFileDir)

    def handle_renameConfirm(self):
        renameDict = dict()
        for name, splitName in zip(self.smplNameList, self.splitNames):
            if name in renameDict:
                pass
            elif (self.renameTableModel._data.loc[splitName[1], splitName[2]]):
                renameDict[name] = self.renameTableModel._data.loc[splitName[1], splitName[2]]
            else:
                pass

        self.renameConfirmed.emit(renameDict)
        self.close()

    def handle_reloadXlsx(self):
        openFileDir, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Load xlsx file for renaming', self.fileRoot, filter='*.xlsx')
        if not openFileDir:
            return

        self.loadRenameFile(openFileDir)

    def loadRenameFile(self, renamingFileDir):

        renames = pd.read_excel(renamingFileDir, header=None).iloc[:, 0:2]
        renames.fillna('').astype(str)
        # duplicates = findDups(renames)
        # dupColorMaps = colorByDuplicates(renames, duplicates)
        # smplColorMaps = colorBySmplNames(renames, self.splitNames)

        self.renameTableModel = pandasTableModel(renames)
        self.tableView1.setModel(self.renameTableModel)
        pass

def exel2renameTable(renamingFileDir, smplNameList):
    names = pd.read_excel(renamingFileDir, header=None)

    return names.iloc[:, 0:2]

def findDups(renamePlates):
    renames = np.vstack([renamePlate.iloc[0:8].to_numpy() for renamePlate in renamePlates])
    allNameFlat = list(renames.flatten())
    allNameFlat = list(filter(lambda x: x!='', allNameFlat))
    duplicates = set([name for name in allNameFlat if allNameFlat.count(name) > 1])

    return duplicates


def colorByDuplicates(renamePlates, duplicats):
    colorPlates = []
    for renamePlate in renamePlates:
        colorPlate = pd.DataFrame().reindex_like(renamePlate)
        colorPlate.fillna(to_hex('k'), inplace=True)

        dupMap = renamePlate.applymap(lambda x : x in duplicats)
        colorPlate[dupMap] = to_hex('tab:red')
        colorPlate.loc['Legend', 2] = to_hex('tab:red')

        colorPlates.append(colorPlate)

    return colorPlates

def colorBySmplNames(renamePlates, splitNames):
    colorPlates = []
    for renamePlate in renamePlates:
        colorPlate = pd.DataFrame().reindex_like(renamePlate)
        colorPlate.fillna(to_hex('w'), inplace=True)

        colorPlate.loc['Legend', 1] = to_hex('xkcd:very light green')
        colorPlates.append(colorPlate)

    for splitName in splitNames:
        plateN, row, col = splitName
        try:
            colorPlates[plateN-1].loc[row, col] = to_hex('xkcd:very light green')
        except KeyError:
            pass

    return colorPlates

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = renameWindow_CF(renamingFileDir='./demoSamples/renamingCF2.xlsx', 
                             smplNameList=['01-Well-A10', '01-Well-A3', '01-Well-B3', '01-Well-C5', '01-Well-D12', '01-Well-E2','01-Well-H7'])
    window.show()
    sys.exit(app.exec_())