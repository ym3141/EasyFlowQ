import sys
from os import getcwd

import matplotlib
from PyQt5 import QtWidgets, QtCore, QtGui, uic

from src import fcsSample, plotCanvas, polygonGateEditor, smplPlotItem, colorGenerator

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
        self.curGateList = []
        self.colorGen = colorGenerator()

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
        self.smplSelectionModel.selectionChanged.connect(self.handle_FigureUpdate)
        self.gateListModel.itemChanged.connect(self.handle_GateSelectionChanged)
        self.xComboBox.currentIndexChanged.connect(self.handle_FigureUpdate)
        self.yComboBox.currentIndexChanged.connect(self.handle_FigureUpdate)
        self.addGateButton.clicked.connect(self.handle_AddGate)


    def handle_LoadData(self):
        fileNames, _ = QtWidgets.QFileDialog.getOpenFileNames(self, 'Open data files', self.baseDir, filter='*.fcs')
        newSmplList = [fcsSample(fileName) for fileName in fileNames]

        newColorList = self.colorGen.giveColors(len(newSmplList))

        for newSmpl, newColor in zip(newSmplList, newColorList):
            newQItem = smplPlotItem(newSmpl, plotColor=QtGui.QColor.fromRgbF(*newColor))
            newQItem.setCheckable(False)
            self.smplListModel.appendRow(newQItem)

            # merging the channel dictionary. 
            # If two channel with same channel name (key), but different flurophore (value), the later one will be kept
            self.chnlDict = {**newSmpl.chnlNameDict, **self.chnlDict}
        
        self.chnlListModel.clear()
        for key in self.chnlDict:
            newQItem = QtGui.QStandardItem('{0}: {1}'.format(key, self.chnlDict[key]))
            self.chnlListModel.appendRow(newQItem)

    def handle_FigureUpdate(self):
        # this function is used to process info for the canvas to redraw
        selectedSmpls = [self.smplListModel.itemFromIndex(idx) for idx in self.sampleListView.selectedIndexes()]

        xChnl = self.chnlLables[self.xComboBox.currentIndex()]
        yChnl = self.chnlLables[self.yComboBox.currentIndex()]
        self.curChnls = [xChnl, yChnl]

        self.curAxScales = ['log', 'log']

        allGateItems = [self.gateListModel.item(idx) for idx in range(self.gateListModel.rowCount())]
        self.curGateList = [gateItem.data() for gateItem in allGateItems if (gateItem.checkState() == 2)]

        self.mpl_canvas.redraw(selectedSmpls, 
                               chnlNames=self.curChnls, 
                               axisNames=(self.xComboBox.currentText(), self.yComboBox.currentText()),
                               axScales=self.curAxScales,
                               gateList=self.curGateList
        )

    def handle_AddGate(self):
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
                self.handle_FigureUpdate()

    def handle_GateSelectionChanged(self, item):
        if item.checkState() == 2:
            pass
        elif item.checkState() == 1:
            pass
        else:
            pass

        self.handle_FigureUpdate()
        # print(item.checkState())            
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

