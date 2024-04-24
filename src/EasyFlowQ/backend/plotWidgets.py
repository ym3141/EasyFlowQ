from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.ticker import PercentFormatter
import matplotlib.transforms as transforms
import matplotlib.pyplot as plt

import numpy as np
from scipy.ndimage import gaussian_filter1d, uniform_filter1d

from PyQt5 import QtCore, QtGui

from ..FlowCal.plot import scatter2d, density2d, hist1d, _LogicleScale, _LogicleLocator, _LogicleTransform
from ..FlowCal.io import FCSData
from .gates import quadrant, split, polygonGate, lineGate

import warnings

# Macros
quadrantTextProps = dict(boxstyle='square', facecolor='w', alpha=0.8)

polygonGateStyle = {
    'marker': 's',
    'ls': '-.',
    'markerfacecolor': 'w',
    'markersize': 5,
    'color': 'gray'
}

lineGateStyle = {
    'marker':'|', 
    'markerfacecolor':'w',
    'markersize':5,
    'color':'gray'
}

dotSizeDict = {
    'Smaller': 1.7,
    'Small' : 3,
    'Regular': 5,
    'Big': 7,
    'Bigger': 10
}

class cachedStats():
    def __init__(self) -> None:
        self.smplItems = []
        self.gatedSmpls = []
        self.gatedFracs = [[]]
        self.selectedGateItem = None

        self.quadFracs = []
        self.splitFracs = []
        self.chnls = []

    @property
    def smplNumber(self):
        return len(self.smplItems)

