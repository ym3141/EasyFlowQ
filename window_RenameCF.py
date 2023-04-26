import sys
from PyQt5 import QtWidgets, QtCore, QtGui, uic
from matplotlib.colors import to_hex
from os import path

import pandas as pd
import numpy as np
from src.qtModels import pandasTableModel

import re

wUi, wBase = uic.loadUiType('./uiDesigns/RenameWindow_CF.ui') # Load the .ui file
re_CFName = re.compile(r'(\d\d)-(Well|Tube)-([A-H])(\d\d?)')

class renameWindow_CF(wUi, wBase):
    renameConfirmed = QtCore.pyqtSignal(dict)

    def __init__(self, dir4Save, smplNameList) -> None:
        wBase.__init__(self)
        self.setupUi(self)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        
        self.smplNameList = smplNameList
        self.fileRoot = dir4Save

        self.splitNames = []
        for smplName in smplNameList:
            reMatch = re_CFName.match(smplName)
            if not (reMatch is None):
                self.splitNames.append((int(reMatch.group(1)), reMatch.group(3), int(reMatch.group(4))))

        self.renames = None

        # Determine the max plate number
        self.maxPlateNumber = max([splitname[0] for splitname in self.splitNames])
        self.renameTableViews = [self.tableView1]

        if self.maxPlateNumber > 1:
            for idx in range(self.maxPlateNumber - 1):
                newTabPage = tabPage(self.tabWidget, tblExample=self.tableView1)
                self.tabWidget.addTab(newTabPage, 'Plate #{0}'.format(idx + 2))
                self.renameTableViews.append(newTabPage.rnTableView)

        self.renamePB.clicked.connect(self.handle_renameConfirm)
        self.reloadPB.clicked.connect(self.handle_reloadXlsx)

    def showEvent(self, event):
        openFileDir, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Load xlsx file for renaming', self.fileRoot, filter='*.xlsx')
        if not openFileDir:
            return

        self.loadRenameFile(openFileDir)

    def handle_renameConfirm(self):
        renameDict = dict()
        if self.renames is not None:
            for name, splitName in zip(self.smplNameList, self.splitNames):
                if not (name in renameDict):
                    rename = self.renameTableViews[splitName[0] - 1].model().dfData.loc[splitName[1], splitName[2]]
                    if rename:
                        renameDict[name] = rename 

        self.renameConfirmed.emit(renameDict)
        self.close()

    def handle_reloadXlsx(self):
        openFileDir, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Load xlsx file for renaming', self.fileRoot, filter='*.xlsx')
        if not openFileDir:
            return

        self.loadRenameFile(openFileDir)

    def loadRenameFile(self, renamingFileDir):
        # Load the renaming file
        self.renames = exel2renameTable(renamingFileDir, self.maxPlateNumber)

        duplicates = findDups(self.renames)
        dupColorMaps = colorByDuplicates(self.renames, duplicates)
        smplColorMaps = colorBySmplNames(self.renames, self.splitNames)

        for idx in range(self.maxPlateNumber):
            renameTableModel = pandasTableModel(self.renames[idx], foregroundDF=dupColorMaps[idx], backgroundDF=smplColorMaps[idx])
            renameTableView = self.renameTableViews[idx]
            renameTableView.setModel(renameTableModel)


def exel2renameTable(renamingFileDir, maxPlatN):
    names = pd.read_excel(renamingFileDir, sheet_name=None, header=None)
    
    # Read all the name tables
    allNameTable = []
    plateNumber = 1
    for idx in range(len(names)):
        allNameTable.append(names.popitem()[1].fillna('').astype(str))
        plateNumber = int(np.max([np.ceil(allNameTable[-1].shape[0]/8), plateNumber]))

    allNameTable.reverse()
    # Make sure all the tables are (8xN)x12 shape
    for nameTable in allNameTable:
        for colName in range(12):
            if not (colName in nameTable):
                nameTable[colName] = [''] * nameTable.shape[0]
        
        for idxName in range(8 * plateNumber):
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
        renamePlate = renames.iloc[idx * 8: idx * 8 + 8, 0: 12]
        renamePlate.set_axis(np.arange(1, 13), axis='columns', inplace=True)
        renamePlate.set_axis(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'], axis='index', inplace=True)
        renamePlate.loc['Legend', [1,2]] = ['Sample exist', 'Duplicated name']
        renamePlate.fillna('', inplace=True)
        renamePlate.replace(emptyName, '', inplace=True)
        renamePlates.append(renamePlate.copy())

    # append empty dfs if there are more plates
    if len(renamePlates) < maxPlatN:
        emptyNamePlate = pd.DataFrame(columns=np.arange(1, 13), index=['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'])
        emptyNamePlate.loc['Legend', [1,2]] = ['Sample exist', 'Duplicated name']
        emptyNamePlate.fillna('', inplace=True)
        for idx in range(maxPlatN - len(renamePlates)):
            renamePlates.append(emptyNamePlate.copy())

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


class tabPage(QtWidgets.QWidget):
    def __init__(self, parent, tblExample=None) -> None:
        super().__init__(parent, flags=QtCore.Qt.Widget)

        self.setLayout(QtWidgets.QHBoxLayout())

        self.rnTableView = QtWidgets.QTableView()
        if tblExample is not None:
            self.rnTableView.setStyleSheet(tblExample.styleSheet())
            self.rnTableView.setFont(tblExample.font())
            self.rnTableView.horizontalHeader().setDefaultSectionSize(tblExample.horizontalHeader().defaultSectionSize())
        self.rnTableView.setWordWrap(True)

        self.layout().addWidget(self.rnTableView)

        # self.objectName = title


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = renameWindow_CF(dir4Save='./demoSamples', 
                             smplNameList=['01-Well-A10', '01-Well-A3', '01-Well-B3', '01-Well-C5', '01-Well-D12', '01-Well-E2','01-Well-H7'])
    window.show()
    sys.exit(app.exec_())