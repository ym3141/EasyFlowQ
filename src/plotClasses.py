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

    def redraw(self, smpls, chnlNames, axisNames, axScales, gateList=[], options=[0, 0], subSampleN=None):
        self.ax.clear()
        self.navigationBar.update()

        xChnl, yChnl = chnlNames

        plotType, normOption = options

        # get the min and max, for histogram
        xDatamin = np.inf
        xDatamax = 0

        # gate the samples
        gatedSmpls = []
        for idx, smpl in enumerate(smpls):
            fcsSmpl = smpl.fcsSmpl

            inGateFlag = np.ones(fcsSmpl.data.shape[0], dtype=bool)
            for gate in gateList:
                inGateFlag = np.logical_and(gate.isInsideGate(fcsSmpl), inGateFlag)
            gatedSmpl = fcsSmpl.data.loc[inGateFlag, :]
            gatedSmpls.append(gatedSmpl)

            # record the min/max if histogram
            if plotType == 1:
                xDatamin = np.min([xDatamin, np.min(gatedSmpl[xChnl])])
                xDatamax = np.max([xDatamax, np.max(gatedSmpl[xChnl])])
                

        # Plot dots or histogram
        if plotType == 0:
            # plot dots
            for gatedSmpl, smpl in zip(gatedSmpls, smpls):
                self.ax.scatter(gatedSmpl[xChnl], gatedSmpl[yChnl], 
                                color=smpl.plotColor.getRgbF(), s=1, label=smpl.displayName)
        else:
            # plot a histograme
            if axScales[0] == 'log':
                xDatamin = 10**(np.floor(np.log10(xDatamin)))
                xDatamax = 10**(np.ceil(np.log10(xDatamax)))

                hist, bins = np.histogram(gatedSmpl[xChnl], bins=np.geomspace(xDatamin, xDatamax, 1000))
                
                self.ax.plot((bins[0:-1] + bins[1:]) / 2, hist, color=smpl.plotColor.getRgbF(), label=smpl.displayName)
            else:
                # A lin x-scale
                xDatamin = 0
                maxDigit = np.floor(np.log10(xDatamax))
                xDatamax = np.ceil(xDatamax / (10**maxDigit)) * (10**maxDigit)

                hist, bins = np.histogram(gatedSmpl[xChnl], bins=np.linspace(xDatamin, xDatamax, 1000))
                self.ax.plot((bins[0:-1] + bins[1:]) / 2, hist, color=smpl.plotColor.getRgbF(), label=smpl.displayName)

        self.ax.legend(markerscale=5)
        self.ax.set_xscale(axScales[0])
        self.ax.set_yscale(axScales[1])
        self.ax.set_xlabel(axisNames[0])
        self.ax.set_ylabel(axisNames[1])

        self.draw()
