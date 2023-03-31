import sys
from PyQt5 import QtWidgets, QtCore, QtGui, uic

from PyQt5.QtGui import QPainter
from PyQt5.QtCore import Qt

import pandas as pd
import numpy as np
from src.qtModels import pandasTableModel, chnlModel
from src.comp import autoFluoTbModel, spillMatTbModel


import json

wUi, wBase = uic.loadUiType('./uiDesigns/CompWindow.ui') # Load the .ui file

class compWindow(wUi, wBase):
    compValueEdited = QtCore.pyqtSignal()

    def __init__(self, chnlListModel=None) -> None:

        wBase.__init__(self)
        self.setupUi(self)

        # Setting up the UIs
        self.ylabelFrame.layout().addWidget(verticalLabel('Signal spill from (fluorophore):'))
        self.autoFluoTable.verticalHeader().setMaximumSize(125, 16777215)
        self.autoFluoTable.horizontalHeader().setMaximumSectionSize(125)

        # link the vertical scrollbars
        self.spillMatTable.verticalScrollBar().valueChanged.connect(self.autoFluoTable.verticalScrollBar().setValue)
        self.autoFluoTable.verticalScrollBar().valueChanged.connect(self.spillMatTable.verticalScrollBar().setValue)

        # link the triggers
        self.autoFluoCheck.clicked.connect(self.compValueEdited)

        # set the model
        self.chnlListModel = chnlListModel

        self.autoFluoModel = autoFluoTbModel([], [])
        self.autoFluoTable.setModel(self.autoFluoModel)

        self.spillMatModel = spillMatTbModel([])
        self.spillMatTable.setModel(self.spillMatModel)

        # link the selection from spillMat to autoFluo:
        spillMatSelectionModel = self.spillMatTable.selectionModel()
        spillMatSelectionModel.selectionChanged.connect(self.handle_SelectAutoFluo)

    # Update according to the new channel list. 
    def updateChnls(self, newChnlListModel:chnlModel):
        self.chnlListModel = newChnlListModel
        chnlList = self.chnlListModel.keyList

        if chnlList == list(self.spillMatModel.chnlList):
            # no need to update
            pass
        
        elif len(self.spillMatModel.chnlList) == 0 or (self.autoFluoModel.isZeros() and self.spillMatModel.isIdentity()):
            # update from no matrix, or empty matrix
            self.createEmpty()

        else:
            # old matrix exist, need new insert
            oldAutoFluo = self.autoFluoModel.dfData.copy()
            oldSpillMat = self.spillMatModel.dfData.copy()

            self.createEmpty()
            self.autoFluoModel.loadDF(oldAutoFluo)
            self.autoFluoModel.loadDF(oldSpillMat)

            # self.autoFluoTable.setModel(self.autoFluoModel)
            # self.spillMatTable.setModel(self.spillMatModel)

    # This function create a model of empty compensation matrix, and set it to the model
    def createEmpty(self):
        chnlList = self.chnlListModel.keyList
        chnlNames = [fullName[len(chnlList[idx])+2:] for idx, fullName in enumerate(self.chnlListModel.fullNameList)]

        self.autoFluoModel = autoFluoTbModel(chnlList, chnlNames)
        self.autoFluoTable.setModel(self.autoFluoModel)
        self.autoFluoModel.dataChanged.connect(self.autoFluoDataEdited)

        self.spillMatModel = spillMatTbModel(chnlList)
        self.spillMatTable.setModel(self.spillMatModel)
        self.spillMatModel.dataChanged.connect(self.spillMatDataEdited)

        self.spillMatTable.selectionModel().selectionChanged.connect(self.handle_SelectAutoFluo)

    # indicate if an update is required
    def autoFluoDataEdited(self, index1, index2):
        if self.autoFluoCheck.isChecked():
            self.compValueEdited.emit()
        pass
    
    # indicate if an update is required
    def spillMatDataEdited(self, index1, index2):
        self.compValueEdited.emit()
        pass
    
    @property
    def curComp(self):

        if self.chnlListModel is None:
            return (None, None, None)
        else:
            if self.autoFluoCheck.isChecked() and (not self.autoFluoModel.isZeros()):
                idxMap = dict(zip(self.autoFluoModel.DFIndices, self.autoFluoModel.chnlList))
                outputAutoFluo = self.autoFluoModel.dfData.rename(index=idxMap)
            else:
                outputAutoFluo = pd.DataFrame(index=self.chnlListModel.keyList, columns=['AutoFluor']).fillna(0)
            outputSpillMat = self.spillMatModel.dfData.copy()
            return (self.chnlListModel.keyList, outputAutoFluo, outputSpillMat)


    def to_json(self):
        jCompInfo = dict()
        jCompInfo['useAutoFluo'] = self.autoFluoCheck.isChecked()
        jCompInfo['keyList'] = self.chnlListModel.keyList
        jCompInfo['autoFluo'] = self.autoFluoModel.to_json()
        jCompInfo['spillMat'] = self.spillMatModel.to_json()

        return jCompInfo

    # this function process JSON 
    def load_json(self, jDict: dict):
        if self.chnlListModel != None and not (self.autoFluoModel.isZeros() and self.spillMatModel.isIdentity()):

            input = QtWidgets.QMessageBox.question(self, 'Current compensation values are not None/Identity', 
                'Do you want to overwrite the current one?')

            if input == QtWidgets.QMessageBox.StandardButton.No:
                return
                
        if not (jDict['autoFluo'] is None):
            self.autoFluoModel.load_json(jDict['autoFluo'])

        if not (jDict['spillMat'] is None):
            self.spillMatModel.load_json(jDict['spillMat'])

    def handle_SelectAutoFluo(self, selected):
        index = selected.indexes()[0]
        self.autoFluoTable.selectRow(index.row())

class verticalLabel(QtWidgets.QLabel):

    def __init__(self, text=None):
        super(self.__class__, self).__init__()
        self.text = text

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(Qt.black)
        painter.setBrush(Qt.Dense1Pattern)
        painter.translate(20, 400)
        painter.rotate(-90)
        if self.text:
            painter.drawText(0, 0, self.text)
        painter.end()

def getGreyDiagDF(length):
    greyDiagDF = pd.DataFrame(index=range(length), columns=range(length)).fillna('#ffffff')
    np.fill_diagonal(greyDiagDF.values, ['#b0b0b0'])
    return greyDiagDF

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = compWindow(None, None)
    window.show()
    sys.exit(app.exec_())
    pass