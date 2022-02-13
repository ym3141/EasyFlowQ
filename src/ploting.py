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
        else:
            # plot histograme

            # set the 
            for gatedSmpl, smplItem in zip(gatedSmpls, smplItems):
                hist1d(gatedSmpl, self.ax, xChnl, histtype='step',
                       xscale=axScales[0], edgecolor=smplItem.plotColor.getRgbF(), label=smplItem.displayName)

            self.ax.autoscale()

            self.ax.set_xlabel(axisNames[0])
            self.ax.set_ylabel(axisNames[1])

            pass
            
            # if axScales[0] == 'log':
            #     xDatamin = 10**(np.floor(np.log10(xDatamin)))
            #     xDatamax = 10**(np.ceil(np.log10(xDatamax)))
                
            #     for gatedSmpl, smpl in zip(gatedSmpls, smplItems): 
            #         hist, bins = np.histogram(gatedSmpl[xChnl], bins=np.geomspace(xDatamin, xDatamax, 1000))
            #         self.ax.plot((bins[0:-1] + bins[1:]) / 2, hist, color=smpl.plotColor.getRgbF(), label=smpl.displayName)
            # else:
            #     # A lin x-scale
            #     xDatamin = 0
            #     maxDigit = np.floor(np.log10(xDatamax))
            #     xDatamax = np.ceil(xDatamax / (10**maxDigit)) * (10**maxDigit)

            #     for gatedSmpl, smpl in zip(gatedSmpls, smplItems):
            #         hist, bins = np.histogram(gatedSmpl[xChnl], bins=np.linspace(xDatamin, xDatamax, 1000))
            #         self.ax.plot((bins[0:-1] + bins[1:]) / 2, hist, color=smpl.plotColor.getRgbF(), label=smpl.displayName)
            
            self.ax.set_xlabel(axisNames[0])
            self.ax.set_ylabel('Count')

        self.ax.legend(markerscale=5)
        self.ax.set_xscale(axScales[0])
        self.ax.set_yscale(axScales[1])
        

        self.draw()
