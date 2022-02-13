from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import numpy as np

from PyQt5 import QtCore, QtGui

import sys
sys.path.insert(0, './FlowCal')
from FlowCal.plot import scatter2d, hist1d


class plotCanvas(FigureCanvasQTAgg):
    def __init__(self):
        self.fig, self.ax = plt.subplots()
        self.fig.set_tight_layout(True)
        super().__init__(self.fig)

        self.navigationBar = NavigationToolbar(self, self)
        self.setFocusPolicy(QtCore.Qt.ClickFocus)

        self.ax.set_xlabel('None')
        self.ax.set_ylabel('None')

        self.draw()

    def redraw(self, smplItems, chnlNames, axisNames, axScales, gateList=[], options=[0, 0], subSampleN=None):
        self.ax.clear()
        self.navigationBar.update()

        xChnl, yChnl = chnlNames

        plotType, normOption = options

        # gate the samples
        gatedSmpls = [] 
        for idx, smplItem in enumerate(smplItems):
            fcsData = smplItem.fcsSmpl

            inGateFlag = np.ones(fcsData.shape[0], dtype=bool)
            for gate in gateList:
                inGateFlag = np.logical_and(gate.isInsideGate(fcsData), inGateFlag)
            gatedSmpl = fcsData[inGateFlag, :]
            gatedSmpls.append(gatedSmpl)
                
        # Plot dots or histogram
        if plotType == 0:
            # plot dots
            for gatedSmpl, smplItem in zip(gatedSmpls, smplItems):
                scatter2d(gatedSmpl, self.ax, [xChnl, yChnl],
                          xscale=axScales[0], yscale=axScales[1],
                          color=smplItem.plotColor.getRgbF(), label=smplItem.displayName, s=1)

            self.ax.autoscale()

            self.ax.set_xlabel(axisNames[0])
            self.ax.set_ylabel(axisNames[1])

            self.ax.legend(markerscale=5)
        else:
            # plot histograme

            # set the 

            # plot
            for gatedSmpl, smplItem in zip(gatedSmpls, smplItems):
                hist1d(gatedSmpl, self.ax, xChnl, histtype='step',
                       xscale=axScales[0],
                       edgecolor=smplItem.plotColor.getRgbF(), label=smplItem.displayName)

            self.ax.autoscale()

            self.ax.set_xlabel(axisNames[0])
            self.ax.set_ylabel('Count')
        

        self.draw()
