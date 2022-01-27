import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import numpy as np

from PyQt5 import QtCore, QtGui
from gateClasses import polygonGate

class plotCanvas(FigureCanvasQTAgg):
    def __init__(self):
        self.fig, self.ax = plt.subplots()
        self.fig.set_tight_layout(True)
        super().__init__(self.fig)

        self.navigationBar = NavigationToolbar(self, self)
        self.setFocusPolicy(QtCore.Qt.ClickFocus)

    def redraw(self, smpls, chnlNames, axisNames, params=None):
        self.ax.clear()
        self.navigationBar.update()

        xChnl, yChnl = chnlNames

        for idx, smpl in enumerate(smpls):
            self.ax.scatter(smpl.data[xChnl], smpl.data[yChnl], color='C'+str(idx%10), s=1, label=smpl.smplName)

        self.ax.legend(markerscale=5)
        self.ax.set_xscale('log')
        self.ax.set_yscale('log')
        self.ax.set_xlabel(axisNames[0])
        self.ax.set_ylabel(axisNames[1])

        self.draw()

    def addGate(self, gateListModel):
        self._gateListModel = gateListModel
        self.setFocus()

        self.newGate = None
        self.pressCid = self.mpl_connect('button_press_event', self.on_press_addGate)
        self.moveCid = self.mpl_connect('motion_notify_event', self.on_motion_addGate)

        pass
    
    def on_press_addGate(self, event):
        if self.newGate == None:
            self.newGate = polygonGate(self.ax, [[event.xdata]*2, [event.ydata]*2])
        elif event.button == 3:
            self.newGate.closeGate()
            self.addGateFinished()
        else:
            self.newGate.addNewVert([[event.xdata, event.ydata]])
        self.draw()

    def on_motion_addGate(self, event):
        if self.newGate == None:
            return
        self.newGate.replaceLastVert([event.xdata, event.ydata])
        self.draw()
        pass

    def addGateFinished(self):
        self.mpl_disconnect(self.pressCid)
        self.mpl_disconnect(self.moveCid)

        newQItem = QtGui.QStandardItem('New Gate')
        newQItem.setData(self.newGate)
        newQItem.setCheckable(False)
        self._gateListModel.appendRow(newQItem)
        pass