class plotCanvas(FigureCanvasQTAgg):

    signal_AxLimsUpdated = QtCore.pyqtSignal(float, float, float, float)
    signal_PlotUpdated = QtCore.pyqtSignal(cachedStats)

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

        self.curPlotType = 'Dot plot'

        # varables to indicate if there is an anotation drawn
        self.drawnQuadrant = False
        self.drawnSplit = False
        self.drawnGates = False

        self.cachedPlotStats = cachedStats()
        self.draw()

    # the function that draw
    def redraw(
        self, smplItems, chnls, axisNames, axScales, axRanges,
        compValues,
        gateList=[], quad_split=None,
        plotType = 'Dot plot',
        normOption = 'Percentage',
        perfModeN=None, legendOps=1, smooth=0,
        selectedGateItem=None,
        dotSize = 0, dotOpacity = 0.8
        ):

        self.curPlotType = plotType
        self.ax.clear()
        self.ax.autoscale(False)
        self.navigationBar.update()

        self.drawnQuadrant = False
        self.drawnSplit = False
        self.drawnGates = False

        qFracs = []
        sFracs = []

        # only draw samples that has the specified channels
        xChnl, yChnl = chnls
        smplItems = [a for a in smplItems if (xChnl in a.fcsSmpl.channels and yChnl in a.fcsSmpl.channels)] 
        smpls = [smpl.fcsSmpl for smpl in smplItems]
        
        # return if no sample to draw, call redraw to show blank
        if len(smplItems) == 0:
            self.draw()
            return []

        # apply the comp
        if not compValues is None:
            compedSmpls = self.compSmpls(smpls, compValues)
        else:
            compedSmpls = smpls

        # gate the samples
        if selectedGateItem is None:
            _gateList = gateList
            gatedSmpls, gateFracs, inGateFlags = gateSmpls(compedSmpls, _gateList)
        else:
            _gateList = gateList + [selectedGateItem.gate]
            gatedSmpls, gateFracs, inGateFlags = gateSmpls(compedSmpls, _gateList, lastGateStatOnly=True)
                
        # Plot dots, histogram or density plot
        if plotType == 'Dot plot' or plotType == 'Density plot':
            # plot dots and density plot
            self.cachedPlotStats.chnls = chnls
            dotAlpha = dotOpacity / 100

            if plotType == 'Dot plot':
                shorthand_scatter2d = lambda smpl, smplItem : scatter2d(smpl, self.ax, [xChnl, yChnl], xscale=axScales[0], yscale=axScales[1],
                                                                        color=smplItem.plotColor.getRgbF(), label=smplItem.displayName, 
                                                                        s=dotSizeDict[dotSize], alpha=dotAlpha, linewidths=0)
                if perfModeN:
                    NperSmpl = int(perfModeN / len(gatedSmpls))
                    for gatedSmpl, smplItem in zip(gatedSmpls, smplItems):
                        if len(gatedSmpl) > NperSmpl:
                            sampleRNG = np.random.default_rng(42)
                            sampledIdx = sampleRNG.choice(len(gatedSmpl), size=NperSmpl, replace=False, axis=0, shuffle=False)
                            sampledSmpl = gatedSmpl[sampledIdx, :]
                        else: 
                            sampledSmpl = gatedSmpl
                    
                        shorthand_scatter2d(sampledSmpl, smplItem)
                else:
                    for gatedSmpl, smplItem in zip(gatedSmpls, smplItems):
                        shorthand_scatter2d(gatedSmpl, smplItem)
            
            elif plotType == 'Density plot':
                # Combine all the selected samples
                if len(gatedSmpls) > 1:
                    allSmplCombined = np.vstack([smpl[:, [xChnl, yChnl]] for smpl in gatedSmpls])
                    allSmplCombined = FCSData_from_array(gatedSmpls[0][:, [xChnl, yChnl]], allSmplCombined)
                    plotLabel = 'All Selected Samples'
                else:
                    allSmplCombined = gatedSmpls[0][:, [xChnl, yChnl]]
                    plotLabel = smplItems[0].displayName

                if perfModeN and len(allSmplCombined) > perfModeN:
                    sampleRNG = np.random.default_rng(42)
                    sampledIdx = sampleRNG.choice(len(allSmplCombined), size=perfModeN, replace=False, axis=0, shuffle=False)
                    sampledSmpl = allSmplCombined[sampledIdx, :]
                else: 
                    sampledSmpl = allSmplCombined
                
                density2d(sampledSmpl, self.ax, [xChnl, yChnl], mode='scatter', cmap='plasma', s=dotSizeDict[dotSize], alpha=dotAlpha, 
                            xscale=axScales[0], yscale=axScales[1], label = plotLabel, bins=256, smooth=smooth)
                

            if isinstance(quad_split, quadrant):
            # Draw quadrant if selected
                if quad_split.chnls[0] == xChnl and quad_split.chnls[1] == yChnl:
                # Only draw quadrant if requested, and the chnls match
                    qFracs = np.zeros((len(gatedSmpls), 4))

                    for idx, gatedSmpl in enumerate(gatedSmpls):
                        qFracs[idx] = np.array(quad_split.cellNs(gatedSmpl)) / gatedSmpl.shape[0]

                    self.ax.axvline(quad_split.center[0], linestyle = '--', color='k')
                    self.ax.axhline(quad_split.center[1], linestyle = '--', color='k')
                    
                    textingProps = {
                        'transform': self.ax.transAxes,
                        'fontsize': 'large',
                        'bbox': quadrantTextProps
                    }
                    self.ax.text(0.03, 0.03, '{:.2%}'.format(qFracs[:, 0].mean()), **textingProps)
                    self.ax.text(0.03, 0.97, '{:.2%}'.format(qFracs[:, 1].mean()), **textingProps, va='top')
                    self.ax.text(0.97, 0.03, '{:.2%}'.format(qFracs[:, 2].mean()), **textingProps, ha='right')
                    self.ax.text(0.97, 0.97, '{:.2%}'.format(qFracs[:, 3].mean()), **textingProps, va='top', ha='right')

                    self.drawnQuadrant = True
            
            if (not selectedGateItem is None) and isinstance(selectedGateItem.gate, polygonGate):
            # draw gate if selected
                selectedGate = selectedGateItem.gate
                if selectedGate.chnls == chnls:
                    xydata = np.vstack([selectedGate.verts, selectedGate.verts[0, :]])
                    self.ax.plot(xydata[:, 0], xydata[:, 1], **polygonGateStyle)
                    self.drawnGates = True

                    if len(gatedSmpls) == 1:
                        inGateFracText = '{:.2%}'.format(gateFracs[0][-1])
                    else:
                        inGateFracText = 'N/A'

                    UR_point = np.max(selectedGate.verts, axis=0)
                    self.ax.annotate('Gate: {0} \n({1})'.format(selectedGateItem.text(), inGateFracText), 
                                     xy=UR_point, textcoords='offset points', xytext=(-20, -10), 
                                     bbox=dict(facecolor='w', alpha=0.3, edgecolor='w'),
                                     horizontalalignment='right', verticalalignment='top', annotation_clip=True)
                pass

            self.ax.set_xlabel(axisNames[0])
            self.ax.set_ylabel(axisNames[1])

        elif plotType == 'Histogram':
            # plot histograme
            # record possible xlims for later use, if xlim is auto
            self.cachedPlotStats.chnls = [xChnl]

            xlim_auto = [np.inf, -np.inf]
            ymax_histo = 0
            for gatedSmpl, smplItem in zip(gatedSmpls, smplItems):
                if gatedSmpl.shape[0] < 1:
                    continue

                n, edge, line = hist1d_line(gatedSmpl, self.ax, xChnl, label=smplItem.displayName,
                                            color=smplItem.plotColor.getRgbF(), xscale=axScales[0], normed_height=normOption, smooth=smooth)
                
                # Find the proper ylims and xlims
                ymax_histo = max([max(n), ymax_histo])

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

            # likely no data drawn
            if xlim_auto == [np.inf, -np.inf]:
                xlim_auto = [1, 1e7]

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
                if quad_split.chnl == xChnl:
                    sFracs = np.zeros((len(gatedSmpls),2))
                    for idx, gatedSmpl in enumerate(gatedSmpls):
                        sFracs[idx] = np.array(quad_split.cellNs(gatedSmpl)) / gatedSmpl.shape[0]

                    self.ax.axvline(quad_split.splitValue, linestyle = '--', color='k')
                    
                    textingProps = {
                        'transform': self.ax.transAxes,
                        'fontsize': 'large',
                        'bbox': quadrantTextProps
                    }
                    self.ax.text(0.03, 0.97, '{:.2%}'.format(sFracs[:, 0].mean()), **textingProps, va='top')
                    self.ax.text(0.97, 0.97, '{:.2%}'.format(sFracs[:, 1].mean()), **textingProps, va='top', ha='right')

                    self.drawnSplit = True
            
            if (not selectedGateItem is None) and isinstance(selectedGateItem.gate, lineGate):
            # draw gate if selected
                selectedGate = selectedGateItem.gate
                if selectedGate.chnl == chnls[0]:
                    self.ax.plot(selectedGate.ends, [0.5 * ymax_histo, 0.5 * ymax_histo], **lineGateStyle)
                    self.drawnGates = True

                    if len(gatedSmpls) == 1:
                        inGateFracText = '{:.2%}'.format(gateFracs[0][-1])
                    else:
                        inGateFracText = 'N/A'

                    self.ax.annotate('Gate: {0} \n({1})'.format(selectedGateItem.text(), inGateFracText), 
                                     xy=[np.mean(selectedGate.ends), 0.5 * ymax_histo], textcoords='offset points', xytext=(10, 25), 
                                     bbox=dict(facecolor='w', alpha=0.3, edgecolor='w'),
                                     horizontalalignment='right', verticalalignment='top', annotation_clip=True)
                    
                    xlim_auto[0] = np.min([selectedGate.ends[0], xlim_auto[0]])
                    xlim_auto[1] = np.max([selectedGate.ends[1], xlim_auto[1]])
                pass

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

        # draw legends
        if legendOps == 2 or (legendOps == 1 and len(smplItems) < 12):
            if self.drawnQuadrant:
                # if a quadrant is drawn, instruct legend will try to avoid the texts
                self.ax.legend(markerscale=5, loc='best', bbox_to_anchor=(0, 0.1, 1, 0.8))
            elif self.drawnSplit:
                self.ax.legend(markerscale=5, loc='best', bbox_to_anchor=(0, 0, 1, 0.9))
            else:
                self.ax.legend(markerscale=5)
            
        self.draw()
        self.signal_AxLimsUpdated.emit(*self.ax.get_xlim(), *self.ax.get_ylim())

        # Update the cached stats, and evoke the signal
        self.cachedPlotStats.smplItems = smplItems
        self.cachedPlotStats.gatedSmpls = gatedSmpls
        self.cachedPlotStats.gatedFracs = gateFracs
        self.cachedPlotStats.quadFracs = qFracs
        self.cachedPlotStats.splitFracs = sFracs
        self.cachedPlotStats.selectedGateItem = selectedGateItem
        self.signal_PlotUpdated.emit(self.cachedPlotStats)

    def compSmpls(self, smpls, compValues):
        compedSmpls = []

        # check if comp channels matches smpl channel; if not create a new autoF and compMat based on the required
        for smpl in smpls:
            if compValues[0] == list(smpl.channels):
                compMat = np.linalg.inv(compValues[2] / 100)
                autoFVector = np.array(compValues[1]).T

            else:
                tempAutoF = compValues[1].loc[list(smpl.channels)]
                tempCompM = compValues[2][list(smpl.channels)].loc[list(smpl.channels)]
                compMat = np.linalg.inv(tempCompM / 100)
                autoFVector = np.array(tempAutoF).T

            compedSmpl = (smpl - autoFVector) @ compMat + autoFVector
            compedSmpls.append(compedSmpl)
        return compedSmpls

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

