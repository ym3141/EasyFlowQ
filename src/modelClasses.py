from PyQt5.QtGui import QStandardItem

class smplPlotItem(QStandardItem):
    def __init__(self, fcsSmpl, plotColor):
        super(smplPlotItem, self).__init__(fcsSmpl.fileName)
        
        # fcsSample class; fcs data is stored here
        self.setData(fcsSmpl, role=0x100)

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