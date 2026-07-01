from PySide6.QtGui import QStandardItem, QStandardItemModel, QColor, QDoubleValidator, QIntValidator, QValidator, QColor
from PySide6.QtCore import QModelIndex, QAbstractTableModel, QSortFilterProxyModel, Qt, Signal
from PySide6.QtWidgets import QListWidgetItem, QTreeWidgetItem
import pandas as pd

import sys
import os.path
import secrets
import string

from .ioData import FCSData_ef as FCSData

from .plotWidgets import gateSmpls
from .gates import polygonGate, lineGate, quadrantGate

try:
    pd.set_option('future.no_silent_downcasting', True)
except pd.errors.OptionError:
    print('Not the pandas version that EasyFlowQ is built based on, but it should be fine.')

def getFileStem(fileDir):
    if fileDir is None:
        return None

    basename = os.path.basename(fileDir)
    return os.path.splitext(basename)[0]

def genShortUID(n=8):
    alphabet = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(n))


class smplItem(QTreeWidgetItem):
    def __init__(self, parent, fcsFileDir=None, 
                 plotColor=QColor.fromRgbF(0.1, 0.1, 0.1), fcsDataInput=None,
                 infileIdx=0, displayName=None, addDrvedParams=[]):
        # From 1.7.6, fcsDataInput is required for smplItem, and fcsFileDir is only used for display and as an identifier for merging. 
        # For subpopItem, fcsFileDir should be None.

        if fcsDataInput is None:
            raise ValueError('fcsDataInput is required for smplItem.')

        super(smplItem, self).__init__(parent)

        self.fileDir = fcsFileDir # if None, likely a subpop item
        self.infileIdx = infileIdx # for multi-sample fcs file, which sample this item corresponds to. Default to 0 for single-sample fcs file.

        # Use the input data to set fcsData
        fcsData = fcsDataInput

        if displayName is None: 
        # No name give for this sample, try to find a SMID from the FCS metadata or use the file name.
            if 'SMID' in fcsData._text and fcsData._text['SMID'] != '':
                displayName = fcsData._text['SMID']
            elif fcsFileDir is not None:
                displayName = getFileStem(fcsFileDir) + ('_{0}'.format(infileIdx) if infileIdx else '')
            else:
                displayName = '(no name)'
        self.setText(0, displayName)


        for drvedParam in addDrvedParams:
            if not drvedParam in fcsData.channels:
                fcsData = fcsData.appendNewParam(drvedParam)

        self.setData(0, 0x100, fcsData)

        self.setFlags(self.flags() | Qt.ItemIsEditable)
        self.chnlNameDict = dict(zip(self.fcsSmpl.channels, self.fcsSmpl.channel_labels()))

        self.setData(0, 1, plotColor)

    def addDrvedParam_recursively(self, drvedParam):
        newData = self.data(0, 0x100).appendNewParam(drvedParam)
        self.setData(0, 0x100, newData)
        for idx in range(self.childCount()):
            self.child(idx).addDrvedParam_recursively(drvedParam)
    
    @property
    def displayName(self):
        return self.data(0, 0)

    @property
    def plotColor(self):
        return self.data(0, 1)

    @property
    def fcsSmpl(self) -> FCSData:
        return self.data(0, 0x100)

    @property
    def fcsFileName(self):
        return getFileStem(self.fileDir)

    @displayName.setter
    def displayName(self, displayName):
        self.setData(0, 0, displayName) 

    @plotColor.setter
    def plotColor(self, plotColor):
        self.setData(0, 1, plotColor) 
        
class subpopItem(smplItem):
    def __init__(self, parent:smplItem, plotColor, displayName, gateItems):
        self.gateIDs = [gateItem.uuid for gateItem in gateItems]
        fcsData = parent.fcsSmpl

        smpls, _, _ = gateSmpls([fcsData], [gateItem.gate for gateItem in gateItems])
        fcsData = smpls[0]

        # addChild after init improves perf
        super().__init__(None, None, plotColor, fcsDataInput=fcsData, displayName=displayName)
        parent.addChild(self)

    def gateUpdated(self, updatedGateItem, allGateItems):
        if not (updatedGateItem.uuid in self.gateIDs):
            return
        
        useGates = [gateItem.gate for gateItem in allGateItems if gateItem.uuid in self.gateIDs]
        newFcss, _, _ = gateSmpls([self.parent().fcsSmpl], useGates)

        self.setData(0, 0x100, newFcss[0])


