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

import csv
import io
from xlsxwriter.utility import xl_col_to_name

wUi, wBase = uic.loadUiType('./uiDesigns/CompWindow.ui') # Load the .ui file

class compWindow(wUi, wBase):
    def __init__(self, chnlListModel=chnlModel(), compMat:compMatrix=None) -> None:

        wBase.__init__(self)
        self.setupUi(self)

        # put the vertical lable, and set stack things
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
            self.spillMatModel = pandasTableModel(
                pd.DataFrame(np.eye(len(chnlList)) * 100, index=chnlList, columns=chnlList),
                backgroundDF=getGreyDiagDF(len(chnlList)),
                editableDF=pd.DataFrame(~np.eye(len(chnlList), dtype=bool), index=chnlList, columns=chnlList),
                validator=QtGui.QDoubleValidator(bottom=0., top=100.)
                )
            self.spillMatTable.setModel(self.spillMatModel)
            self.spillMatModel.userInputSignal.connect(self.spillMatDataEdited)

            self.autoFluoModel = pandasTableModel(
                pd.DataFrame(index=chnlList, columns=['AutoFluor']).fillna(0),
                validator=QtGui.QDoubleValidator()
                )
            self.autoFluoTable.setModel(self.autoFluoModel)
            self.autoFluoModel.userInputSignal.connect(self.autoFluoDataEdited)

            self.needUpdatePage.hide()
            self.stackedCenter.setCurrentWidget(self.mainPage)

    def updateMat(self, newMat):
        pass

    def spillMatDataEdited(self, index1, index2):
        row, col = (index1.row(), index1.column())

        diagValue = 100 - np.sum(self.spillMatModel.dfData.iloc[row, :]) + self.spillMatModel.dfData.iloc[row, row]
        oldValue = self.spillMatModel.dfData.iloc[row, col] + diagValue - self.spillMatModel.dfData.iloc[row, row]

        if diagValue > 0:
            self.spillMatModel.setData(self.spillMatModel.index(row, row), diagValue, role=0x100)
        else:
            input = QtWidgets.QMessageBox.warning(
                self, 'Invalid spill matrix', 
                'The total percentage of a single fluorephore cannot exceed 100. \n' \
                'Click \"Apply\" to aplly re-nomalization accross channels based on entered value; ' \
                'or click \"Cancel\" to revert the last editing',
                QtWidgets.QMessageBox.Cancel | QtWidgets.QMessageBox.Apply
                )

            if input == QtWidgets.QMessageBox.Cancel or input == QtWidgets.QMessageBox.Escape:
                self.spillMatModel.setData(self.spillMatModel.index(row, col), oldValue, role=0x100)
            elif input == QtWidgets.QMessageBox.Apply:
                normalized = self.spillMatModel.dfData.iloc[row, :] / np.sum(self.spillMatModel.dfData.iloc[row, :]) *100
                self.spillMatModel.dfData.iloc[row, :] = normalized

                self.spillMatModel.dataChanged.emit(self.spillMatModel.index(row, 0), self.spillMatModel.index(row, -1))
                pass

            
    def autoFluoDataEdited(self, index1, index2):
        print(index1)
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