from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.ticker import PercentFormatter
from matplotlib.figure import Figure
import matplotlib.transforms as transforms

# import the necessary backend for saving figures (for pyinstaller)
import matplotlib.backends.backend_pdf
import matplotlib.backends.backend_ps
import matplotlib.backends.backend_svg
import matplotlib.backends.backend_pgf

import numpy as np
import io
from scipy.ndimage import gaussian_filter1d, uniform_filter1d
from scipy.interpolate import interpn
from scipy.stats import gaussian_kde

from PySide6 import QtCore, QtWidgets, QtGui

from ..FlowCal.plot import scatter2d, hist1d, _LogicleScale, _LogicleLocator, _LogicleTransform
from ..FlowCal.io import FCSData
from .gates import quadrant, split, polygonGate, lineGate
from .ioData import FCSData_ef

import warnings
import time

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

    signal_AxLimsUpdated = QtCore.Signal(object, object)
    signal_PlotUpdated = QtCore.Signal(cachedStats)

    to_load_session = QtCore.Signal(str)

    def __init__(self, dpiScale=None):
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.fig.set_layout_engine("tight") 

        if dpiScale:
            self.fig.dpi = self.fig.dpi * dpiScale
        else:
            self.fig.dpi = self.fig.dpi * 1.25
            
        super().__init__(self.fig)

        self.navigationBar = efNavigationToolbar(self, self)
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.setAcceptDrops(True)


        self.ax.set_xlabel('None')
        self.ax.set_ylabel('None')

        self.curPlotType = 'Dot plot'

        # varables to indicate if there is an anotation drawn
        self.drawnQuadrant = False
        self.drawnSplit = False
        self.drawnGates = False

        self.legend = None

        self.cachedPlotStats = cachedStats()
        self.draw_counter = 0
        self.draw_idle()

    # the function that draw
    def redraw(
        self, smplItems, chnls, axisNames, axScales, axRanges,
        compValues,
        gateList=[], quad_split=None,
        plotType = 'Dot plot',
        normOption = 'Unit Area',
        perfModeN=None, legendOps=QtCore.Qt.PartiallyChecked, gatePercOps=True, smooth=0,
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
        lines = []

        # only draw samples that has the specified channels
        xChnl, yChnl = chnls
        smplItems = [a for a in smplItems if (xChnl in a.fcsSmpl.channels and yChnl in a.fcsSmpl.channels)] 
        smpls = [smpl.fcsSmpl for smpl in smplItems]
        
        # return if no sample to draw, call redraw to show blank
        if len(smplItems) == 0:
            self.draw_idle()
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

        if [len(smpl) for smpl in gatedSmpls] == [0] * len(gatedSmpls):
            self.draw_idle()
            return None

                
        # Plot dots, histogram or density plot
        if plotType == 'Dot plot' or plotType == 'Density plot':
            # plot dots and density plot
            self.cachedPlotStats.chnls = chnls
            dotAlpha = dotOpacity / 100

            if plotType == 'Dot plot':
                plot_dots = lambda smpl, smplItem : self.ax.plot(smpl[:, xChnl], smpl[:, yChnl], '.', mew=0,
                                                                 color=smplItem.plotColor.getRgbF(), label=smplItem.displayName, 
                                                                 ms=dotSizeDict[dotSize], alpha=dotAlpha)
                if perfModeN:
                    NperSmpl = int(perfModeN / len(gatedSmpls))
                    for gatedSmpl, smplItem in zip(gatedSmpls, smplItems):
                        if len(gatedSmpl) > NperSmpl:
                            sampleRNG = np.random.default_rng(42)
                            sampledIdx = sampleRNG.choice(len(gatedSmpl), size=NperSmpl, replace=False, axis=0, shuffle=False)
                            sampledSmpl = gatedSmpl[sampledIdx, :]
                        else: 
                            sampledSmpl = gatedSmpl
                    
                        plot_dots(sampledSmpl, smplItem)
                else:
                    for gatedSmpl, smplItem in zip(gatedSmpls, smplItems):
                        plot_dots(gatedSmpl, smplItem)
            
            elif plotType == 'Density plot':

                sampledSmpl, smplMask, cmap = self.density_by_kde(gatedSmpls, xChnl, yChnl, axScales, perfModeN)

                # determine the proper label for the legend
                if len(gatedSmpls) > 1:
                    plotLabel = 'All Selected Samples'
                else:
                    plotLabel = smplItems[0].displayName

                # plotting
                scatter2d(sampledSmpl[smplMask, :], self.ax, channels=[xChnl, yChnl], 
                          c=cmap, xscale=axScales[0], yscale=axScales[1],
                          cmap = 'plasma', label=plotLabel, s=dotSizeDict[dotSize], alpha=dotAlpha, linewidths=0)

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

                    if len(gatedSmpls) < 5 and gatePercOps:
                        inGateFracText = []
                        for idx in range(len(gatedSmpls)):
                            if len(smplItems[idx].displayName) > 20:
                                smplDisplayName = smplItems[idx].displayName[0:20] + '...'
                            else:
                                smplDisplayName = smplItems[idx].displayName
                            inGateFracText.append('\n{1}: {0:7.2%}'.format(gateFracs[idx][-1], smplDisplayName))
                        inGateFracText = ''.join(inGateFracText)

                    else:
                        inGateFracText = ''

                    UR_point = np.max(selectedGate.verts, axis=0)
                    self.ax.annotate('Gate: {0}{1}'.format(selectedGateItem.text(), inGateFracText), 
                                     xy=UR_point, textcoords='offset points', xytext=(-20, -10), 
                                     bbox=dict(facecolor='w', alpha=0.3, edgecolor='w'),
                                     horizontalalignment='right', verticalalignment='top', annotation_clip=True)
                pass

            self.ax.set_xlabel(axisNames[0])
            self.ax.set_ylabel(axisNames[1])

            # re-adjust the lims if logicle scale is used, because logicle scale limit the lower limit based on the last sample
            if axScales[0] == 'logicle':
                if axRanges[0] == 'auto':
                    self.ax.set_xscale('logicle', data=gatedSmpls, channel=chnls[0])
                else:
                    # Get T (max value) and min_neg (min negative value) from user defined limits
                    min_neg = min(0, axRanges[0][0])
                    self.ax.set_xscale('logicle', data=gatedSmpls, channel=chnls[0], min_neg=min_neg, T=axRanges[0][1])
            else:
                self.ax.set_xscale(axScales[0])

            if axScales[1] == 'logicle':
                if axRanges[1] == 'auto':
                    self.ax.set_yscale('logicle', data=gatedSmpls, channel=chnls[1])
                else:
                    min_neg = min(0, axRanges[1][0])
                    self.ax.set_yscale('logicle', data=gatedSmpls, channel=chnls[1], min_neg=min_neg, T=axRanges[1][1])
            else:
                self.ax.set_yscale(axScales[1])

            self.updateAxLims(axRanges[0], axRanges[1])

        elif plotType in ('Histogram', 'Stacked histo', 'Aggregated histo'):
        # plot histograme
            self.cachedPlotStats.chnls = [xChnl]

            # record possible xlims for later use, if xlim is auto
            xlim_auto = [np.inf, -np.inf]
            # record the maximum height of the histogram, this is for drawing the gate
            ymax_histo = 0

            # recorded all the hights, edges and lines
            ns, edges, lines = [], [], []

            smplNames = [smplItem.displayName for smplItem in smplItems]
            smplColors = [smplItem.plotColor.getRgbF() for smplItem in smplItems]
            
            if plotType == 'Aggregated histo':
                # if the plot type is aggregated, then we need to combine all the samples

                aggregatedSmpl = FCSData_ef.fromArray(gatedSmpls[0], np.vstack(gatedSmpls))
                smplNames = ['Aggregated sample']
                smplColors = [smplItems[0].plotColor.getRgbF()]

                        
            smpls_to_plot = gatedSmpls if plotType != 'Aggregated histo' else [aggregatedSmpl]
            for gatedSmpl, smplName, smplColor in zip(smpls_to_plot, smplNames, smplColors):
                if gatedSmpl.shape[0] < 1:
                    continue

                n, edge, line = hist1d_line(gatedSmpl, self.ax, xChnl, label=smplName,
                                            color=smplColor, xscale=axScales[0], normed_height=normOption, smooth=smooth)

                ns.append(n)
                edges.append(edges)
                lines.append(line[0])

            if plotType == 'Histogram' or plotType == 'Aggregated histo':
                ymax_histo = max([np.max(ns), ymax_histo]) * 1.1

            else:  # It's stacked histogram
                yShift = np.max(ns) * 0.5
                ymax_histo = yShift * (len(ns) + 1.1)

                for idx, line in enumerate(lines):
                    xdata = line.get_xdata()
                    ydata = line.get_ydata()
                    line.set_data(xdata, ydata + yShift * idx)

                    self.ax.fill_between(xdata, ydata + yShift * idx, yShift * idx, color=line.get_color(), alpha=0.3)

            # calculate the xlims based on the data
            nonZerosList = [np.nonzero(n) for n in ns]
            minIdx = max(np.hstack(nonZerosList).min() - 1, 0)
            maxIdx = min(np.hstack(nonZerosList).max() + 1, len(ns[0]) - 1)

            xlim_auto[0] = np.min([edge[minIdx], xlim_auto[0]])
            xlim_auto[1] = np.max([edge[maxIdx], xlim_auto[1]])

            # likely no data drawn
            if xlim_auto == [np.inf, -np.inf]:
                xlim_auto = [1, 1e7]

            if axScales[0] == 'log':
                if xlim_auto[0] <= 0:
                    xlim_auto[0] = gatedSmpl.hist_bins(channels=xChnl, nbins=256, scale='log')[0]
            elif axScales[0] == 'logicle':
                # re-adjust the xlims if logicle scale is used, because logicle scale limit the right limit based on the last sample
                # This ensures the logical scale limits are based on all the data
                if axRanges[0] == 'auto':
                    self.ax.set_xscale('logicle', data=gatedSmpls, channel=xChnl)
                else:
                    min_neg = min(0, axRanges[0][0])
                    self.ax.set_xscale('logicle', data=gatedSmpls, channel=xChnl, min_neg=min_neg, T=axRanges[0][1])

            # force the y axis to be log scale if logicle is used
            if axScales[1] == 'logicle':
                self.ax.set_yscale('log')
            else:
                self.ax.set_yscale(axScales[1])


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

                    if len(gatedSmpls) <= 5 and gatePercOps:
                        inGateFracText = []
                        for idx in range(len(gatedSmpls)):
                            if len(smplItems[idx].displayName) > 20:
                                smplDisplayName = smplItems[idx].displayName[0:20] + '...'
                            else:
                                smplDisplayName = smplItems[idx].displayName
                            inGateFracText.append('\n{1}: {0:7.2%}'.format(gateFracs[idx][-1], smplDisplayName))
                        inGateFracText = ''.join(inGateFracText)
                    else:
                        inGateFracText = ''

                    self.ax.annotate('Gate: {0}{1}'.format(selectedGateItem.text(), inGateFracText), 
                                     xy=[selectedGate.ends[1], 0.5 * ymax_histo], textcoords='offset points', xytext=(-2, 2), 
                                     bbox=dict(facecolor='w', alpha=0.3, edgecolor='w'),
                                     horizontalalignment='right', verticalalignment='bottom', annotation_clip=True)
                    

            self.ax.set_xlabel(axisNames[0])
            self.ax.set_ylabel(normOption)

            # replace the xlims if it is auto, with calculated xlims
            xlim = xlim_auto if axRanges[0] == 'auto' else axRanges[0]
            ylim = [0, ymax_histo] if axRanges[1] == 'auto' else axRanges[1]
            self.updateAxLims(xlim, ylim)


        # draw legends and annotations in statcked histograms
        if legendOps is QtCore.Qt.Checked or (legendOps is QtCore.Qt.PartiallyChecked and len(smplItems) < 12) or plotType == 'Aggregated histo':
            self.legend = None
            if plotType == 'Stacked histo' and len(lines) > 0:
                for idx, line in enumerate(lines):
                    yshift_text = idx / (len(lines) + 1)
                    self.ax.annotate(
                        line.get_label(), xy=(1, yshift_text), bbox=dict(facecolor='w', alpha=0.4, edgecolor='w'),
                        horizontalalignment='right', verticalalignment='bottom', xycoords='axes fraction'
                    )
            elif self.drawnQuadrant:
                # if a quadrant is drawn, instruct legend will try to avoid the texts
                self.legend = self.ax.legend(markerscale=5, loc='best', bbox_to_anchor=(0, 0.1, 1, 0.8))
            elif self.drawnSplit:
                self.legend = self.ax.legend(markerscale=5, loc='best', bbox_to_anchor=(0, 0, 1, 0.9))
            else:
                self.legend = self.ax.legend(markerscale=5)

            if not self.legend is None:
                self.legend.set_draggable(True)

        # hide the y axis ticks if it is a stacked histogram
        if plotType == 'Stacked histo':
            self.ax.set_yticks([], [])            
        
        self.draw_idle()
        self.signal_AxLimsUpdated.emit(self.ax.get_xlim(), self.ax.get_ylim())

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
            # get the channels that are not derived parameters (the derived parameters are always at the end)
            chnls_no_drvd = smpl.channels_no_drved

            # test if the compValue and sample has the same channels and order
            if compValues[0:len(chnls_no_drvd)] == list(chnls_no_drvd):
                compMat = np.linalg.inv(compValues[2] / 100)
                autoFVector = np.array(compValues[1]).T
            
            # if not, create a new autoF and compMat based on sample's order
            else:
                tempAutoF = compValues[1].loc[list(chnls_no_drvd)]
                tempCompM = compValues[2][list(chnls_no_drvd)].loc[list(chnls_no_drvd)]
                compMat = np.linalg.inv(tempCompM / 100)
                autoFVector = np.array(tempAutoF).T

            # expand the autoFVector and compMat if needed for are derived parameters
            if len(smpl.drvedParamNames) > 0:
                autoFVectorFiller = np.zeros((1, len(smpl.channels)))
                autoFVectorFiller[:, :autoFVector.shape[1]] = autoFVector
                autoFVector = autoFVectorFiller
                compMatFiller = np.diag(np.ones(len(smpl.channels)))
                compMatFiller[:compMat.shape[0], :compMat.shape[1]] = compMat
                compMat = compMatFiller

            compedSmpl = (smpl - autoFVector) @ compMat + autoFVector
            compedSmpls.append(compedSmpl)
        return compedSmpls

    def density_by_kde(self, gatedSmpls, xChnl, yChnl, axScales, perfModeN, kde_size=1024):

        # Combine all the gated samples for density estimation. 
        if len(gatedSmpls) > 1:
            allSmplCombined = np.vstack([smpl[:, [xChnl, yChnl]] for smpl in gatedSmpls])
            allSmplCombined = FCSData_ef.fromArray(gatedSmpls[0][:, [xChnl, yChnl]], allSmplCombined)
        else:
            allSmplCombined = gatedSmpls[0][:, [xChnl, yChnl]]

        # Subsample the data if the "performance/normalize mode" is enabled 
        if perfModeN and len(allSmplCombined) > perfModeN:
            sampleRNG = np.random.default_rng(42)
            sampledIdx = sampleRNG.choice(len(allSmplCombined), size=perfModeN, replace=False, axis=0, shuffle=False)
            sampledSmpl = allSmplCombined[sampledIdx, :]
        else: 
            sampledSmpl = allSmplCombined

        # Further downsample for KDE 
        if len(sampledSmpl) < kde_size:
            kdeSmpl = sampledSmpl[:, [xChnl, yChnl]]
        else:
            sampleRNG2 = np.random.default_rng(43)
            kdeSmplIdx = sampleRNG2.choice(len(sampledSmpl), size=min(kde_size, perfModeN), replace=False, axis=0, shuffle=False)
            kdeSmpl = sampledSmpl[kdeSmplIdx, :]

        # Transform the data if needed
        transformed_kdeSmpl = []
        transformed_sampledSmpl = []

        for chnl, scale in zip([xChnl, yChnl], axScales):
            if scale == 'logicle':
                logicleT = _LogicleTransform(data=kdeSmpl[:, chnl], channel=chnl).inverted()
                transformed_kdeSmpl.append(logicleT.transform_non_affine(kdeSmpl[:, chnl]))
                transformed_sampledSmpl.append(logicleT.transform_non_affine(sampledSmpl[:, chnl]))
            elif scale == 'log':
                transformed_kdeSmpl.append(np.log10(kdeSmpl[:, chnl]))
                transformed_sampledSmpl.append(np.log10(sampledSmpl[:, chnl]))
            elif scale == 'linear':
                transformed_kdeSmpl.append(kdeSmpl[:, chnl])
                transformed_sampledSmpl.append(sampledSmpl[:, chnl])

        transformed_kdeSmpl = np.vstack(transformed_kdeSmpl).T
        transformed_sampledSmpl = np.vstack(transformed_sampledSmpl).T

        # Remove NaN and INFs in rows
        transformed_kdeSmpl = transformed_kdeSmpl[np.all(np.isfinite(transformed_kdeSmpl), axis=1), :]
        smplMask = np.all(np.isfinite(transformed_sampledSmpl), axis=1)

        # Normalize between dimentions for kde
        minMax = np.array([np.min(transformed_kdeSmpl, axis=0), np.max(transformed_kdeSmpl, axis=0)])
        transformed_kdeSmpl = (transformed_kdeSmpl - minMax[0]) / (minMax[1] - minMax[0])
        transformed_sampledSmpl = (transformed_sampledSmpl - minMax[0]) / (minMax[1] - minMax[0])

        # Construct the kdea
        G_kde = gaussian_kde(transformed_kdeSmpl.T)
        G_kde.set_bandwidth(G_kde.factor / (kde_size**(-1./6)) * (len(transformed_sampledSmpl)**(-1./6)))
        cmap = G_kde(transformed_sampledSmpl[smplMask, :].T)

        return sampledSmpl, smplMask, cmap


    # Update axis limites with lims. If 'auto', set auto axis. If None, then do nothing for that axis
    def updateAxLims(self, xlims = 'auto', ylims = 'auto'):
        if xlims == 'auto':
            self.ax.autoscale(axis='x')
            self.signal_AxLimsUpdated.emit(self.ax.get_xlim(), self.ax.get_ylim())
        elif not (xlims is None):
            try: 
                self.ax.set_xlim(xlims)
            except ValueError:
                self.ax.autoscale(axis='x')
                self.signal_AxLimsUpdated.emit(self.ax.get_xlim(), self.ax.get_ylim())
        
        if ylims == 'auto':
            self.ax.autoscale(axis='y')
            self.signal_AxLimsUpdated.emit(self.ax.get_xlim(), self.ax.get_ylim())
        elif not (ylims is None):
            try:
                self.ax.set_ylim(ylims)
            except ValueError:
                self.ax.autoscale(axis='y')
                self.signal_AxLimsUpdated.emit(self.ax.get_xlim(), self.ax.get_ylim())

        self.draw_idle()

    # Adjust the axis to 1 and 99 percentile for dot and density plots, with some margins
    def adjustLim_noExtreme(self):
        if self.curPlotType in ('Dot plot', 'Density plot'):
            x_minmax = [np.inf, -np.inf]
            y_minmax = [np.inf, -np.inf]
            for smpl in self.cachedPlotStats.gatedSmpls:
                x_minmax_smpl = np.percentile(np.array(smpl[:, self.cachedPlotStats.chnls[0]]), [1, 99])
                y_minmax_smpl = np.percentile(np.array(smpl[:, self.cachedPlotStats.chnls[1]]), [1, 99])

                x_minmax[0] = min(x_minmax[0], x_minmax_smpl[0])
                x_minmax[1] = max(x_minmax[1], x_minmax_smpl[1])
                y_minmax[0] = min(y_minmax[0], y_minmax_smpl[0])
                y_minmax[1] = max(y_minmax[1], y_minmax_smpl[1])

            if np.all(np.isfinite(x_minmax)) and np.all(np.isfinite(y_minmax)):
                # Using axis transforms to handle behaviors in log/logical scales, for 10% margin
                data2axes = self.ax.transData + self.ax.transAxes.inverted()
                axes2data = data2axes.inverted()

                lowerLeft_ax = data2axes.transform([x_minmax[0], y_minmax[0]])
                upperRight_ax = data2axes.transform([x_minmax[1], y_minmax[1]])

                figSpan = np.array(upperRight_ax) - np.array(lowerLeft_ax)
                lowerLeft_ax = np.clip(np.array(lowerLeft_ax) - 0.1 * figSpan, a_min=0, a_max=None)
                upperRight_ax = np.clip(np.array(upperRight_ax) + 0.1 * figSpan, a_min=None, a_max=1)

                lowerLeft_data = axes2data.transform(lowerLeft_ax)
                upperRight_data = axes2data.transform(upperRight_ax)

                self.ax.set_xlim(lowerLeft_data[0], upperRight_data[0])
                self.ax.set_ylim(lowerLeft_data[1], upperRight_data[1])

                self.signal_AxLimsUpdated.emit([lowerLeft_data[0], upperRight_data[0]], [lowerLeft_data[1], upperRight_data[1]])

                self.draw_idle()
            else:
                return

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            dropUrls = event.mimeData().urls()
            if len(dropUrls) > 1:
                QtWidgets.QMessageBox.warning(self, 'Too many files', 
                                              'EasyFlowQ only support droping a single session file(.eqfl) for loading.')
                event.ignore()
            else:
                sessionDir = event.mimeData().urls()[0].toLocalFile()
                event.accept()
                self.to_load_session.emit(sessionDir)
        else:
            event.ignore()

class efNavigationToolbar(NavigationToolbar):
    # Customized NavigationToolbar2QT by removing the subplot and axis tool buttons
    toolitems = [t for t in NavigationToolbar.toolitems if t[0] in ('Home', 'Back', 'Forward', None, 'Pan', 'Zoom', 'Save')]

    def __init__(self, canvas, parent=None):
        super().__init__(canvas, parent)

        copyIcon = QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.EditCopy)
        self.copyAction = QtGui.QAction(copyIcon, 'Copy plot', self)
        self.copyAction.setShortcut('Ctrl+C')
        self.copyAction.setStatusTip('Copy the current plot to clipboard')

        self.copyAction.triggered.connect(self.handle_CopyPlot)
        
        # Insert the copy action
        self.addAction(self.copyAction)

    def handle_CopyPlot(self):
        buf = io.BytesIO()
        self.canvas.figure.savefig(buf, format='png', dpi=self.canvas.figure.dpi)
        copiedImage = QtGui.QImage.fromData(buf.getvalue())
        qClipBoard = QtWidgets.QApplication.clipboard()
        qClipBoard.setImage(copiedImage)

        self.locLabel.setText('Plot copied to clipboard \t')


