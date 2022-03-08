from PyQt5.QtGui import QStandardItem, QStandardItemModel, QColor
from PyQt5.QtCore import QModelIndex, QAbstractTableModel, Qt
import pandas as pd

from pathlib import Path
import sys

from FlowCal.io import FCSData
from FlowCal.transform import to_rfi

class smplPlotItem(QStandardItem):
    def __init__(self, fcsFileDir, plotColor):
        self.fileDir = fcsFileDir
        super(smplPlotItem, self).__init__(Path(self.fileDir).stem)
        
        # FCSData class; fcs data is stored here
        fcsData = to_rfi(FCSData(self.fileDir))
        self.setData(fcsData, role=0x100)

        self.chnlNameDict = dict(zip(fcsData.channels, fcsData.channel_labels()))

        self.setData(plotColor, role=1)
    
    @property
    def displayName(self):
        return self.data(role=0)

    @property
    def plotColor(self):
        return self.data(role=1)

    @property
    def fcsSmpl(self):
        return self.data(role=0x100)

    @property
    def fcsFileName(self):
        return Path(self.fileDir).stem

    @displayName.setter
    def displayName(self, displayName):
        self.setData(displayName, role=0) 

    @plotColor.setter
    def plotColor(self, plotColor):
        self.setData(plotColor, role=1) 


class chnlModel(QStandardItemModel):
    def __init__(self):
        super().__init__()

    def addChnl(self, chnlKey, chnlName):
        if not (chnlKey in self.keyList):
            newChnlItem = QStandardItem('{0}: {1}'.format(chnlKey, chnlName))
            newChnlItem.setData(chnlKey)
            self.appendRow(newChnlItem)
            return 1
        else:
            return 0

    def qIdxFromKey(self, chnlKey):
        if chnlKey in self.chnlNameDict:
            idx = self.keyList.index(chnlKey)
            return self.indexFromItem(self.item(row=idx))
        else:
            return QModelIndex()

    def keyFormQIdx(self, qIdx):
        return self.itemFromIndex(qIdx).data()
        
    @property
    def keyList(self):
        return [self.item(idx).data() for idx in range(self.rowCount())]




class pandasTableModel(QAbstractTableModel):

    def __init__(self, data, foregroundDF = None, backgroundDF = None):
        super(pandasTableModel, self).__init__()
        self._data = data

        if foregroundDF is None:
            self._foreground =  pd.DataFrame().reindex_like(data).fillna('#000000')
        else:
            self._foreground = foregroundDF

        if backgroundDF is None:
            self._background =  pd.DataFrame().reindex_like(data).fillna('#ffffff')
        else:
            self._background = backgroundDF

    def data(self, index, role):
        if role == Qt.DisplayRole or role == Qt.EditRole:
            value = self._data.iloc[index.row(), index.column()]
            return str(value)
        elif role == Qt.ForegroundRole:
            value = self._foreground.iloc[index.row(), index.column()]

            return QColor(value)

        elif role == Qt.BackgroundRole:
            value = self._background.iloc[index.row(), index.column()]

            return QColor(value)

    def rowCount(self, index):
        return self._data.shape[0]

    def columnCount(self, index):
        return self._data.shape[1]

    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._data.columns[section])

            if orientation == Qt.Vertical:
                return str(self._data.index[section])
    
    def setData(self, index, value, role):
        if not index.isValid():
            return False
        if role != Qt.EditRole:
            return False
        row = index.row()
        if row < 0 or row >= len(self._data.values):
            return False
        column = index.column()
        if column < 0 or column >= self._data.columns.size:
            return False
        self._data.iloc[row, column] = value
        self.dataChanged.emit(index, index)
        return True

    def flags(self, index):
        flags = super(self.__class__,self).flags(index)
        flags |= Qt.ItemIsEditable
        return flags

