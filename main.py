import sys
from os import getcwd

import matplotlib
from PyQt5 import QtWidgets, QtCore, QtGui, uic

from dataClasses import fcsSample
from plotClasses import plotCanvas
from gateClasses import polygonGateEditor
from modelClasses import smplPlotItem

matplotlib.use('QT5Agg')

mainWindowUi, mainWindowBase = uic.loadUiType('./uiDesignes/MainWindow.ui') # Load the .ui file

class mainUi(mainWindowBase, mainWindowUi):
    def __init__(self):

        # init and setup UI
        mainWindowBase.__init__(self)
        self.setupUi(self)
        
        # other init
        self.baseDir = './demoSamples/'
        self.chnlDict = dict()
        self.curChnls = None
        self.curAxScales = None

        # add the matplotlib ui
        matplotlib.rcParams['savefig.directory'] = self.baseDir

        self.mpl_canvas = plotCanvas()

        self.plotLayout = QtWidgets.QVBoxLayout(self.plotBox)
        self.plotLayout.addWidget(self.mpl_canvas.navigationBar)
        self.plotLayout.addWidget(self.mpl_canvas)

        # init ui models
        self.smplListModel = QtGui.QStandardItemModel(self.sampleListView)
        self.sampleListView.setModel(self.smplListModel)
        self.smplSelectionModel = self.sampleListView.selectionModel()

        self.gateListModel = QtGui.QStandardItemModel(self.gateListView)
        self.gateListView.setModel(self.gateListModel)
        self.gateSelectionModel = self.gateListView.selectionModel()

        self.chnlListModel = QtGui.QStandardItemModel(self)
        self.xComboBox.setModel(self.chnlListModel)
        self.yComboBox.setModel(self.chnlListModel)

        # link triggers
        self.actionNew_Session.triggered.connect(self.handle_NewSession)
        self.actionLoad_Data_Files.triggered.connect(self.handle_LoadData)
        self.smplSelectionModel.selectionChanged.connect(self.handle_FigureReplot)
        self.gateListModel.itemChanged.connect(self.handle_GateSelectionChanged)
        self.xComboBox.currentIndexChanged.connect(self.handle_FigureReplot)
        self.yComboBox.currentIndexChanged.connect(self.handle_FigureReplot)
        self.addGateButton.clicked.connect(self.handle_addGate)


    def handle_LoadData(self):
        fileNames, _ = QtWidgets.QFileDialog.getOpenFileNames(self, 'Open data files', self.baseDir, filter='*.fcs')
        newSmplList = [fcsSample(fileName) for fileName in fileNames]

        for newSmpl in newSmplList:
            newQItem = smplPlotItem(newSmpl, plotColor=QtGui.QColor(0.9, 0., 0.))
            newQItem.setCheckable(False)
            self.smplListModel.appendRow(newQItem)

            # merging the channel dictionary. 
            # If two channel with same channel name (key), but different flurophore (value), the later one will be kept
            self.chnlDict = {**newSmpl.chnlNameDict, **self.chnlDict}
        
        self.chnlListModel.clear()
        for key in self.chnlDict:
            newQItem = QtGui.QStandardItem('{0}: {1}'.format(key, self.chnlDict[key]))
            self.chnlListModel.appendRow(newQItem)

    def handle_FigureReplot(self):
        # this function is used to process info for the canvas to redraw
        selectedSmpls = [self.smplListModel.itemFromIndex(idx).data(role=0x100) for idx in self.sampleListView.selectedIndexes()]

        xChnl = self.chnlLables[self.xComboBox.currentIndex()]
        yChnl = self.chnlLables[self.yComboBox.currentIndex()]

        self.curChnls = (xChnl, yChnl)
        self.curAxScales = ('log', 'log')

        self.mpl_canvas.redraw(selectedSmpls, 
                               chnlNames=(self.chnlDict[xChnl], self.chnlDict[yChnl]), 
                               axisNames=(self.xComboBox.currentText(), self.yComboBox.currentText()),
                               axScales=self.curAxScales
        )

    def handle_addGate(self):
        self.gateEditor = polygonGateEditor(self.mpl_canvas.ax, self.gateReturned, 
                                            canvasParam=(self.curChnls, self.curAxScales))
        self.gateEditor.addGate_connnect()

    def gateReturned(self, gate, replace=None):
        if replace:
            pass
        else:
            gateName, flag = QtWidgets.QInputDialog.getText(self,'New gate', 'Name for the new gate')

            if flag:
                gate.name = gateName
                newQItem = QtGui.QStandardItem(gate.name)
                newQItem.setData(gate)
                newQItem.setCheckable(True)
                self.gateListModel.appendRow(newQItem)
            else: 
                self.handle_FigureReplot()

    def handle_GateSelectionChanged(self, item):
        if item.checkState() == 2:
            pass
        elif item.checkState() == 1:
            pass
        else:
            pass
        print(item.checkState())            
        pass
                

    
    def handle_NewSession(self):
        QtCore.QProcess().startDetached('python ./main.py')

    @property
    def chnlLables(self):
        return list(self.chnlDict.keys())

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    MainWindow = mainUi()
    MainWindow.show()
    sys.exit(app.exec_())