class gateWidgetItem(QListWidgetItem):
    def __init__(self, gateName, gate):
        super().__init__(gateName)

        self.setFlags(self.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEditable)
        self.setCheckState(Qt.Unchecked)

        self.setData(0x100, gate)

        self._uuid = genShortUID()

        if isinstance(self.gate, polygonGate):
            toolTips = 'Polygon gate: \nx = {0} in {2} scale \ny = {1} in {3} scale'.format(*self.gate.chnls, *self.gate.axScales)
        elif isinstance(self.gate, quadrantGate):
            toolTips = 'Quadrant gate: \nx = {0} \ny = {1}'.format(*self.gate.chnls)
        elif isinstance(self.gate, lineGate):
            toolTips = 'Line gate: \nx = {0}'.format(self.gate.chnls[0])
        self.setToolTip(toolTips)

    def data(self, role: int):
        if role == Qt.DisplayRole:
            if isinstance(self.gate, (polygonGate, quadrantGate)):
                propStr = '2D: x={0}, y={1}'.format(*self.gate.chnls)
            elif isinstance(self.gate, lineGate):
                propStr = '1D: x={0}'.format(self.gate.chnls[0])

            return super().data(role) + ' ({0})'.format(propStr)

        return super().data(role)

    def text(self) -> str:
        return self.data(Qt.EditRole)

    @property
    def gate(self):
        return self.data(0x100)
    
    @property
    def uuid(self):
        return self._uuid
    
    @uuid.setter
    def uuid(self, newUuid):
        self._uuid = newUuid

    @gate.setter
    def gate(self, newGate):
        self.setData(0x100, newGate)

class quadWidgetItem(QListWidgetItem):
    def __init__(self, quadName, quad):
        super().__init__(quadName)

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
        super().__init__(splitName)

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
        self.stainDict = dict()

    def addChnl(self, chnlKey, chnlName):
        if not (chnlKey in self.keyList):
            newChnlItem = QStandardItem('{0}: {1}'.format(chnlKey, chnlName))
            newChnlItem.setData(chnlKey)
            self.appendRow(newChnlItem)
            self.chnlNameDict[chnlKey] = chnlName
            self.stainDict[chnlKey] = ''
            return 1
        else:
            return 0
        
    def setStainName(self, chnlKey, stainName):
        if chnlKey in self.stainDict:
            self.stainDict[chnlKey] = stainName
            idx = self.keyList.index(chnlKey)

            if stainName != '':
                self.item(idx).setText('{0}: {1} | {2}'.format(chnlKey, self.chnlNameDict[chnlKey], stainName))
            else:
                self.item(idx).setText('{0}: {1}'.format(chnlKey, self.chnlNameDict[chnlKey]))
    
    def loadStainDict(self, stainDict: dict):
        for chnlKey, stainName in stainDict.items():
            if stainName != '':
                self.setStainName(chnlKey, stainName)


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
    def keyList_no_drvedParam(self):
        keyList = [key for key in self.keyList]
        for key in keyList:
            if type(self.chnlNameDict[key]) is str:
                if self.chnlNameDict[key].startswith('Derived Parameter'):
                    keyList.remove(key)
        return keyList

    @property
    def fullTextList(self):
        return [self.item(idx).text() for idx in range(self.rowCount())]

    @property
    def stainLabelList(self):
        return [self.stainDict[chnlKey] for chnlKey in self.keyList]
    
    @property
    def fullChnlNameList(self):
        result = []
        for chnlKey in self.keyList:
            result.append('{0}: {1}'.format(chnlKey, self.chnlNameDict[chnlKey]))
        return result


class pandasTableModel(QAbstractTableModel):
    userInputSignal = Signal(QModelIndex, object)

    def __init__(self, data, foregroundDF = None, backgroundDF = None, editableDF = None, validator=None):
        super(pandasTableModel, self).__init__()
        self._data = data

        self._foreground = self._normalize_color_df(foregroundDF, '#000000')

        self._background = self._normalize_color_df(backgroundDF, '#ffffff')

        if editableDF is None:
            self._editableDF = pd.DataFrame(index=data.index, columns=data.columns).fillna(True)
        else:
            self._editableDF = editableDF

        self._validator = validator

    def _normalize_color_df(self, color_df, default_color):
        if color_df is None:
            return pd.DataFrame(index=self._data.index, columns=self._data.columns).fillna(default_color)

        if color_df.shape == self._data.shape:
            normalized_df = color_df.copy()
            normalized_df = normalized_df.set_axis(self._data.index, axis='index')
            normalized_df = normalized_df.set_axis(self._data.columns, axis='columns')
        else:
            normalized_df = color_df.reindex(index=self._data.index, columns=self._data.columns)

        return normalized_df.fillna(default_color)

    def _color_from_value(self, value, default_color):
        if isinstance(value, QColor):
            return value if value.isValid() else QColor(default_color)

        if pd.isna(value):
            return QColor(default_color)

        color = QColor(str(value))

        if color.isValid():
            return color 
        else: 
            return QColor(default_color)

    def data(self, index, role):
        if role == Qt.DisplayRole or role == Qt.EditRole:
            value = self._data.iloc[index.row(), index.column()]
            return str(value)

        elif role == Qt.ForegroundRole:
            value = self._foreground.iloc[index.row(), index.column()]
            return self._color_from_value(value, '#000000')

        elif role == Qt.BackgroundRole:
            value = self._background.iloc[index.row(), index.column()]
            return self._color_from_value(value, '#ffffff')

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

            elif self._validator.validate(str(value), 0)[0] is QValidator.State.Acceptable:
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
