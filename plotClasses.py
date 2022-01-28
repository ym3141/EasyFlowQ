import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import numpy as np

from PyQt5 import QtCore, QtGui

class plotCanvas(FigureCanvasQTAgg):
    def __init__(self):
        self.fig, self.ax = plt.subplots()
        self.fig.set_tight_layout(True)
        super().__init__(self.fig)

        self.navigationBar = NavigationToolbar(self, self)
        self.setFocusPolicy(QtCore.Qt.ClickFocus)

    def redraw(self, smpls, chnlNames, axisNames, axScales, params=None):
        self.ax.clear()
        self.navigationBar.update()

        xChnl, yChnl = chnlNames

        for idx, smpl in enumerate(smpls):
            self.ax.scatter(smpl.data[xChnl], smpl.data[yChnl], color='C'+str(idx%10), s=1, label=smpl.smplName)

        self.ax.legend(markerscale=5)
        self.ax.set_xscale(axScales[0])
        self.ax.set_yscale(axScales[1])
        self.ax.set_xlabel(axisNames[0])
        self.ax.set_ylabel(axisNames[1])

        self.draw()
