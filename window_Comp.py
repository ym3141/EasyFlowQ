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

            self.needUpdatePage.hide()
            self.stackedCenter.setCurrentWidget(self.mainPage)

    def updateMat(self, newMat):
        pass

    def spillMatDataEdited(self, index1, index2):
        self.compValueEdited.emit()
        pass
            
    def autoFluoDataEdited(self, index1, index2):
        if self.autoFluoCheck.isChecked():
            self.compValueEdited.emit()
        print(index1)
        pass
    
    @property
    def curComp(self):
        if self.stackedCenter.currentWidget == self.needUpdatePage:
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