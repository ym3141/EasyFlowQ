import sys
from PyQt5 import QtWidgets, QtCore, QtGui, uic
from matplotlib.colors import to_hex
from os import path, getcwd

import pandas as pd
import numpy as np
from backend.qtModels import pandasTableModel
from backend.efio import writeRawFcs
from backend.plotWidgets import cachedStats

import csv
import io
from xlsxwriter.utility import xl_col_to_name

__location__ = path.realpath(path.join(getcwd(), path.dirname(__file__)))
wUi, wBase = uic.loadUiType(path.join(__location__, 'uiDesigns/StatWindow.ui')) # Load the .ui file

intFormater = '{:.0f}'.format
percFormater = '{:.2%}'.format
valFormater = '{:.4e}'.format

class statWindow(wUi, wBase):
    def __init__(self, sessionDir, curGateItems_func, curQSItem_func) -> None:

        wBase.__init__(self)
        self.setupUi(self)

        self.sessionDir = sessionDir
        self.dataDF = pd.DataFrame()
        self.displayDF = pd.DataFrame()
        self.cur_Name_RawData_Pairs = []

        self.curGateItems = curGateItems_func
        self.curQSItem = curQSItem_func
        self.curFormaterList = []

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

        formaterList = [intFormater, percFormater]
        newDF = pd.DataFrame(columns=['Cell number', '% of total'], 
                             index=[smplItem.displayName for smplItem in cachedPlotStats.smplItems])

        newDF['Cell number'] = [gatedSmpl.shape[0] for gatedSmpl in cachedPlotStats.gatedSmpls]

        percs = []
        for idx in range(cachedPlotStats.smplNumber):
            percs.append(cachedPlotStats.gatedSmpls[idx].shape[0] / cachedPlotStats.smplItems[idx].fcsSmpl.shape[0])
        newDF['% of total'] = percs
        
        for idx, gateItem in enumerate(self.curGateItems()):
            newDF['% of parent in: \n{0}'.format(gateItem.text())] =  [gatedFrac[idx] for gatedFrac in cachedPlotStats.gatedFracs]
            formaterList.append(percFormater)

        if not (cachedPlotStats.selectedGateItem is None):
            newDF['% of parent in: \n{0} (selected)'.format(cachedPlotStats.selectedGateItem.text())] = [gatedFrac[-1] for gatedFrac in cachedPlotStats.gatedFracs]
            formaterList.append(percFormater)
                
        for chnl in chnls:
            newDF['Median of \n{0}:{1}'.format(chnl, firstItem.chnlNameDict[chnl])] = [np.median(gatedSmpl[:, chnl]) for gatedSmpl in cachedPlotStats.gatedSmpls]
            newDF['Mean of \n{0}:{1}'.format(chnl, firstItem.chnlNameDict[chnl])] = [np.mean(gatedSmpl[:, chnl]) for gatedSmpl in cachedPlotStats.gatedSmpls]

            formaterList += [valFormater] * 2
            
        if len(cachedPlotStats.splitFracs) > 0:
            newDF['% of cells in split: \nleft'] = [splitFrac[0] for splitFrac in cachedPlotStats.splitFracs]
            newDF['% of cells in split: \nright'] = [splitFrac[1] for splitFrac in cachedPlotStats.splitFracs]
            
            formaterList += [percFormater] * 2

        elif len(cachedPlotStats.quadFracs) > 0:
            newDF['% of cells in quad: \nlower left'] = [quadFrac[0] for quadFrac in cachedPlotStats.quadFracs]
            newDF['% of cells in quad: \nupper left'] = [quadFrac[1] for quadFrac in cachedPlotStats.quadFracs]
            newDF['% of cells in quad: \nlower right'] = [quadFrac[2] for quadFrac in cachedPlotStats.quadFracs]
            newDF['% of cells in quad: \nupper right'] = [quadFrac[3] for quadFrac in cachedPlotStats.quadFracs]

            formaterList += [percFormater] * 4
            
        # Save this value for furture faster raw export
        self.cur_Name_RawData_Pairs = []
        for idx in range(cachedPlotStats.smplNumber):
            self.cur_Name_RawData_Pairs.append((cachedPlotStats.smplItems[idx].displayName, cachedPlotStats.gatedSmpls[idx]))

        # save the origin DF (number before conversion to str), and formatter
        self.dataDF = newDF
        self.curFormaterList = formaterList

        # Create the displayDF for display, numbers are convereted to strings
        self.displayDF = pd.DataFrame()
        for idx, col in enumerate(newDF.columns):
            self.displayDF[col] = newDF.iloc[:, idx].apply(formaterList[idx])
        
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

                for idx, formater in enumerate(self.curFormaterList):
                    if formater is percFormater:
                        # +1 because excel's first column is index (sample names)
                        writer.sheets['stats'].set_column(idx + 1, idx + 1, cell_format=percFmt)

                writer.close()
        
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