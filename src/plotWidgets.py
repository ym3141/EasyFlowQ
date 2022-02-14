from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import numpy as np

from PyQt5 import QtCore, QtGui

import sys

sys.path.insert(0, './FlowCal')
from FlowCal.plot import scatter2d, hist1d, _LogicleScale, _LogicleLocator, _LogicleTransform


class plotCanvas(FigureCanvasQTAgg):
    def __init__(self):
        self.fig, self.ax = plt.subplots()
        self.fig.set_tight_layout(True)
        super().__init__(self.fig)

        self.navigationBar = NavigationToolbar(self, self)
        self.setFocusPolicy(QtCore.Qt.ClickFocus)

        self.ax.set_xlabel('None')
        self.ax.set_ylabel('None')

        self.sampleRNG = rng = np.random.default_rng()

        self.draw()

    def redraw(self, smplItems, chnlNames, axisNames, axScales, gateList=[], perfModeN=None, options=[0, 0]):

        if len(smplItems) == 0:
            return

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
            if perfModeN:
                NperSmpl = int(perfModeN / len(gatedSmpls))
                for gatedSmpl, smplItem in zip(gatedSmpls, smplItems):
                    if len(gatedSmpl) > NperSmpl:
                        sampledIdx = self.sampleRNG.choice(NperSmpl, size=NperSmpl, replace=False, axis=0, shuffle=False)
                        sampledSmpl = gatedSmpl[sampledIdx, :]
                    else: 
                        sampledSmpl = gatedSmpl
                
                    scatter2d(sampledSmpl, self.ax, [xChnl, yChnl],
                            xscale=axScales[0], yscale=axScales[1],
                            color=smplItem.plotColor.getRgbF(), label=smplItem.displayName, s=1)

            else:
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
            xlim = [np.inf, -np.inf]
            for gatedSmpl, smplItem in zip(gatedSmpls, smplItems):

                xlim[0] = np.min([np.min(gatedSmpl[:, xChnl]), xlim[0]])
                xlim[1] = np.max([np.max(gatedSmpl[:, xChnl]), xlim[1]])

                hist1d_line(gatedSmpl, self.ax, xChnl, label=smplItem.displayName,
                            color=smplItem.plotColor.getRgbF(), xscale=axScales[0], normed_height=True)

            if axScales[0] == 'log':
                if xlim[0] <= 0:
                    xlim[0] = gatedSmpl.hist_bins(channels=xChnl, nbins=256, scale='log')[0]
            self.ax.set_xlim(xlim)

            self.ax.legend()
            self.ax.set_xlabel(axisNames[0])
            self.ax.set_ylabel('Density')
        

        self.draw()

def hist1d_line(data, ax, channel, xscale, color,
                bins=1024,
                normed_area=False,
                normed_height=False,
                label=''):

    xscale_kwargs = {}
    if xscale=='logicle':
        t = _LogicleTransform(data=data[:, channel], channel=channel)
        xscale_kwargs['T'] = t.T
        xscale_kwargs['M'] = t.M
        xscale_kwargs['W'] = t.W
    
    if hasattr(data, 'hist_bins') and hasattr(data.hist_bins, '__call__'):
            # If bins is None or an integer, get bin edges from
            # ``data_plot.hist_bins()``.
            if bins is None or isinstance(bins, int):
                bins = data.hist_bins(channels=channel, nbins=bins, scale=xscale, **xscale_kwargs)

    weights = None
    # Calculate weights if normalizing bins by height
    if normed_height and not normed_area:
        weights = np.ones_like(data[:, channel]) / float(len(data[:, channel]))

    # Plot
    n, edges = np.histogram(data[:, channel], bins=bins, weights=weights, density=normed_area)

    line = ax.plot((edges[1:] + edges[0:-1]) / 2, n, color=color, label=label)

    if xscale=='logicle':
        ax.set_xscale(xscale, data=data, channel=channel)
    else:
        ax.set_xscale(xscale)

    return n, edges, line


if __name__ == '__main__':
    QtCore.QProcess().startDetached('python ./main.py')