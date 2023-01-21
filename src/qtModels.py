from PyQt5.QtGui import QStandardItem, QStandardItemModel, QColor, QDoubleValidator, QIntValidator
from PyQt5.QtCore import QModelIndex, QAbstractTableModel, QSortFilterProxyModel, Qt, pyqtSignal
from PyQt5.QtWidgets import QListWidgetItem
import pandas as pd

from PyQt5 import QtCore

import sys
import os.path

from FlowCal.io import FCSData
from FlowCal.transform import to_rfi

def getFileStem(fileDir):
    basename = os.path.basename(fileDir)
    return os.path.splitext(basename)[0]


class smplPlotItem(QListWidgetItem):
    def __init__(self, fcsFileDir, plotColor):
        self.fileDir = fcsFileDir
        super(smplPlotItem, self).__init__(getFileStem(self.fileDir))
        
        # FCSData class; fcs data is stored here
        self.setFlags(self.flags() | Qt.ItemIsEditable)
        fcsData = to_rfi(FCSData(self.fileDir))
        self.setData(0x100, fcsData)

        self.chnlNameDict = dict(zip(fcsData.channels, fcsData.channel_labels()))

        self.setData(1, plotColor)
    
    @property
    def displayName(self):
        return self.data(0)

    @property
    def plotColor(self):
        return self.data(1)

    @property
    def fcsSmpl(self):
        return self.data(0x100)

    @property
    def fcsFileName(self):
        return getFileStem(self.fileDir)

    @displayName.setter
    def displayName(self, displayName):
        self.setData(0, displayName) 

    @plotColor.setter
    def plotColor(self, plotColor):
        self.setData(1, plotColor) 

class gateWidgetItem(QListWidgetItem):
    def __init__(self, gateName, gate):
        super(QListWidgetItem, self).__init__(gateName)

        self.setFlags(self.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEditable)
        self.setCheckState(0)

        self.setData(0x100, gate)

    def data(self, role: int):
        if role == Qt.DisplayRole:
            return super().data(role) + ' ({0})'.format(self.gate.__class__.__name__)

        return super().data(role)

    def text(self) -> str:
        return self.data(Qt.EditRole)

    @property
    def gate(self):
        return self.data(0x100)

class quadWidgetItem(QListWidgetItem):
    def __init__(self, quadName, quad):
        super(QListWidgetItem, self).__init__(quadName)

        self.setFlags(self.flags() | Qt.ItemIsEditable)

        self.quad = quad
    
    def data(self, role: int):
        if role == Qt.DisplayRole:
            return super().data(role) + ' (Q: x={0}, y={1})'.format(self.quad.chnls[0], self.quad.chnls[1])

        return super().data(role)

    def text(self) -> str:
        return self.data(Qt.EditRole)

class splitWidgetItem(QListWidgetItem):
    def __init__(self, splitName, split):
        super(QListWidgetItem, self).__init__(splitName)

        self.setFlags(self.flags() | Qt.ItemIsEditable)

        self.split = split
    
    def data(self, role: int):
        if role == Qt.DisplayRole:
            return super().data(role) + ' (S: x={0})'.format(self.split.chnl)

        return super().data(role)
    
    def text(self) -> str:
        return self.data(Qt.EditRole)

class chnlModel(QStandardItemModel):
    def __init__(self):
        super().__init__()
        self.chnlNameDict = dict()

    def addChnl(self, chnlKey, chnlName):
        if not (chnlKey in self.keyList):
            newChnlItem = QStandardItem('{0}: {1}'.format(chnlKey, chnlName))
            newChnlItem.setData(chnlKey)
            self.appendRow(newChnlItem)
            self.chnlNameDict[chnlKey] = chnlName
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

    @property
    def fullNameList(self):
        return [self.item(idx).text() for idx in range(self.rowCount())]

class gateProxyModel(QSortFilterProxyModel):
    def __init__(self, parent):
        QSortFilterProxyModel.__init__(self, parent)

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        # leftData = self.sourceModel().data(left)
        # rightData = self.sourceModel().data(right)

        return super().lessThan(left, right)
    pass

class pandasTableModel(QAbstractTableModel):
    userInputSignal = pyqtSignal(QtCore.QModelIndex, object)

    def __init__(self, data, foregroundDF = None, backgroundDF = None, editableDF = None, validator=None):
        super(pandasTableModel, self).__init__()
        self._data = data

        if foregroundDF is None:
            self._foreground = pd.DataFrame().reindex_like(data).fillna('#000000')
        else:
            self._foreground = foregroundDF

        if backgroundDF is None:
            self._background = pd.DataFrame().reindex_like(data).fillna('#ffffff')
        else:
            self._background = backgroundDF

        if editableDF is None:
            self._editableDF = pd.DataFrame().reindex_like(data).fillna(True)
        else:
            self._editableDF = editableDF

        self._validator = validator

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
    
    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False

        row = index.row()
        if row < 0 or row >= len(self._data.values):
            return False

        column = index.column()
        if column < 0 or column >= self._data.columns.size:
            return False

        if role == Qt.EditRole or role == 0x100:
            if self._validator is None :
                self._data.iloc[row, column] = value
                self.dataChanged.emit(index, index)
                if role == Qt.EditRole:
                    self.userInputSignal.emit(index, value)
                return True

            elif self._validator.validate(str(value), 0)[0] == 2:
                if isinstance(self._validator,  QIntValidator):
                    self._data.iloc[row, column] = int(value)
                elif isinstance(self._validator, QDoubleValidator):
                    self._data.iloc[row, column] = float(value)
                else:
                    self._data.iloc[row, column] = value
                self.dataChanged.emit(index, index)
                if role == Qt.EditRole:
                    self.userInputSignal.emit(index, value)
                return True
            else:
                return False
        else:
            return False

    # give flags that help to decide if an element is editable
    def flags(self, index):
        flags = super().flags(index)

        if self._editableDF.iloc[index.row(), index.column()]:
            flags |= Qt.ItemIsEditable
        else: 
            flags &= ~Qt.ItemIsEditable

        return flags

    @property
    def dfData(self):
        return self._data

if __name__ == '__main__':
    pass