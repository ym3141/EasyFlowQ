import sys
from os import getcwd

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt5 import QtWidgets, QtCore, QtGui, uic

from dataClasses import fcsSample

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

        # add the matplotlib ui
        self.fig, self.ax = plt.subplots()
        self.fig.set_tight_layout(True)
        self.mpl_canvas = FigureCanvasQTAgg(self.fig)
        self.mpl_nevigationToolbar = NavigationToolbar(self.mpl_canvas, self)

        self.plotLayout = QtWidgets.QVBoxLayout(self.plotBox)
        self.plotLayout.addWidget(self.mpl_nevigationToolbar)
        self.plotLayout.addWidget(self.mpl_canvas)

        # init ui models
        self.smplListModel = QtGui.QStandardItemModel(self.sampleListView)
        self.sampleListView.setModel(self.smplListModel)
        self.smplSelectionModel = self.sampleListView.selectionModel()

        self.chnlListModel = QtGui.QStandardItemModel(self)
        self.xComboBox.setModel(self.chnlListModel)
        self.yComboBox.setModel(self.chnlListModel)

        # link triggers
        self.actionNew_Session.triggered.connect(self.handle_NewSession)
        self.actionLoad_Data_Files.triggered.connect(self.handle_LoadData)
        self.smplSelectionModel.selectionChanged.connect(self.handle_FigureReplot)
        self.xComboBox.currentIndexChanged.connect(self.handle_FigureReplot)
        self.yComboBox.currentIndexChanged.connect(self.handle_FigureReplot)



    def handle_LoadData(self):
        fileNames, _ = QtWidgets.QFileDialog.getOpenFileNames(self, 'Open data files', self.baseDir, filter='*.fcs')
        newSmplList = [fcsSample(fileName) for fileName in fileNames]

        for newSmpl in newSmplList:
            newQItem = QtGui.QStandardItem(newSmpl.fileName)
            newQItem.setData(newSmpl)
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
        self.ax.clear()

        selectedSmpls = [self.smplListModel.itemFromIndex(idx).data() for idx in self.sampleListView.selectedIndexes()]

        xChnl = self.chnlLables[self.xComboBox.currentIndex()]
        yChnl = self.chnlLables[self.yComboBox.currentIndex()]

        for idx, selectedSmpl in enumerate(selectedSmpls):
            self.ax.plot(selectedSmpl.data[self.chnlDict[xChnl]], selectedSmpl.data[self.chnlDict[yChnl]], '.', color='C'+str(idx%10))


        self.ax.set_xscale('log')
        self.ax.set_yscale('log')
        self.ax.set_xlabel(self.xComboBox.currentText())
        self.ax.set_ylabel(self.yComboBox.currentText())

        self.mpl_canvas.draw()

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

