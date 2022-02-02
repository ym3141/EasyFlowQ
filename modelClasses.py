from PyQt5.QtGui import QStandardItem

from plotClasses import plotCanvas

class smplPlotItem(QStandardItem):
    def __init__(self, fcsSmpl, plotColor):
        super(smplPlotItem, self).__init__(fcsSmpl.fileName)
        
        # fcsSample class; fcs data is stored here
        self.setData(fcsSmpl, role=0x100)

        # gate list is here
        self.setData([], role=0x101)

        self.setData(plotColor, role=1)
    
    @property
    def displayName(self):
        return self.data(role=1)

    @property
    def fcsSmpl(self):
        return self.data(role=0x100)

    @property
    def gateList(self):
        return self.data(role=0x101)

    @displayName.setter
    def displayName(self, displayName):
        self.setData(displayName, role=1)

    @gateList.setter
    def gateList(self, gateList):
        self.setData(gateList, role=0x101)        