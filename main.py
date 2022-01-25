from PyQt5 import QtWidgets, uic
import sys
from os import getcwd
from dataClasses import fcsSample

from matplotlib.backends.backend_qt5agg import (FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
import matplotlib.pyplot as plt
import matplotlib


matplotlib.use('QT5Agg')

mainWindowUi, mainWindowBase = uic.loadUiType('./Designes/MainWindow.ui') # Load the .ui file

class mainUi(mainWindowBase, mainWindowUi):
    def __init__(self):

        # init and setup UI
        mainWindowBase.__init__(self)
        self.setupUi(self)

        # add the matplotlib ui
        self.fig, self.ax = plt.subplots()
        self.mpl_canvas = FigureCanvas(self.fig)
        self.mpl_nevigationToolbar = NavigationToolbar(self.mpl_canvas, self)

        self.plotLayout = QtWidgets.QVBoxLayout(self.plotBox)
        self.plotLayout.addWidget(self.mpl_nevigationToolbar)
        self.plotLayout.addWidget(self.mpl_canvas)

        # meta info
        self.baseDir = getcwd()

        # linking triggers
        self.actionLoad_Data_Files.triggered.connect(self.handle_LoadData)

    def handle_LoadData(self):
        fileNames, _ = QtWidgets.QFileDialog.getOpenFileNames(self, 'Open data files', self.baseDir, filter='*.fcs')
        newSmplList = [fcsSample(fileName) for fileName in fileNames]
        self.ax.plot(newSmplList[0].data['FSC-A'], newSmplList[0].data['SSC-A'], '.')
        self.ax.set_xscale('log')
        self.ax.set_yscale('log')
        self.mpl_canvas.draw()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    MainWindow = mainUi()
    MainWindow.show()
    sys.exit(app.exec_())