# Quick and dirty way of creating a FCSData from an numpy array
# Use cautionously, this clase does not check if the created FCSData files are self-consistant
class FCSData_from_array(FCSData):

    # This copys all attributes from the "templet"
    def __new__(cls, template, np_array):
        # Get data from fcs_file object
        obj = np_array.view(cls)

        # Add FCS file attributes
        obj._infile = 'N/A'
        obj._text = template._text
        obj._analysis = template._analysis

        # Add channel-independent attributes
        obj._data_type = template._data_type
        obj._time_step = template._time_step
        obj._acquisition_start_time = template._acquisition_start_time
        obj._acquisition_end_time = template._acquisition_end_time

        # Add channel-dependent attributes
        obj._channels = template._channels
        obj._amplification_type = template._amplification_type
        obj._detector_voltage = template._detector_voltage
        obj._amplifier_gain = template._amplifier_gain
        obj._channel_labels = template._channel_labels
        obj._range = template._range
        obj._resolution = template._resolution

        return obj


def gateSmpls(smpls, gateList, lastGateStatOnly=False):
    #gate samples with a list of gate:

    gatedSmpls = []
    gateFracs = []
    inGateFlags = []
    for idx, fcsData in enumerate(smpls):
        
        inGateFlag = np.ones(fcsData.shape[0], dtype=bool)
        fracInEachGate = []

        for idx, gate in enumerate(gateList):

            if gate.chnls[0] in fcsData.channels and gate.chnls[1] in fcsData.channels:

                newFlag = gate.isInsideGate(fcsData)

                if np.sum(inGateFlag) > 0:
                    fracInParent = np.sum(np.logical_and(newFlag, inGateFlag)) / np.sum(inGateFlag)
                else:
                    fracInParent = float('nan')
                fracInEachGate.append(fracInParent)

                if lastGateStatOnly and idx == len(gateList) - 1:
                    pass
                else:
                    inGateFlag = np.logical_and(gate.isInsideGate(fcsData), inGateFlag)

            else: 
                warnings.warn('Sample does not have channel(s) for this gate, skipping this gate', RuntimeWarning)
                fracInEachGate.append(1.0)
        
        gateFracs.append(fracInEachGate)

        gatedSmpl = fcsData[inGateFlag, :]
        gatedSmpls.append(gatedSmpl)
        inGateFlags.append(inGateFlag)
    
    return gatedSmpls, gateFracs, inGateFlags

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
        uniformFilterSize = int(smooth / 8) * 2 + 1 # make sure it's a ood intiger. Does not kick in till smooth = 16
        n = uniform_filter1d(n, size=uniformFilterSize, mode='nearest')
        n = gaussian_filter1d(n, sigma=smooth/16)

    line = ax.plot((edges[1:] + edges[0:-1]) / 2, n, color=color, label=label)

    if xscale=='logicle':
        ax.set_xscale(xscale, data=data, channel=channel)
    else:
        ax.set_xscale(xscale)

    return n, edges, line


if __name__ == '__main__':
    QtCore.QProcess().startDetached('python ./main.py')