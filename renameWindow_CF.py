import sys
from PyQt5 import QtWidgets, QtCore, QtGui, uic
from matplotlib.colors import to_hex
from os import path

import pandas as pd
import numpy as np
from src.qtModels import pandasTableModel

import re

wUi, wBase = uic.loadUiType('./uiDesigns/RenameWindow_CF.ui') # Load the .ui file
re_CFName = re.compile(r'(\d\d)-Well-([A-H])(\d\d?)')

class renameWindow_CF(wUi, wBase):
    renameConfirmed = QtCore.pyqtSignal(dict)

    def __init__(self, renamingFileDir, smplNameList) -> None:
        wBase.__init__(self)
        self.setupUi(self)
        
        self.smplNameList = smplNameList
        self.fileRoot = path.dirname(renamingFileDir)

        self.splitNames = []
        for smplName in smplNameList:
            reMatch = re_CFName.match(smplName)
            self.splitNames.append((int(reMatch.group(1)), reMatch.group(2), int(reMatch.group(3))))


        self.loadRenameFile(renamingFileDir)

        self.renamePB.clicked.connect(self.handle_renameConfirm)
        self.reloadPB.clicked.connect(self.handel_reloadXlsx)

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

    def handel_reloadXlsx(self):
        openFileDir, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Load xlsx file for renaming', self.fileRoot, filter='*.xlsx')
        if not openFileDir:
            return

        self.loadRenameFile(openFileDir)

    def loadRenameFile(self, renamingFileDir):
        maxPlateNumber = max([splitname[0] for splitname in self.splitNames])

        renames = exel2renameTable(renamingFileDir, maxPlateNumber)
        duplicates = findDups(renames)
        dupColorMaps = colorByDuplicates(renames, duplicates)
        smplColorMaps = colorBySmplNames(renames, self.splitNames)

        self.renameTableModel = pandasTableModel(renames[0], foregroundDF=dupColorMaps[0], backgroundDF=smplColorMaps[0])
        self.tableView1.setModel(self.renameTableModel)
        pass

def exel2renameTable(renamingFileDir, maxPlatN):
    names = pd.read_excel(renamingFileDir, sheet_name=None, header=None)
    
    # Read all the name tables
    allNameTable = []
    plateNumber = 1
    for idx in range(len(names)):
        allNameTable.append(names.popitem()[1].fillna('').astype(str))
        plateNumber = int(np.max([np.ceil(allNameTable[-1].shape[0]/12), plateNumber]))

    allNameTable.reverse()
    # Make sure all the tables are (8xN)x12 shape
    for nameTable in allNameTable:
        for colName in range(12):
            if not (colName in nameTable):
                nameTable[colName] = [''] * nameTable.shape[0]
        
        for idxName in range(8*plateNumber):
            if not (idxName in nameTable.index):
                nameTable.loc[idxName] = [''] * 12

    # Concact thing together
    renames = allNameTable[0]
    emptyName = '_' * (len(allNameTable) - 1)
    if len(allNameTable) > 1:
        for nameTable in allNameTable[1:]:
            renames = renames + '_' + nameTable

    # Seperate to plates:
    renamePlates = []
    for idx in range(plateNumber):
        renamePlate = renames.iloc[idx * 0: idx * 0 + 8, 0: 12]
        renamePlate.set_axis(np.arange(1, 13), axis='columns', inplace=True)
        renamePlate.set_axis(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'], axis='index', inplace=True)
        renamePlate.loc['Legend', [1,2]] = ['Sample exist', 'Duplicated name']
        renamePlate.fillna('', inplace=True)
        renamePlate.replace(emptyName, '', inplace=True)
        renamePlates.append(renamePlate.copy())

    # if len(renamePlate) < maxPlatN:
    #     for idx in maxPlatN - len(renamePlate)

    return renamePlates

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