from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.ticker import PercentFormatter
import matplotlib.pyplot as plt

import numpy as np
from scipy.ndimage import gaussian_filter1d

from PyQt5 import QtCore, QtGui

from FlowCal.plot import scatter2d, hist1d, _LogicleScale, _LogicleLocator, _LogicleTransform
from .gates import quadrant, split

import warnings

quadrantTextProps = dict(boxstyle='square', facecolor='w', alpha=0.8)

class plotCanvas(FigureCanvasQTAgg):

    signal_AxLimsUpdated = QtCore.pyqtSignal(float, float, float, float)

    def __init__(self, dpiScale=None):
        self.fig, self.ax = plt.subplots()
        self.fig.set_tight_layout(True)

        if dpiScale:
            self.fig.dpi = self.fig.dpi * dpiScale
        else:
            self.fig.dpi = self.fig.dpi * 1.25
            
        super().__init__(self.fig)

        self.navigationBar = NavigationToolbar(self, self)
        self.setFocusPolicy(QtCore.Qt.ClickFocus)

        self.ax.set_xlabel('None')
        self.ax.set_ylabel('None')

        self.sampleRNG = np.random.default_rng()

        self.curPlotType = 'Dot plot'

        self.draw()

    # the function that draw
    def redraw(self, smplItems, chnlNames, axisNames, axScales, axRanges,
               gateList=[], quad_split=None,
               plotType = 'Dot plot',
               normOption = 'Percentage',
               perfModeN=None,
               smooth=0):


        self.curPlotType = plotType
        self.ax.clear()
        self.ax.autoscale(False)
        self.navigationBar.update()

        drawnQuadrant = False
        drawnSplit = False

        # only draw samples that has the specified channels
        smplItems = [a for a in smplItems if (chnlNames[0] in a.fcsSmpl.channels and chnlNames[1] in a.fcsSmpl.channels)] 

        # return if no sample to draw, call redraw to show blank
        if len(smplItems) == 0:
            self.draw()
            return []

        xChnl, yChnl = chnlNames

        # gate the samples
        gatedSmpls, gateFracs = self.gateSmpls(smplItems, gateList)
                
        # Plot dots or histogram
        if plotType == 'Dot plot':
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

            if isinstance(quad_split, quadrant):
                if quad_split.chnls[0] == xChnl and quad_split.chnls[1] == yChnl:
                # Only draw quadrant if requested, and the chnls match

                    totQs = np.zeros(4)
                    for gateSmpl in gatedSmpls:
                        totQs += quad_split.cellNs(gateSmpl)

                    qFracs = totQs / np.sum(totQs)
                    
                    self.ax.axvline(quad_split.center[0], linestyle = '--', color='k')
                    self.ax.axhline(quad_split.center[1], linestyle = '--', color='k')
                    
                    textingProps = {
                        'transform': self.ax.transAxes,
                        'fontsize': 'large',
                        'bbox': quadrantTextProps
                    }
                    self.ax.text(0.03, 0.03, '{:.2%}'.format(qFracs[0]), **textingProps)
                    self.ax.text(0.03, 0.97, '{:.2%}'.format(qFracs[1]), **textingProps, va='top')
                    self.ax.text(0.97, 0.03, '{:.2%}'.format(qFracs[2]), **textingProps, ha='right')
                    self.ax.text(0.97, 0.97, '{:.2%}'.format(qFracs[3]), **textingProps, va='top', ha='right')

                    drawnQuadrant = True

            self.ax.set_xlabel(axisNames[0])
            self.ax.set_ylabel(axisNames[1])

            
        elif plotType == 'Histogram':
            # plot histograme
            # record possible xlims for later use, if xlim is auto
            xlim_auto = [np.inf, -np.inf]
            for gatedSmpl, smplItem in zip(gatedSmpls, smplItems):

                n, edge, line = hist1d_line(gatedSmpl, self.ax, xChnl, label=smplItem.displayName,
                                            color=smplItem.plotColor.getRgbF(), xscale=axScales[0], normed_height=normOption, smooth=smooth)

                nonZeros = np.nonzero(n)
                if np.min(nonZeros) > 0:
                    minIdx = np.min(nonZeros) - 1
                else:
                    minIdx = np.min(nonZeros)

                if np.max(nonZeros) < len(nonZeros) - 1:
                    maxIdx = np.max(nonZeros) + 1
                else:
                    maxIdx = np.max(nonZeros)

                xlim_auto[0] = np.min([edge[minIdx], xlim_auto[0]])
                xlim_auto[1] = np.max([edge[maxIdx], xlim_auto[1]])

            if axScales[0] == 'log':
                if xlim_auto[0] <= 0:
                    xlim_auto[0] = gatedSmpl.hist_bins(channels=xChnl, nbins=256, scale='log')[0]

            if axScales[1] == 'logicle':
                self.ax.set_yscale('log')
            else:
                self.ax.set_yscale(axScales[1])

            if not (normOption == 'Cell count'):
                self.ax.yaxis.set_major_formatter(PercentFormatter(xmax=1))

            if isinstance(quad_split, split):
                totSs = np.zeros(2)
                for gateSmpl in gatedSmpls:
                    totSs += quad_split.cellNs(gateSmpl)

                sFracs = totSs / np.sum(totSs)
                self.ax.axvline(quad_split.splitValue, linestyle = '--', color='k')
                
                textingProps = {
                    'transform': self.ax.transAxes,
                    'fontsize': 'large',
                    'bbox': quadrantTextProps
                }
                self.ax.text(0.03, 0.97, '{:.2%}'.format(sFracs[0]), **textingProps, va='top')
                self.ax.text(0.97, 0.97, '{:.2%}'.format(sFracs[1]), **textingProps, va='top', ha='right')

                drawnSplit = True

            self.ax.set_xlabel(axisNames[0])
            self.ax.set_ylabel(normOption)

        # deal with xlim and ylim            
        xmin, xmax, ymin, ymax = axRanges
        if xmin == 'auto' or xmax =='auto':
            if plotType == 'Histogram':
                self.ax.set_xlim(xlim_auto)
            else:
                self.ax.autoscale(True, 'x')
        else:
            self.ax.set_xlim([xmin, xmax])

        if ymin == 'auto' or ymax == 'auto':
            self.ax.autoscale(True, 'y')
        else:
            self.ax.set_ylim([ymin, ymax])
    
        
        if len(smplItems) < 12:
            if drawnQuadrant:
                # if a quadrant is drawn, instruct legend will try to avoid the texts
                self.ax.legend(markerscale=5, loc='best', bbox_to_anchor=(0, 0.1, 1, 0.8))
            elif drawnSplit:
                self.ax.legend(markerscale=5, loc='best', bbox_to_anchor=(0, 0, 1, 0.9))
            else:
                self.ax.legend(markerscale=5)
            
        self.draw()
        self.signal_AxLimsUpdated.emit(*self.ax.get_xlim(), *self.ax.get_ylim())

        return list(zip(smplItems, gatedSmpls, gateFracs))

    def gateSmpls(self, smplItems, gateList):
        #gate samples with a list of gate:

        gatedSmpls = []
        gateFracs = []
        for idx, smplItem in enumerate(smplItems):
            
            fcsData = smplItem.fcsSmpl
            inGateFlag = np.ones(fcsData.shape[0], dtype=bool)

            fracInEachGate = []

            for gate in gateList:

                if gate.chnls[0] in fcsData.channels and gate.chnls[1] in fcsData.channels:

                    newFlag = gate.isInsideGate(fcsData)

                    fracInParent = np.sum(np.logical_and(newFlag, inGateFlag)) / np.sum(inGateFlag)
                    fracInEachGate.append(fracInParent)

                    inGateFlag = np.logical_and(gate.isInsideGate(fcsData), inGateFlag)

                else: 
                    warnings.warn('Sample does not have channel(s) for this gate, skipping this gate', RuntimeWarning)
                    fracInEachGate.append(1.0)
            
            gateFracs.append(fracInEachGate)

            gatedSmpl = fcsData[inGateFlag, :]
            gatedSmpls.append(gatedSmpl)
        
        return gatedSmpls, gateFracs

    def updateAxLims(self, xmin=None, xmax=None, ymin=None, ymax=None):
        # self.ax.autoscale()

        if not (xmin is None or xmax is None):
            if xmin == 'auto' or xmax == 'auto':
                self.ax.autoscale(True, axis='x')
                self.signal_AxLimsUpdated.emit(*self.ax.get_xlim(), *self.ax.get_ylim())
            else:
                self.ax.set_xlim([xmin, xmax])

        if not (ymin is None or ymax is None):
            if ymin == 'auto' or ymax == 'auto':
                self.ax.autoscale(True, axis='y')
                self.signal_AxLimsUpdated.emit(*self.ax.get_xlim(), *self.ax.get_ylim())
            else:
                self.ax.set_ylim([ymin, ymax])

        self.draw()
    

def hist1d_line(data, ax, channel, xscale, color,
                bins=1024,
                normed_height=False,
                label='',
                smooth=0):

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

    # Calculate weights if normalizing bins by height
    if normed_height == 'Percentage':
        weights = np.ones_like(data[:, channel]) / float(len(data[:, channel]))
    elif normed_height == 'Percentage of total':
        weights = np.ones_like(data[:, channel]) / float(int(data.text['$TOT']))
    else:
        weights = None

    # Plot
    n, edges = np.histogram(data[:, channel], bins=bins, weights=weights)

    if smooth:
        n = gaussian_filter1d(n, sigma=smooth/16)

    line = ax.plot((edges[1:] + edges[0:-1]) / 2, n, color=color, label=label)

    if xscale=='logicle':
        ax.set_xscale(xscale, data=data, channel=channel)
    else:
        ax.set_xscale(xscale)

    return n, edges, line


if __name__ == '__main__':
    QtCore.QProcess().startDetached('python ./main.py')