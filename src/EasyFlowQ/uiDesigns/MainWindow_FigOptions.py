import sys
import math
from PySide6 import QtWidgets, QtCore, QtUiTools
from PySide6.QtGui import QDoubleValidator

from os import path, getcwd
from . import UiLoader

class mainUI_figOps(QtWidgets.QWidget):
    signal_AxLimsNeedUpdate = QtCore.Signal(object, object)
    signal_HistTypeSelected = QtCore.Signal(bool)
    signal_PlotRedraw = QtCore.Signal()

    def __init__(self, parent):

        super().__init__(parent)
        UiLoader().loadUi('MainWindow_FigOptions.ui', self)

        # Group the buttons
        buttonGroups = self._organizeButtonGroups()
        self.plotOptionBG, self.xAxisOptionBG, self.yAxisOptionBG, self.normOptionBG = buttonGroups
        self.rangeEdits = self._setupLineEdit()

        self.stackWidget.setCurrentWidget(self.pageDots)

        self.xlimAutoCheck.stateChanged.connect(self.handle_AxisAuto)
        self.ylimAutoCheck.stateChanged.connect(self.handle_AxisAuto)

        self.histRadio.toggled.connect(self.signal_HistTypeSelected)
        self.histRadio.toggled.connect(self.handle_histRadioToggled)

        self.dotSizeComboBox.setCurrentIndex(2)

        for bg in buttonGroups:
            for radio in bg.buttons():
                radio.clicked.connect(self.signal_PlotRedraw)

        self.smoothSlider.valueChanged.connect(self.signal_PlotRedraw)
        self.opacitySlider.valueChanged.connect(self.signal_PlotRedraw)
        self.dotSizeComboBox.currentIndexChanged.connect(self.signal_PlotRedraw)

    def handle_AxlimEdited(self):
        which = self.sender()
        if which is self.rangeEdits[0]:
            self.rangeEdits[1].setValidator(axlimValidator(float(which.text()), float('inf'), 5))
        elif which is self.rangeEdits[1]:
            self.rangeEdits[0].setValidator(axlimValidator(float('-inf'), float(which.text()), 5))
        elif which is self.rangeEdits[2]:
            self.rangeEdits[3].setValidator(axlimValidator(float(which.text()), float('inf'), 5))
        elif which is self.rangeEdits[3]:
            self.rangeEdits[2].setValidator(axlimValidator(float('-inf'), float(which.text()), 5))

        if which in self.rangeEdits[0:2]:
            self.signal_AxLimsNeedUpdate.emit((float(self.xlimMinEdit.text()), float(self.xlimMaxEdit.text())), None)
        elif which in self.rangeEdits[2:4]:
            self.signal_AxLimsNeedUpdate.emit(None, (float(self.ylimMinEdit.text()), float(self.ylimMaxEdit.text())))
        
        
    def handle_AxisAuto(self, checkState):
        which = self.sender()

        if which.checkState() is QtCore.Qt.Checked:
            if which is self.xlimAutoCheck:
                self.signal_AxLimsNeedUpdate.emit('auto', None)
                pass
            elif which is self.ylimAutoCheck:
                self.signal_AxLimsNeedUpdate.emit(None, 'Auto')
                pass

    def handle_histRadioToggled(self, toggleState):
        if toggleState:
            self.stackWidget.setCurrentWidget(self.pageHist)
        else:
            self.stackWidget.setCurrentWidget(self.pageDots)

    
    def _organizeButtonGroups(self):
        # Create button groups to manage the radio button for plot options

        plotOptionBG, xAxisOptionBG, yAxisOptionBG, normOptionBG = [QtWidgets.QButtonGroup(self) for i in range(4)]

        plotOptionBG.addButton(self.dotRadio, 0)
        plotOptionBG.addButton(self.histRadio, 1)
        plotOptionBG.addButton(self.densityRadio, 2)
        # Make sure y auto is always unchecked when switch figure type
        plotOptionBG.buttonToggled.connect(lambda: self.ylimAutoCheck.setChecked(2))

        xAxisOptionBG.addButton(self.xLinRadio, 0)
        xAxisOptionBG.addButton(self.xLogRadio, 1)
        xAxisOptionBG.addButton(self.xLogicleRadio, 2)

        yAxisOptionBG.addButton(self.yLinRadio, 0)
        yAxisOptionBG.addButton(self.yLogRadio, 1)
        yAxisOptionBG.addButton(self.yLogicleRadio, 2)

        normOptionBG.addButton(self.norm2PercRadio, 0)
        normOptionBG.addButton(self.norm2CountRadio, 2)

        return plotOptionBG, xAxisOptionBG, yAxisOptionBG, normOptionBG

    def _setupLineEdit(self):
        rangeEdits = [self.xlimMinEdit, self.xlimMaxEdit, self.ylimMinEdit, self.ylimMaxEdit]
        for edit in rangeEdits:
            edit.setValidator(QDoubleValidator())
            edit.editingFinished.connect(self.handle_AxlimEdited)

        return rangeEdits

    # This returns a package of relevant fig options
    @property
    def curFigOptions(self):
        return self.curPlotType, self.curAxScales, self.curAxLims, self.curNormOption, self.smoothSlider.value(), self.curDotSize, self.curOpacity
    
    @property
    def curAxScales(self):
        return (self.xAxisOptionBG.checkedButton().text(), self.yAxisOptionBG.checkedButton().text())

    def set_curAxScales(self, AxScales):
        for xRadio in self.xAxisOptionBG.buttons():
            if xRadio.text() == AxScales[0]:
                xRadio.setChecked(True)
                continue
        for yRadio in self.yAxisOptionBG.buttons():
            if yRadio.text() == AxScales[1]:
                yRadio.setChecked(True)
                continue

    @property
    def curNormOption(self):
        return self.normOptionBG.checkedButton().text()

    def set_curNormOption(self, normOption):
        for normRadio in self.normOptionBG.buttons():
            if normRadio.text() == normOption:
                normRadio.setChecked(True)
                continue

    @property
    def curPlotType(self):
        return self.plotOptionBG.checkedButton().text()

    def set_curPlotType(self, plotType):
        for plotRadio in self.plotOptionBG.buttons():
            if plotRadio.text() == plotType:
                plotRadio.setChecked(True)
                continue

    @property
    def curAxLims(self):
    # Returns [xmin, xmax, ymin, ymax] in float
        xAuto = (self.xlimAutoCheck.isChecked())
        yAuto = (self.ylimAutoCheck.isChecked())

        xlim = ['auto'] if xAuto else [[float(self.xlimMinEdit.text()), float(self.xlimMaxEdit.text())]]
        ylim = ['auto'] if yAuto else [[float(self.ylimMinEdit.text()), float(self.ylimMaxEdit.text())]]

        return xlim + ylim

    # Set the current axis limits, if the input is nan, set lim to auto
    def set_curAxLims(self, xlim, ylim):
        if not (xlim == 'auto' or xlim is None):
            xmin, xmax = xlim
            if not (math.isnan(xmin) or math.isnan(xmax)):
                self.xlimMinEdit.setText('{0:.2e}'.format(xmin))
                self.xlimMaxEdit.setText('{0:.2e}'.format(xmax))
        
        if not (ylim == 'auto' or ylim is None):
            ymin, ymax = ylim
            if not (math.isnan(ymin) or math.isnan(ymax)):
                self.ylimMinEdit.setText('{0:.2e}'.format(ymin))
                self.ylimMaxEdit.setText('{0:.2e}'.format(ymax))
            
            
    def set_axAuto(self, xAxis=None, yAxis=None):
        if not xAxis is None:
            self.xlimAutoCheck.setChecked(True if xAxis else False)
        if not yAxis is None:
            self.ylimAutoCheck.setChecked(True if yAxis else False)

    @property
    def curSmooth(self):
        return self.smoothSlider.value()

    def set_curSmooth(self, smooth):
        self.smoothSlider.setValue(smooth)

    @property
    def curDotSize(self):
        return self.dotSizeComboBox.currentText()
    
    @property
    def curOpacity(self):
        return self.opacitySlider.value()

class axlimValidator(QDoubleValidator):
    def fixup(self, a0: str) -> str:
        if float(a0) > self.top():
            return str(self.top())
        elif float(a0) < self.bottom():
            return str(self.bottom())
        
        return super().fixup(a0)

if __name__ == '__main__':

    app = QtWidgets.QApplication(sys.argv)

    window = mainUI_figOps(None)
    window.show()
    sys.exit(app.exec_())