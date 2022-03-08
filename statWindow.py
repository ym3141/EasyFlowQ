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
    def __init__(self, sessionDir) -> None:

        wBase.__init__(self)
        self.setupUi(self)

        self.sessionDir = sessionDir
        self.dataDF = pd.DataFrame()
        self.displayDF = pd.DataFrame()
        self.cur_Name_RawData_Pairs = []

        self.statTabelModel = pandasTableModel(self.displayDF)
        self.tableView.setModel(self.statTabelModel)
        self.tableView.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignLeft)
        self.tableView.verticalHeader().setDefaultAlignment(QtCore.Qt.AlignRight)

        self.exportStatsPB.clicked.connect(self.handle_ExportStats)
        self.exportDataPB.clicked.connect(self.handle_ExportData)

    def updateStat(self, smplsOnPlot, chnls):

        self.cur_Name_RawData_Pairs = []

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

            self.cur_Name_RawData_Pairs.append((originItem.displayName, gatedFCS))

        self.dataDF = newDF

        formatters = ['{:.0f}', '{:.2%}'] + ['{:.4e}'] * 4
        self.displayDF = pd.DataFrame()
        for idx, col in enumerate(newDF.columns):
            self.displayDF[col] = newDF.iloc[:, idx].apply(formatters[idx].format)
        
        self.statTabelModel = pandasTableModel(self.displayDF)
        self.tableView.setModel(self.statTabelModel)
        pass
    
    def handle_ExportStats(self):
        saveFileDir, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Export stats', self.sessionDir, filter='*.xlsx')
        if not saveFileDir:
            return

        self.dataDF.to_excel(saveFileDir)
        pass


    def handle_ExportData(self):
        saveFileDir, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Export raw data', self.sessionDir, filter='*.xlsx')
        if not saveFileDir:
            return

        self.progressBar.setEnabled(True)
        self.progressBar.reset()        
        with pd.ExcelWriter(saveFileDir) as writer:
            for idx, pair in enumerate(self.cur_Name_RawData_Pairs):
                name, fcsData = pair
                self.exportLabel.setText(name)
                df2write = pd.DataFrame(fcsData, columns=fcsData.channels)
                df2write.to_excel(writer, sheet_name=name)

                self.progressBar.setValue((idx + 1) / len(self.cur_Name_RawData_Pairs) * 100)

        self.exportLabel.setText('Finished')
        self.progressBar.setEnabled(False)
        pass

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = statWindow('./demoSamples')
    window.show()
    sys.exit(app.exec_())