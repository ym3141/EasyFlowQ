from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtCore import QModelIndex
# from dataClasses import fcsSample

from pathlib import Path
import sys

sys.path.insert(0, './FlowCal')
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

