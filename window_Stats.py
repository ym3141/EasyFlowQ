import sys
from PyQt5 import QtWidgets, QtCore, QtGui, uic
from matplotlib.colors import to_hex
from os import path

import pandas as pd
import numpy as np
from src.qtModels import pandasTableModel
from src.efio import writeRawFcs
from src.plotWidgets import cachedStats

import csv
import io
from xlsxwriter.utility import xl_col_to_name

wUi, wBase = uic.loadUiType('./uiDesigns/StatWindow.ui') # Load the .ui file

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

        self.tableView.installEventFilter(self)

    def updateStat(self, cachedPlotStats:cachedStats, forceUpdate=False):

        if (not self.isVisible()) and (not forceUpdate):
            return

        if cachedPlotStats.smplNumber == 0:
            self.cur_Name_RawData_Pairs = []
            self.dataDF = pd.DataFrame()
            self.displayDF = pd.DataFrame()

            self.statTabelModel = pandasTableModel(self.displayDF)
            self.tableView.setModel(self.statTabelModel)

            return

        firstItem = cachedPlotStats.smplItems[0]
        chnls = cachedPlotStats.chnls

        columns = ['Cell number', '% of total']

        if not (cachedPlotStats.selectedGateItem is None):
            columns += ['% of parent in: \n{0}'.format(cachedPlotStats.selectedGateItem.text())]
        elif len(cachedPlotStats.gatedFracs[0]) > 0:
            columns += ['% of parent in: \nlast gate']
        
        for chnl in chnls:
            columns += ['Median of \n{0}:{1}'.format(chnl, firstItem.chnlNameDict[chnl]), 
                        'Mean of \n{0}:{1}'.format(chnl, firstItem.chnlNameDict[chnl])]
            
        if len(cachedPlotStats.splitFracs) > 0:
            columns += ['% of cells in split: left', '% of cells in split: right']

        elif len(cachedPlotStats.quadFracs) > 0:
            columns += ['% of cells in quad: \nlower left', '% of cells in split: \nupper left', 
                        '% of cells in split: \nlower right', '% of cells in split: \nupper right']


        newDF = pd.DataFrame(columns=columns)
        self.cur_Name_RawData_Pairs = []

        for idx in range(cachedPlotStats.smplNumber):
            N_Perc = [cachedPlotStats.gatedSmpls[idx].shape[0], cachedPlotStats.gatedSmpls[idx].shape[0] / cachedPlotStats.smplItems[idx].fcsSmpl.shape[0]]

            selectedFrac = []
            if len(cachedPlotStats.gatedFracs[idx]) > 0:
                selectedFrac = [cachedPlotStats.gatedFracs[idx][-1]]                
            
            med_avgs = []
            for chnl in chnls:
                med_avgs += [np.median(cachedPlotStats.gatedSmpls[idx][:, chnl]), np.mean(cachedPlotStats.gatedSmpls[idx][:,chnl])]

            split_perc = []
            quad_perc = []
            if len(cachedPlotStats.splitFracs) > 0:
                split_perc = cachedPlotStats.splitFracs[idx]
                
            elif len(cachedPlotStats.quadFracs) > 0:
                quad_perc = cachedPlotStats.quadFracs[idx]

            newDF.loc[cachedPlotStats.smplItems[idx].displayName] = N_Perc + selectedFrac + med_avgs + list(split_perc) + list(quad_perc)

            self.cur_Name_RawData_Pairs.append((cachedPlotStats.smplItems[idx].displayName, cachedPlotStats.gatedSmpls[idx]))

        self.dataDF = newDF

        formatters = ['{:.0f}', '{:.2%}'] + ['{:.2%}'] * len(selectedFrac) + ['{:.4e}'] * 2 * len(cachedPlotStats.chnls) + ['{:.2%}'] * len(list(split_perc) + list(quad_perc))
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

        try:
            with pd.ExcelWriter(saveFileDir, engine='xlsxwriter') as writer:
                self.dataDF.to_excel(excel_writer=writer, sheet_name='stats')
                #format the fractions as percentage in excel
                percFmt = writer.book.add_format({'num_format': '0.00%'})
                fmtRange = '{0}:{1}'.format(xl_col_to_name(2), xl_col_to_name(len(self.dataDF.columns)-4))
                writer.sheets['stats'].set_column(fmtRange, None, cell_format=percFmt)

                writer.save()
        
        except PermissionError:
            QtWidgets.QMessageBox.warning(self, 'Permission Error', 'Please ensure you have writing permission to this directory, and the file is not opened elsewhere.')

        except BaseException as err:
            QtWidgets.QMessageBox.warning(self, 'Unexpected Error', 'Message: {0}'.format(err))

        pass


    def handle_ExportData(self):
        saveFileDir = QtWidgets.QFileDialog.getExistingDirectory(self, caption='Export raw data', directory=self.sessionDir)
        if not saveFileDir:
            return

        self.exportLabel.setText('Starting...')
        self.progressBar.setValue(0)

        names = [a[0] for a in self.cur_Name_RawData_Pairs]
        fcsDatas = [a[1] for a in self.cur_Name_RawData_Pairs]

        writterThread = writeRawFcs(self, names, fcsDatas, saveFileDir)
        writterThread.prograssChanged.connect(self.handle_updateProgBar)
        writterThread.finished.connect(self.handle_ExportDataFinished)

        writterThread.start()

        pass
    
    def handle_updateProgBar(self, curName, progFrac):
        self.exportLabel.setText('{0}'.format(curName))
        self.progressBar.setValue(int(progFrac*100))

    def handle_ExportDataFinished(self):
        self.exportLabel.setText('Finished')
        self.progressBar.setValue(100)
    

    def eventFilter(self, source, event):

        if (event.type() == QtCore.QEvent.KeyPress and event.matches(QtGui.QKeySequence.Copy)):
            self.copySelection()
            return True

        return super(wBase, self).eventFilter(source, event)

    def copySelection(self):
        # this parts enables copy multiple cells.

        selection = self.tableView.selectedIndexes()
        if selection:
            rows = sorted(index.row() for index in selection)
            columns = sorted(index.column() for index in selection)
            rowcount = rows[-1] - rows[0] + 1
            colcount = columns[-1] - columns[0] + 1
            table = [[''] * colcount for _ in range(rowcount)]
            for index in selection:
                row = index.row() - rows[0]
                column = index.column() - columns[0]
                table[row][column] = index.data()
            stream = io.StringIO()
            csv.writer(stream, delimiter='\t').writerows(table)
            QtWidgets.qApp.clipboard().setText(stream.getvalue())
        return

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = statWindow('./demoSamples')
    window.show()
    sys.exit(app.exec_())