import sys
import matplotlib
import math

from PyQt5 import QtWidgets, QtCore, QtGui, uic
from os import path

from src.qtModels import smplPlotItem, chnlModel, gateWidgetItem, quadWidgetItem
from src.gates import polygonGateEditor, lineGateEditor, quadrantEditor
from src.plotWidgets import plotCanvas
from src.efio import sessionSave, writeRawFcs, getSysDefaultDir
from src.utils import colorGenerator, axlimValidator

from window_RenameCF import renameWindow_CF
from window_Stats import statWindow
from window_Settings import settingsWindow, localSettings

matplotlib.use('QT5Agg')

mainWindowUi, mainWindowBase = uic.loadUiType('./uiDesigns/MainWindow.ui') # Load the .ui file

class mainUi(mainWindowBase, mainWindowUi):
    requestNewWindow = QtCore.pyqtSignal(str, QtCore.QPoint)

    def __init__(self, setting: localSettings, sessionSaveFile=None, pos=None):

        # init and setup UI
        mainWindowBase.__init__(self)
        self.setupUi(self)

        # show manubar on macos
        self.menubar.setNativeMenuBar(False)

        # Group the buttons
        buttonGroups = self._organizeButtonGroups()
        self.plotOptionBG, self.xAxisOptionBG, self.yAxisOptionBG, self.normOptionBG = buttonGroups

        # load the seetings:
        self.settingDict = setting.settingDict
        
        # other init
        self.version = 0.1
        
        self._saveFlag = False
        self.rangeEdits = self._setupLineEdit()

        self.set_sessionSaveDir(sessionSaveFile)

        self.chnlDict = dict()
        self.colorGen = colorGenerator()
        self.sessionSaveDir = None
        self.holdFigureUpdate = True
        self.gateEditor = None

        # initiate other windows
        self.renameWindow = None
        self.settingsWindow = None
        self.statWindow = statWindow(self.sessionSaveDir if self.sessionSaveDir else self.baseDir)

        # add the matplotlib ui
        matplotlib.rcParams['savefig.directory'] = self.baseDir

        self.mpl_canvas = plotCanvas(dpiScale=self.settingDict['plot dpi scale'])

        self.plotLayout = QtWidgets.QVBoxLayout(self.plotBox)
        self.plotLayout.addWidget(self.mpl_canvas.navigationBar)
        self.plotLayout.addWidget(self.mpl_canvas)

        self.smplsOnPlot = []

        # init ui models
        self.smplListWidgetModel = self.smplListWidget.model()
        self.gateListWidgetModel = self.gateListWidget.model()


        self.chnlListModel = chnlModel()
        self.xComboBox.setModel(self.chnlListModel)
        self.yComboBox.setModel(self.chnlListModel)

        # add actions to context memu
        self.gateListWidget.addActions([self.actionDelete_Gate, self.actionEdit_Gate])

        # add the secret testing shortcut
        secretShortcut = QtWidgets.QShortcut(QtGui.QKeySequence('Alt+C'), self, self.secretCrash)

        # link triggers:
        # menu
        self.actionNew_Session.triggered.connect(self.handle_NewSession)
        self.actionSave.triggered.connect(self.handle_Save)
        self.actionOpen_Session.triggered.connect(self.handle_OpenSession)
        self.actionSave_as.triggered.connect(self.handle_SaveAs)

        self.actionLoad_Data_Files.triggered.connect(self.handle_LoadData)
        self.actionFor_Cytoflex.triggered.connect(self.handle_RenameForCF)
        self.actionExport_data_in_current_gates.triggered.connect(self.handle_ExportDataInGates)

        self.actionStats_window.triggered.connect(self.handle_StatWindow)

        self.actionSettings.triggered.connect(self.handle_Settings)

        # context menu
        self.actionDelete_Gate.triggered.connect(self.handle_DeleteGate)
        self.actionEdit_Gate.triggered.connect(self.handle_EditGate)

        # everything update figure
        self.smplListWidget.itemChanged.connect(self.handle_One)
        self.smplListWidget.itemSelectionChanged.connect(self.handle_One)
        self.smplListWidgetModel.rowsMoved.connect(self.handle_One)

        self.gateListWidget.itemChanged.connect(self.handle_One)
        self.gateListWidgetModel.rowsMoved.connect(self.handle_One)

        self.xComboBox.currentIndexChanged.connect(self.handle_One)
        self.yComboBox.currentIndexChanged.connect(self.handle_One)

        for bg in buttonGroups:
            for radio in bg.buttons():
                radio.clicked.connect(self.handle_One)
        self.perfCheck.stateChanged.connect(self.handle_One)

        self.smoothSlider.valueChanged.connect(self.handle_One)

        # gates
        self.addGateButton.clicked.connect(self.handle_AddGate)
        self.addQuadButton.clicked.connect(self.handle_AddQuad)

        # axes lims
        self.mpl_canvas.axLimUpdated.connect(self.handle_UpdateAxLim)
        self.xlimAutoCheck.stateChanged.connect(self.handle_AxisAuto)
        self.ylimAutoCheck.stateChanged.connect(self.handle_AxisAuto)

        # others
        self.colorPB.clicked.connect(self.handle_ChangeSmplColor)

        # axis ranges
        # self.xlimAutoCheck.stateChanged.connect(lambda checkState: self.handle_axisAuto('x', checkState))
        # self.ylimAutoCheck.stateChanged.connect(lambda checkState: self.handle_axisAuto('y', checkState))

        # load the session if there is a session save file:
        if sessionSaveFile:
            sessionSave.loadSessionSave(self, sessionSaveFile)
            self.holdFigureUpdate = False
            self.handle_One()

        if pos:
            self.move(pos)

        self.holdFigureUpdate = False

    # the centre handler for updating the figure.
    def handle_One(self):
        # this function is used to process info for the canvas to redraw

        if self.holdFigureUpdate:
            return

        self.set_saveFlag(True)
        selectedSmpls = self.smplListWidget.selectedItems()

        if self.perfCheck.isChecked():
            try:
                perfModeN = self.settingDict['dot N in perf mode']
            except:
                perfModeN = 20000
        else:
            perfModeN = None

        smplsOnPlot = self.mpl_canvas.redraw(selectedSmpls, 
                                             chnlNames=self.curChnls, 
                                             axisNames=(self.xComboBox.currentText(), self.yComboBox.currentText()),
                                             axScales=self.curAxScales,
                                             axRanges=self.curLimSettings,
                                             gateList=[gateItem.gate for gateItem in self.curGateItems],
                                             quadrant = self.curQuadrantItem.quad if self.curQuadrantItem else None,
                                             plotType = self.curPlotType,
                                             normOption = self.curNormOption,
                                             perfModeN = perfModeN,
                                             smooth = self.smoothSlider.value()
        )

        self.smplsOnPlot = smplsOnPlot

        if self.statWindow.isVisible() and len(self.smplsOnPlot):
            self.statWindow.updateStat(self.smplsOnPlot, self.curChnls, self.curGateItems)

    def handle_LoadData(self):
        fileNames, _ = QtWidgets.QFileDialog.getOpenFileNames(self, 'Open data files', self.baseDir, filter='*.fcs')
        newColorList = self.colorGen.giveColors(len(fileNames))

        for fileName, newColor in zip(fileNames, newColorList):
            self.loadFcsFile(fileName, newColor)
    
    def handle_AddGate(self):
        self._disableInputForGate(True)
        self.mpl_canvas.setCursor(QtCore.Qt.CrossCursor)

        if self.curPlotType == 'Dot plot':
            self.statusbar.showMessage('Left click to draw, Right click to close the gate and confirm', 0)
            self.gateEditor = polygonGateEditor(self.mpl_canvas.ax, canvasParam=(self.curChnls, self.curAxScales))
        
        elif self.curPlotType == 'Histogram':
            self.statusbar.showMessage('Left click to draw a line gate, Right click to cancel', 0)
            self.gateEditor = lineGateEditor(self.mpl_canvas.ax, self.curChnls[0])

        self.gateEditor.gateConfirmed.connect(self.loadGate)
        self.gateEditor.addGate_connnect()

    def handle_GateSelectionChanged(self, item):
        if item.checkState() == 2:
            pass
        elif item.checkState() == 1:
            pass
        else:
            pass
        # print(item.checkState())            
        pass

    def handle_AddQuad(self):
        self._disableInputForGate(True)
        self.mpl_canvas.setCursor(QtCore.Qt.CrossCursor)

        if self.curPlotType == 'Dot plot':
            self.statusbar.showMessage('Left click to confirm, Right click to close the gate and confirm', 0)
            self.quadEditor = quadrantEditor(self.mpl_canvas.ax, canvasParam=(self.curChnls, self.curAxScales))
        
        else:
            pass

        self.quadEditor.quadrantConfirmed.connect(self.loadQuadrant)
        self.quadEditor.addQuad_connnect()

                
    def handle_NewSession(self):
        self.requestNewWindow.emit('', self.pos() + QtCore.QPoint(60, 60))

    def handle_OpenSession(self):
        openFileDir, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Save session', self.baseDir, filter='*.eflq')
        if not openFileDir:
            return
        # print(openFileDir)

        if self.isWindowAlmostNew():
        #If there is nothing in this current window, update the current window
            self.holdFigureUpdate = True
            sessionSave.loadSessionSave(self, openFileDir)
            self.set_sessionSaveDir(openFileDir)
            self.holdFigureUpdate = False
            self.handle_One()

            self.set_saveFlag(False)
        else:
            self.requestNewWindow.emit(openFileDir, self.pos() + QtCore.QPoint(60, 60))

    def handle_Save(self):
        if self.sessionSaveDir:
            # if save exist, replace it at the same dir
            sessionSaveFile = sessionSave(self, self.sessionSaveDir)
            sessionSaveFile.saveJson()

            self.set_saveFlag(False)
        else: 
            self.handle_SaveAs()

    def handle_SaveAs(self):
        saveFileDir, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save session', self.baseDir, filter='*.eflq')
        if not saveFileDir:
            return

        self.set_sessionSaveDir(saveFileDir)
        sessionSaveFile = sessionSave(self, saveFileDir)
        sessionSaveFile.saveJson()

        self.set_saveFlag(False)
        pass

    def handle_RenameForCF(self):
        if  not self.smplListWidget.count():
            msgBox = QtWidgets.QMessageBox.warning(self, 'Error', 'No samples to rename')
            return

        openFileDir, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Load xlsx file for renaming', self.baseDir, filter='*.xlsx')
        if not openFileDir:
            return

        smplNameList = [self.smplListWidget.item(idx).fcsFileName for idx in range(self.smplListWidget.count())]
        self.renameWindow = renameWindow_CF(openFileDir, smplNameList)
        self.renameWindow.setWindowModality(QtCore.Qt.ApplicationModal)
        self.renameWindow.renameConfirmed.connect(self.handle_RenameForCF_return)
        self.renameWindow.show()

    def handle_RenameForCF_return(self, renameDict):
        self.holdFigureUpdate = True
        for idx in range(self.smplListWidget.count()):
            smplItem = self.smplListWidget.item(idx)
            if smplItem.fcsFileName in renameDict:
                smplItem.displayName = renameDict[smplItem.fcsFileName]
        
        self.holdFigureUpdate = False

        self.handle_One()

    def handle_ExportDataInGates(self):

        self.statWindow.updateStat(self.smplsOnPlot, self.curChnls, self.curGateItems)

        if len(self.statWindow.cur_Name_RawData_Pairs):
            saveFileDir = QtWidgets.QFileDialog.getExistingDirectory(self, caption='Export raw data', directory=self.sessionSaveDir)
            if not saveFileDir:
                return

            self.progBar = QtWidgets.QProgressBar(self)
            self.statusbar.addPermanentWidget(self.progBar)
            self.statusbar.showMessage('Exporting starting...')

            names = [a[0] for a in self.statWindow.cur_Name_RawData_Pairs]
            fcsDatas = [a[1] for a in self.statWindow.cur_Name_RawData_Pairs]

            writterThread = writeRawFcs(self, names, fcsDatas, saveFileDir)
            writterThread.prograssChanged.connect(lambda a, b: self.handle_UpdateProgBar(a, b, 'Exporting: '))
            writterThread.finished.connect(self.handle_ExportDataFinished)

            writterThread.start()

        else:
            QtWidgets.QMessageBox.warning(self, 'Error', 'No sample selected to export')

    def handle_StatWindow(self):
        if not self.statWindow.isVisible():
            self.statWindow.updateStat(self.smplsOnPlot, self.curChnls, self.curGateItems)
            self.statWindow.show()
        self.statWindow.raise_()
        self.statWindow.move(self.pos() + QtCore.QPoint(100, 60))
        pass


    def handle_ChangeSmplColor(self):
        color = QtWidgets.QColorDialog.getColor()

        if color.isValid():
            for item in self.smplListWidget.selectedItems():
                item.plotColor = color

    def handle_Settings(self, firstTime=False):
        self.settingsWindow = settingsWindow(firstTime=firstTime)
        self.settingsWindow.setWindowModality(QtCore.Qt.ApplicationModal)

        self.settingsWindow.newLocalSettingConfimed.connect(self.handle_NewSetting)

        self.settingsWindow.show()

    def handle_NewSetting(self, newNetting):
        self.settingDict = newNetting.settingDict

    def handle_UpdateProgBar(self, curName, progFrac, prefixText=''):
        self.statusbar.showMessage(prefixText + curName)
        self.progBar.setValue(int(progFrac*100))

    def handle_ExportDataFinished(self):
        self.statusbar.removeWidget(self.progBar)
        self.statusbar.showMessage('Exporting Finished')

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
            self.mpl_canvas.updateLims(float(self.xlimMinEdit.text()), float(self.xlimMaxEdit.text()), None, None)
        elif which in self.rangeEdits[2:4]:
            self.mpl_canvas.updateLims(None, None, float(self.ylimMinEdit.text()), float(self.ylimMaxEdit.text()))
        
        print('range edited')

    def handle_UpdateAxLim(self, xmin, xmax, ymin, ymax):
        if not (math.isnan(xmin) or math.isnan(xmax)):
            self.xlimMinEdit.setText('{0:.2e}'.format(xmin))
            self.xlimMaxEdit.setText('{0:.2e}'.format(xmax))

        if not (math.isnan(ymin) or math.isnan(ymax)):
            self.ylimMinEdit.setText('{0:.2e}'.format(ymin))
            self.ylimMaxEdit.setText('{0:.2e}'.format(ymax))

    def handle_AxisAuto(self, checkState):
        which = self.sender()

        if checkState == 2:
            if which is self.xlimAutoCheck:
                self.mpl_canvas.updateLims(xmin='auto', xmax='auto')
                pass
            elif which is self.ylimAutoCheck:
                self.mpl_canvas.updateLims(ymin='auto', ymax='auto')
                pass
        pass

    def handle_DeleteGate(self):
        curSelected = self.gateListWidget.selectedItems()
        if len(curSelected) == 0:
            QtWidgets.QMessageBox.warning(self, 'No gate selected', 'Please select a gate to delete')
            return
        input = QtWidgets.QMessageBox.question(self, 'Delete gate?', 'Are you sure to delete gate \"{0}\"'.format(curSelected[0].text()))

        if input == QtWidgets.QMessageBox.Yes:
            self.gateListWidget.takeItem(self.gateListWidget.row(curSelected[0]))
            self.handle_One()
        pass

    def handle_EditGate(self):
        pass

    def closeEvent(self, event: QtGui.QCloseEvent):
        if self.statWindow.isVisible():
            self.statWindow.close()

        if self.saveFlag:
            input = QtWidgets.QMessageBox.question(self, 'Close session', 'Save changes to the file?', buttons=
                                                   QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel)

            if input == QtWidgets.QMessageBox.Cancel:
                event.ignore()
            elif input == QtWidgets.QMessageBox.Discard:
                event.accept()
            elif input == QtWidgets.QMessageBox.Save:
                self.handle_Save()
                event.accept()

        else:
            event.accept()


    def _organizeButtonGroups(self):
        # Create button groups to manage the radio button for plot options

        plotOptionBG, xAxisOptionBG, yAxisOptionBG, normOptionBG = [QtWidgets.QButtonGroup(self) for i in range(4)]

        plotOptionBG.addButton(self.dotRadio, 0)
        plotOptionBG.addButton(self.histRadio, 1)
        # Make sure y auto is always unchecked when switch figure type
        plotOptionBG.buttonToggled.connect(lambda: self.ylimAutoCheck.setChecked(2))

        xAxisOptionBG.addButton(self.xLinRadio, 0)
        xAxisOptionBG.addButton(self.xLogRadio, 1)
        xAxisOptionBG.addButton(self.xLogicleRadio, 2)

        yAxisOptionBG.addButton(self.yLinRadio, 0)
        yAxisOptionBG.addButton(self.yLogRadio, 1)
        yAxisOptionBG.addButton(self.yLogicleRadio, 2)

        normOptionBG.addButton(self.norm2PercRadio, 0)
        normOptionBG.addButton(self.norm2TotalRadio, 1)
        normOptionBG.addButton(self.norm2CountRadio, 2)

        return plotOptionBG, xAxisOptionBG, yAxisOptionBG, normOptionBG
    
    def _setupLineEdit(self):
        rangeEdits = [self.xlimMinEdit, self.xlimMaxEdit, self.ylimMinEdit, self.ylimMaxEdit]
        for edit in rangeEdits:
            edit.setValidator(QtGui.QDoubleValidator())
            edit.editingFinished.connect(self.handle_AxlimEdited)

        return rangeEdits


    def _disableInputForGate(self, disable=True):
        self.toolBox.setEnabled(not disable)
        for idx in range(self.leftLayout.count()):
            self.leftLayout.itemAt(idx).widget().setEnabled(not disable)
        for idx in range(self.rightLayout.count()):
            self.rightLayout.itemAt(idx).widget().setEnabled(not disable)

    def loadFcsFile(self, fileDir, color, displayName=None, selected=False):
        self.set_saveFlag(True)
        newSmplItem = smplPlotItem(fileDir, plotColor=QtGui.QColor.fromRgbF(*color))
        self.smplListWidget.addItem(newSmplItem)
        if displayName:
            newSmplItem.displayName = displayName

        if selected:
            newSmplItem.setSelected(True)

        # merging the channel dictionary. 
        # If two channel with same channel name (key), but different flurophore (value), the former one will be kept
        for key in newSmplItem.chnlNameDict:
            self.chnlListModel.addChnl(key, newSmplItem.chnlNameDict[key])

    def loadGate(self, gate, replace=None, gateName=None, checkState=0):
        self.set_saveFlag(True)
        self._disableInputForGate(False)
        self.mpl_canvas.unsetCursor()
        self.statusbar.clearMessage()

        if replace:
            pass
        else:
            if gate is None:
                QtWidgets.QMessageBox.warning(self, 'Error', 'Not a valid gate')
                self.handle_One()
            else:
                if not gateName:
                    gateName, flag = QtWidgets.QInputDialog.getText(self, 'New gate', 'Name for the new gate')
                    if not flag:
                        self.handle_One()
                        return
                    
                newQItem = gateWidgetItem(gateName, gate)
                if checkState: 
                    newQItem.setCheckState(checkState)
                # newQItem.setData(0x100, gate)
                # newQItem.setCheckable(True)
                self.gateListWidget.addItem(newQItem)

    def loadQuadrant(self, quadrant, replace=None, quadName=None, checkState=0):
        self.set_saveFlag(True)
        self._disableInputForGate(False)
        self.mpl_canvas.unsetCursor()
        self.statusbar.clearMessage()

        if replace:
            pass
        else:
            if quadrant is None:
                QtWidgets.QMessageBox.warning(self, 'Error', 'Not a valid quadrant')
                self.handle_One()
            else:
                if not quadName:
                    quadName, flag = QtWidgets.QInputDialog.getText(self, 'New quadrant', 'Name for the new quadrant')
                    if not flag:
                        self.handle_One()
                        return
                    
                newQItem = quadWidgetItem(quadName, quadrant)

                # newQItem.setData(0x100, gate)
                # newQItem.setCheckable(True)
                self.quadListWidget.addItem(newQItem)

        pass

    def secretCrash(self):
        input = QtWidgets.QMessageBox.critical(self, 'Warning! (or congrat?)', 
                                               'You have reached the secret place for crashing the app, proceed?',
                                               buttons=QtWidgets.QMessageBox.StandardButton.Ok | QtWidgets.QMessageBox.StandardButton.Cancel)
        if input == QtWidgets.QMessageBox.StandardButton.Ok:
            null_val2 = dict()
            null_val1 = null_val2['Key_Not_Exsit']

    @property
    def curChnls(self):
        if self.xComboBox.currentIndex() == -1 and self.yComboBox.currentIndex() == -1:
            return [None, None]
        else:
            xChnl = self.chnlListModel.keyList[self.xComboBox.currentIndex()]
            yChnl = self.chnlListModel.keyList[self.yComboBox.currentIndex()]
            return [xChnl, yChnl]

    def set_curChnls(self, chnls):
        self.xComboBox.setCurrentIndex(self.chnlListModel.keyList.index(chnls[0]))
        self.yComboBox.setCurrentIndex(self.chnlListModel.keyList.index(chnls[1]))

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
    def curGateItems(self):
        allGateItems = [self.gateListWidget.item(idx) for idx in range(self.gateListWidget.count())]

        return [gateItem for gateItem in allGateItems if (gateItem.checkState() == 2)]

    @property
    def curQuadrantItem(self):
        quadList = self.quadListWidget.selectedItems()
        if quadList:
            return quadList[0]
        else:
            return None

    @property
    def curLimSettings(self):
        xAuto = (self.xlimAutoCheck.checkState() == 2)
        yAuto = (self.ylimAutoCheck.checkState() == 2)

        xlim = ['auto', 'auto'] if xAuto else [float(self.xlimMinEdit.text()), float(self.xlimMaxEdit.text())]
        ylim = ['auto', 'auto'] if yAuto else [float(self.ylimMinEdit.text()), float(self.ylimMaxEdit.text())]

        return xlim + ylim

    @property
    def saveFlag(self):
        return self._saveFlag

    def set_saveFlag(self, flag: bool):
        if not self._saveFlag == flag:
            self._saveFlag = flag

            self.set_sessionSaveDir(self.sessionSaveDir)    

    def set_sessionSaveDir(self, sessionSaveDir):
        # Set the sessionSaveDir, also update the window title
        self.sessionSaveDir = sessionSaveDir
        self.setWindowTitle('EasyFlowQ v{0:.1f}; ({1}{2})'.format(self.version, 
                                                                         ('*' if self.saveFlag else ''), 
                                                                         (self.sessionSaveDir if self.sessionSaveDir else 'Not saved')))

    def isWindowAlmostNew(self):
        return not (len(self.chnlListModel.keyList) and self.smplListWidget.count() and self.gateListWidget.count())

    @property
    def baseDir(self):
        if self.sessionSaveDir is not None:
            return path.dirname(self.sessionSaveDir)
        elif self.smplListWidget.count() > 0:
            return path.dirname(self.smplListWidget.item(0).fileDir)
        elif path.exists(self.settingDict['default dir']):
            return self.settingDict['default dir']
        else:
            return path.abspath(getSysDefaultDir())
        pass



if __name__ == '__main__':

    _excepthook = sys.excepthook
    def myexcepthook(type, value, traceback, oldhook=sys.excepthook):
        _excepthook(type, value, traceback)

    sys.excepthook = myexcepthook

    app = QtWidgets.QApplication(sys.argv)

    testSettings = localSettings('./localSettings.default.json')
    testSettings.settingDict["default dir"] = './demoSamples'

    window = mainUi(testSettings)
    window.show()
    sys.exit(app.exec_())