def gateSmpls(smpls, gateList, lastGateStatOnly=False):
    #gate samples with a list of gate:
    gatedSmpls = []
    gateFracs = []
    inGateFlags = []
    for idx, fcsData in enumerate(smpls):
        
        inGateFlag = np.ones(fcsData.shape[0], dtype=bool)
        fracInEachGate = []
        for idx, gate in enumerate(gateList):
            # channels exist in the sample
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
                    inGateFlag = np.logical_and(newFlag, inGateFlag)

            else: 
                warnings.warn('Sample does not have channel(s) for this gate, skipping this gate', RuntimeWarning)
                fracInEachGate.append(1.0)
        
        gateFracs.append(fracInEachGate)

        gatedSmpl = fcsData[inGateFlag, :]
        gatedSmpls.append(gatedSmpl)
        inGateFlags.append(inGateFlag)
    
    return gatedSmpls, gateFracs, inGateFlags

# Coppied and modified from FlowCal.plot.hist1D
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
                ploting_bins = data.hist_bins(channels=channel, nbins=bins, scale=xscale, **xscale_kwargs)

                # If there is less then 16th of non-zero bins, use actual range
                minData = np.min(data[:, channel])
                maxData = np.max(data[:, channel])
                minBinIdx = np.searchsorted(ploting_bins, minData)
                maxBinIdx = np.searchsorted(ploting_bins, maxData)

                if (maxBinIdx - minBinIdx) / len(ploting_bins) < 1/16:
                    # print('there is less then 16th of non-zero bins')
                    ploting_bins = data.hist_bins(channels=channel, nbins=bins, scale=xscale, use_actual_range=True, **xscale_kwargs)

    # Calculate weights if normalizing bins by height
    if normed_height == 'Unit Area':
        weights = np.ones_like(data[:, channel]) / float(len(data[:, channel]))
    else:
        weights = None

    # Plot
    n, edges = np.histogram(data[:, channel], bins=ploting_bins, weights=weights)

    if smooth >= 8 and len(n) // 128 > 1:
        combine_folds = max(smooth // 8, 1) # combine every n bins, n is determined by the smooth parameter. Does not kick in till smooth = 8
        n = np.add.reduceat(n, np.arange(0, len(n), combine_folds))
        edges = edges[::combine_folds]
        edges = np.append(edges, ploting_bins[-1]) # make sure the last edge is the same as the last bin edge
        edges = edges[:len(n)+1] # make sure edges has one more element than n

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