import sys
from PyQt5 import QtWidgets, QtCore, QtGui, uic
from matplotlib.colors import to_hex
from os import path

from PyQt5.QtGui import QPainter
from PyQt5.QtCore import Qt

import pandas as pd
import numpy as np
from src.qtModels import pandasTableModel, chnlModel
from src.comp import compMatrix

import json

wUi, wBase = uic.loadUiType('./uiDesigns/CompWindow.ui') # Load the .ui file

class compWindow(wUi, wBase):
    compValueEdited = QtCore.pyqtSignal()

    def __init__(self, chnlListModel=None, compMat:compMatrix=None) -> None:

        wBase.__init__(self)
        self.setupUi(self)

        # Setting up the UIs
        self.ylabelFrame.layout().addWidget(verticalLabel('Signal spill from (fluorophore):'))
        self.stackedCenter.layout().setStackingMode(QtWidgets.QStackedLayout.StackAll)
        self.needUpdatePage.hide()
        self.autoFluoTable.verticalHeader().setMaximumSize(125, 16777215)
        self.autoFluoTable.horizontalHeader().setMaximumSectionSize(125)

        # link the vertical scrollbars
        self.spillMatTable.verticalScrollBar().valueChanged.connect(self.autoFluoTable.verticalScrollBar().setValue)
        self.autoFluoTable.verticalScrollBar().valueChanged.connect(self.spillMatTable.verticalScrollBar().setValue)

        # link the triggers
        self.refreshPB.clicked.connect(lambda : self.updateChnls(hold=False))
        self.autoFluoCheck.clicked.connect(self.compValueEdited)

        # set the model
        self.chnlListModel = chnlListModel

        self.spillMatModel = pandasTableModel(pd.DataFrame([0]))
        self.spillMatTable.setModel(self.spillMatModel)

        self.autoFluoModel = pandasTableModel(pd.DataFrame([0]))
        self.autoFluoTable.setModel(self.autoFluoModel)

    # Update according to the new channel list. if hold=True, don't update model, but switch to the "need update" page.
    # This should be the only place that one need to change the model.
    def updateChnls(self, newChnlListModel=None, hold=True):
        if newChnlListModel != None:
            self.chnlListModel = newChnlListModel

        if hold:
            self.needUpdatePage.show()
            self.stackedCenter.setCurrentWidget(self.needUpdatePage)

        else:
            chnlList = self.chnlListModel.keyList
            if chnlList == list(self.spillMatModel.dfData.columns):
                # no need to update
                pass
            
            elif self.spillMatModel.dfData.shape == (1, 1):
                # update from no matrix
                self.createEmpty()

            else:
                # old matrix exist, need new insert
                oldAutoFluo = self.autoFluoModel.dfData.copy()
                oldSpillMat = self.spillMatModel.dfData.copy()

                self.createEmpty()

                for oldRowName in oldAutoFluo.index:
                    if not oldAutoFluo.loc[oldRowName, 'AutoFluor'] == 0:
                        self.autoFluoModel.dfData[oldRowName] = oldAutoFluo[oldRowName]
                self.autoFluoTable.setModel(self.autoFluoModel)

                for oldColName in oldSpillMat:
                    self.spillMatModel.dfData[oldColName] = oldSpillMat[oldColName]
                self.spillMatModel.dfData.fillna(0.0, inplace=True)
                self.spillMatTable.setModel(self.spillMatModel)

            self.needUpdatePage.hide()
            self.stackedCenter.setCurrentWidget(self.mainPage)


    # This function create a model of empty compensation matrix, and set it to the model
    def createEmpty(self):
        chnlList = self.chnlListModel.keyList
        chnlFullNames = self.chnlListModel.fullNameList
        self.spillMatModel = pandasTableModel(
            pd.DataFrame(np.eye(len(chnlList)) * 100, index=chnlList, columns=chnlList),
            backgroundDF=getGreyDiagDF(len(chnlList)),
            editableDF=pd.DataFrame(~np.eye(len(chnlList), dtype=bool), index=chnlList, columns=chnlList),
            validator=QtGui.QDoubleValidator(bottom=0.)
            )
        self.spillMatTable.setModel(self.spillMatModel)
        self.spillMatModel.dataChanged.connect(self.spillMatDataEdited)

        self.autoFluoModel = pandasTableModel(
            pd.DataFrame(index=chnlFullNames, columns=['AutoFluor']).fillna(0),
            validator=QtGui.QDoubleValidator()
            )
        self.autoFluoTable.setModel(self.autoFluoModel)
        self.autoFluoModel.dataChanged.connect(self.autoFluoDataEdited)

    # This is used to update model loading. It should not change the chennal list. As the chennal list should always be synced to the data in the mainWindow
    # This will overwrite the info, no checking.
    def updateModels(self, newAutoFluo: pd.DataFrame, newSpillMat: pd.DataFrame):
        
        chnlNumber = newAutoFluo.shape[0]
        self.spillMatModel = pandasTableModel(
            newSpillMat,
            backgroundDF=getGreyDiagDF(chnlNumber),
            editableDF=pd.DataFrame(~np.eye(chnlNumber, dtype=bool)),
            validator=QtGui.QDoubleValidator(bottom=0.)
            )
        self.spillMatTable.setModel(self.spillMatModel)
        self.spillMatModel.dataChanged.connect(self.spillMatDataEdited)

        self.autoFluoModel = pandasTableModel(
            newAutoFluo,
            validator=QtGui.QDoubleValidator()
            )
        self.autoFluoTable.setModel(self.autoFluoModel)
        self.autoFluoModel.dataChanged.connect(self.autoFluoDataEdited)
        pass

    # indicate if an update is required
    def spillMatDataEdited(self, index1, index2):
        self.compValueEdited.emit()
        pass
    
    # indicate if an update is required
    def autoFluoDataEdited(self, index1, index2):
        if self.autoFluoCheck.isChecked():
            self.compValueEdited.emit()
        pass
    
    @property
    def curComp(self):
        if self.atHold:
            self.updateChnls(None, False)

        if self.chnlListModel is None:
            return (None, None, None)
        else:
            if self.autoFluoCheck.isChecked():
                outputAutoFluo = self.autoFluoModel.dfData.set_index(self.chnlListModel.keyList, inplace=False)
            else:
                outputAutoFluo = pd.DataFrame(index=self.chnlListModel.keyList, columns=['AutoFluor']).fillna(0)
            outputSpillMat = self.spillMatModel.dfData.copy()
            return (self.chnlListModel.keyList, outputAutoFluo, outputSpillMat)

    @property
    def atHold(self):
        return self.stackedCenter.currentWidget() == self.needUpdatePage

    def to_json(self):
        if self.atHold:
            self.updateChnls(None, False)
        
        keyList, autoFluo, spillMat = self.curComp

        jCompInfo = dict()
        jCompInfo['keyList'] = keyList
        jCompInfo['autoFluo'] = autoFluo.to_json() if not (autoFluo is None) else None
        jCompInfo['spillMat'] = spillMat.to_json() if not (spillMat is None) else None

        return json.dumps(jCompInfo, sort_keys=True, indent=4)

    # this function process JSON 
    def load_json(self, jString: str):
        if self.atHold:
            self.updateChnls(None, False)

        if self.chnlListModel != None and not \
            (np.allclose(self.autoFluoModel.dfData.to_numpy(), 0) and np.allclose(self.spillMatModel.dfData.to_numpy(), np.eye(len(self.chnlListModel.keyList)) * 100)):

            input = QtWidgets.QMessageBox.question(self, 'Current compensation values are not None/Identity', 
                'Do you want to overwrite the current one?')

            if input == QtWidgets.QMessageBox.StandardButton.No:
                return
        
        jDict = json.loads(jString)
        if self.chnlListModel.keyList == jDict['keyList']:
            self.updateModels(pd.read_json(jDict['autoFluo']), pd.read_json(jDict['spillMat']))
            pass

        else:
            input = QtWidgets.QMessageBox.critical(self, 'Warning! Compensation matrix loading error', 
                'The compensation matrix don\'t have matching channels with the current sample. \
                Click apply so that we can ateempt to load. Or cancel to skip loading the matrix.',
                buttons=QtWidgets.QMessageBox.StandardButton.Apply | QtWidgets.QMessageBox.StandardButton.Cancel)
            
        pass


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