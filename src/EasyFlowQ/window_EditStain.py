from PySide6 import QtWidgets, QtCore, QtGui
from matplotlib.colors import to_hex
from os import path, getcwd

import pandas as pd
import numpy as np
from .backend.qtModels import pandasTableModel, chnlModel
from .uiDesigns import UiLoader


class editStainWindow(QtWidgets.QDialog):
    # Class for the window that allows the user to edit the stain labels for each channel
    # stainDict: dictionary with the stain labels for each channel, input is expected to be empty dict
    def __init__(self, chnlListModel: chnlModel, outStainDict: dict) -> None:
        super().__init__()
        UiLoader().loadUi('EditStainWindow.ui', self)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.chnlList = chnlListModel.keyList
        self.fullChnlNames = chnlListModel.fullChnlNameList
        self.curStainLabels = chnlListModel.stainLabelList
        self.newStainDict = outStainDict

        tableDF = pd.DataFrame({'Channel': self.fullChnlNames, 'Stain label': self.curStainLabels})
        editableDF = pd.DataFrame({'Channel': [False]*len(self.chnlList), 'Stain label': [True]*len(self.chnlList)})
        self.anotateTableModel = pandasTableModel(tableDF, editableDF=editableDF)
        self.tableView.setModel(self.anotateTableModel)

    def accept(self):
        for row in self.anotateTableModel.dfData.iterrows():
            stainName = row[1]['Stain label']
            chnlKey = self.chnlList[row[0]]

            # New stain label
            if stainName != '':
                self.newStainDict[chnlKey] = stainName
            
            # Stain label deleted
            elif self.curStainLabels[row[0]] != '':
                self.newStainDict[chnlKey] = ''

        super().accept()