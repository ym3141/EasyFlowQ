import sys
from os import getcwd

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt5 import QtWidgets, QtCore, uic

from dataClasses import fcsSample

matplotlib.use('QT5Agg')

mainWindowUi, mainWindowBase = uic.loadUiType('./uiDesignes/MainWindow.ui') # Load the .ui file

class mainUi(mainWindowBase, mainWindowUi):
    def __init__(self):

        # init and setup UI
        mainWindowBase.__init__(self)
        self.setupUi(self)

        # add the matplotlib ui
        self.fig, self.ax = plt.subplots()
        self.fig.set_tight_layout(True)
        self.mpl_canvas = FigureCanvas(self.fig)
        self.mpl_nevigationToolbar = NavigationToolbar(self.mpl_canvas, self)

        self.plotLayout = QtWidgets.QVBoxLayout(self.plotBox)
        self.plotLayout.addWidget(self.mpl_nevigationToolbar)
        self.plotLayout.addWidget(self.mpl_canvas)

        # meta info
        self.baseDir = getcwd()

        # linking triggers
        self.actionNew_Session.triggered.connect(self.handle_NewSession)
        self.actionLoad_Data_Files.triggered.connect(self.handle_LoadData)

    def handle_LoadData(self):
        fileNames, _ = QtWidgets.QFileDialog.getOpenFileNames(self, 'Open data files', self.baseDir, filter='*.fcs')
        newSmplList = [fcsSample(fileName) for fileName in fileNames]
        self.ax.plot(newSmplList[0].data['FSC-A'], newSmplList[0].data['SSC-A'], '.')
        self.ax.set_xscale('log')
        self.ax.set_yscale('log')
        self.ax.set_ylabel('SSC-A')
        self.ax.set_xlabel('FSC-A')
        self.mpl_canvas.draw()

    def handle_NewSession(self):
        QtCore.QProcess().startDetached('python ./main.py')

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    MainWindow = mainUi()
    MainWindow.show()
    sys.exit(app.exec_())

