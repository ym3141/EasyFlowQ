import sys
from PyQt5 import QtWidgets, QtCore, QtGui, uic
from matplotlib.colors import to_hex
from os import path

import pandas as pd
import numpy as np
from src import pandasTableModel

import re

wUi, wBase = uic.loadUiType('./uiDesignes/StatWindow.ui') # Load the .ui file

class statWindow(wUi, wBase):
    def __init__(self) -> None:

        wBase.__init__(self)
        self.setupUi(self)

        self.statTabelModel = pandasTableModel(pd.DataFrame())
        self.tableView.setModel(self.statTabelModel)
        self.tableView.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignLeft)
        self.tableView.verticalHeader().setDefaultAlignment(QtCore.Qt.AlignRight)

    def updateStat(self, smplsOnPlot, chnls):

        firstItem = smplsOnPlot[0][0]
        newDF = pd.DataFrame(columns=['Cell number', '% of total', 
                                      'Median of \n{0}:{1}'.format(chnls[0], firstItem.chnlNameDict[chnls[0]]), 
                                      'Mean of \n{0}:{1}'.format(chnls[0], firstItem.chnlNameDict[chnls[0]]),
                                      'Median of \n{0}:{1}'.format(chnls[1], firstItem.chnlNameDict[chnls[1]]), 
                                      'Mean of \n{0}:{1}'.format(chnls[1], firstItem.chnlNameDict[chnls[1]])
                                      ])
        for originItem, gatedFCS in smplsOnPlot:
            N_Perc = [gatedFCS.shape[0], gatedFCS.shape[0]/originItem.fcsSmpl.shape[0]]

            
            med_avg1 = [np.median(gatedFCS[:,chnls[0]]), np.mean(gatedFCS[:,chnls[0]])]
            med_avg2 = [np.median(gatedFCS[:,chnls[1]]), np.mean(gatedFCS[:,chnls[1]])]

            newDF.loc[originItem.displayName] = N_Perc + med_avg1 + med_avg2

        self.dataDF = newDF

        formatters = ['{:.0f}', '{:.3%}'] + ['{:.4e}'] * 4
        self.displayDF = pd.DataFrame()
        for idx, col in enumerate(newDF.columns):
            self.displayDF[col] = newDF[col].apply(formatters[idx].format)
        
        self.statTabelModel = pandasTableModel(self.displayDF)
        self.tableView.setModel(self.statTabelModel)
        pass

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = statWindow()
    window.show()
    sys.exit(app.exec_())