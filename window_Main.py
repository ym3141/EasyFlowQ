import sys
import matplotlib
import json

from PyQt5 import QtWidgets, QtCore, QtGui, uic
from os import path

from src.qtModels import smplPlotItem, smplItem, chnlModel, gateWidgetItem, quadWidgetItem, splitWidgetItem
from src.gates import polygonGateEditor, lineGateEditor, quadrantEditor, polygonGate, lineGate, quadrantGate, split, splitEditor
from src.plotWidgets import plotCanvas
from src.efio import sessionSave, writeRawFcs, getSysDefaultDir
from src.utils import colorGenerator

from window_RenameCF import renameWindow_CF
from window_RenameMap import renameWindow_Map
from window_Stats import statWindow
from window_Settings import settingsWindow, localSettings
from window_About import aboutWindow
from window_Comp import compWindow
from wizard_Comp import compWizard

from uiDesigns.MainWindow_FigOptions import mainUI_figOps

matplotlib.use('QT5Agg')

mainWindowUi, mainWindowBase = uic.loadUiType('./uiDesigns/MainWindow.ui') # Load the .ui file

class mainUi(mainWindowBase, mainWindowUi):
    requestNewWindow = QtCore.pyqtSignal(str, QtCore.QPoint)

    def __init__(self, setting: localSettings, sessionSaveFile=None, pos=None):

        # init and setup UI
        mainWindowBase.__init__(self)
        self.setupUi(self)

        # UI tweaks for macos
        self.menubar.setNativeMenuBar(False)
        self.tab_GateQuad.tabBar().setTabTextColor(0, QtGui.QColor('black'))
        self.tab_GateQuad.tabBar().setTabTextColor(1, QtGui.QColor('black'))

        # load the seetings:
        self.settingDict = setting.settingDict
        
        # other init
        self.version = self.settingDict['version']
        self._saveFlag = False

        self.chnlDict = dict()
        self.colorGen = colorGenerator()
        self.sessionSavePath = None
        self.holdFigureUpdate = True
        self.gateEditor = None

        self.showLegendCheck.setCheckState(1)

        # initiate other windows
        self.renameWindow = None
        self.settingsWindow = None
        self.compWindow = compWindow()
        self.statWindow = statWindow(self.sessionSavePath if self.sessionSavePath else self.dir4Save)
        self.aboutWindow = aboutWindow()

        # add the matplotlib ui
        matplotlib.rcParams['savefig.directory'] = self.dir4Save

        self.mpl_canvas = plotCanvas(dpiScale=self.settingDict['plot dpi scale'])

        self.plotLayout = QtWidgets.QVBoxLayout(self.plotBox)
        self.plotLayout.addWidget(self.mpl_canvas.navigationBar)
        self.plotLayout.addWidget(self.mpl_canvas)

        self.smplsOnPlot = []

        # add the figure property panel
        self.figOpsLayout = QtWidgets.QVBoxLayout(self.figOpsFrame)
        self.figOpsLayout.setContentsMargins(0, 0, 0, 0)
        self.figOpsPanel = mainUI_figOps(self.figOpsFrame)
        self.figOpsLayout.addWidget(self.figOpsPanel)


        # init ui models
        # self.smplListWidgetModel = self.smplListWidget.model()
        self.gateListWidgetModel = self.gateListWidget.model()

        self.chnlListModel = chnlModel()
        self.xComboBox.setModel(self.chnlListModel)
        self.yComboBox.setModel(self.chnlListModel)

        # add actions to context memu
        self.gateListWidget.addActions([self.actionDelete_Gate, self.actionEdit_Gate])
        self.qsListWidget.addActions([self.actionDelete_Quad, self.actionQuad2Gate])

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
        self.actionSimple_mapping.triggered.connect(self.handle_RenameMap)
        self.actionExport_data_in_current_gates.triggered.connect(self.handle_ExportDataInGates)

        self.actionStats_window.triggered.connect(self.handle_StatWindow)

        self.actionWizardComp.triggered.connect(self.handle_CompWizard)
        self.actionImportComp.triggered.connect(self.handle_ImportComp)
        self.actionExportComp.triggered.connect(self.handle_ExportComp)

        self.actionSettings.triggered.connect(self.handle_Settings)

        self.actionAbout.triggered.connect(lambda : self.aboutWindow.show())

        # context menu
        self.actionDelete_Gate.triggered.connect(self.handle_DeleteGate)
        self.actionEdit_Gate.triggered.connect(self.handle_EditGate)
        self.actionDelete_Quad.triggered.connect(self.handle_DeleteQuad)
        self.actionQuad2Gate.triggered.connect(self.handle_Quad2Gate)

        # everything update figure
        self.smplTreeWidget.itemChanged.connect(self.handle_One)
        self.smplTreeWidget.itemSelectionChanged.connect(self.handle_One)
        # self.smplListWidgetModel.rowsMoved.connect(self.handle_One)

        self.qsListWidget.itemSelectionChanged.connect(self.handle_One)

        self.gateListWidget.itemChanged.connect(self.handle_One)
        self.gateListWidgetModel.rowsMoved.connect(self.handle_One)

        self.xComboBox.currentIndexChanged.connect(self.handle_One)
        self.yComboBox.currentIndexChanged.connect(self.handle_One)

        self.perfCheck.stateChanged.connect(self.handle_One)
        self.showLegendCheck.stateChanged.connect(self.handle_One)

        self.figOpsPanel.signal_PlotRedraw.connect(self.handle_One)
        self.compWindow.compValueEdited.connect(self.handle_One)

        # gates
        self.addGateButton.clicked.connect(self.handle_AddGate)
        self.addQuadButton.clicked.connect(self.handle_AddQuad)

        # axes lims
        self.mpl_canvas.signal_AxLimsUpdated.connect(self.figOpsPanel.set_curAxLims)
        self.figOpsPanel.signal_AxLimsNeedUpdate.connect(self.mpl_canvas.updateAxLims)

        # compensation:
        self.compEditPB.clicked.connect(self.handle_EditComp)
        self.compApplyCheck.stateChanged.connect(self.handle_ApplyComp)
        self.compWindow.compValueEdited.connect(lambda : self.set_saveFlag(True))

        # others
        self.colorPB.clicked.connect(self.handle_ChangeSmplColor)
        self.clearQuadPB.clicked.connect(lambda : self.qsListWidget.clearSelection())
        # self.figOpsPanel.signal_HistTypeSelected.connect(self.handle_ChangedToHist)

        # load the session if there is a session save file:
        if sessionSaveFile:
            sessionSave.loadSessionSave(self, sessionSaveFile)
            self.saveFlag = False
            self.set_sessionSavePath(sessionSaveFile)
            self.holdFigureUpdate = False
            self.handle_One()

        self.updateWinTitle()

        if pos:
            self.move(pos)

        self.holdFigureUpdate = False

    # the centre handler for updating the figure.
    def handle_One(self):
        # this function is used to process info for the canvas to redraw

        if self.holdFigureUpdate:
            return

        self.set_saveFlag(True)
        selectedSmpls = self.smplTreeWidget.selectedItems()

        if self.perfCheck.isChecked():
            try:
                perfModeN = self.settingDict['dot N in perf mode']
            except:
                perfModeN = 20000
        else:
            perfModeN = None

        plotType, axScales, axRanges, normOption, smooth = self.figOpsPanel.curFigOptions

        if isinstance(self.curQuadrantItem, quadWidgetItem):
            quad_split = self.curQuadrantItem.quad
        elif isinstance(self.curQuadrantItem, splitWidgetItem):
            quad_split = self.curQuadrantItem.split
        else:
            quad_split = None

        compValues = self.compWindow.curComp if self.compApplyCheck.isChecked() else None

        smplsOnPlot = self.mpl_canvas.redraw(
            selectedSmpls, 
            chnlNames=self.curChnls, 
            axisNames=(self.xComboBox.currentText(), self.yComboBox.currentText()),
            compValues = compValues,
            gateList=[gateItem.gate for gateItem in self.curGateItems],
            quad_split = quad_split,
            plotType = plotType, axScales = axScales, axRanges = axRanges, normOption=normOption, smooth=smooth,
            perfModeN = perfModeN, legendOps = self.showLegendCheck.checkState()
        )

        self.smplsOnPlot = smplsOnPlot

        if self.statWindow.isVisible() and len(self.smplsOnPlot):
            self.statWindow.updateStat(self.smplsOnPlot, self.curChnls, self.curGateItems)

    def handle_LoadData(self):
        fileNames, _ = QtWidgets.QFileDialog.getOpenFileNames(self, 'Open data files', self.dir4Save, filter='*.fcs')
        newColorList = self.colorGen.giveColors(len(fileNames))

        for fileName, newColor in zip(fileNames, newColorList):
            self.loadFcsFile(fileName, newColor)
    
    def handle_AddGate(self):
        self._disableInputForGate(True)
        self.mpl_canvas.setCursor(QtCore.Qt.CrossCursor)
        plotType, axScales, axRanges, normOption, smooth = self.figOpsPanel.curFigOptions

        if plotType == 'Dot plot':
            self.statusbar.showMessage('Left click to draw, Right click to close the gate and confirm', 0)
            self.gateEditor = polygonGateEditor(self.mpl_canvas.ax, canvasParam=(self.curChnls, axScales))
        
        elif plotType == 'Histogram':
            self.statusbar.showMessage('Left click to draw a line gate, Right click to cancel', 0)
            self.gateEditor = lineGateEditor(self.mpl_canvas.ax, self.curChnls[0])

        self.gateEditor.gateConfirmed.connect(self.loadGate)
        self.gateEditor.addGate_connect()

    def handle_AddQuad(self):
        self._disableInputForGate(True)
        self.mpl_canvas.setCursor(QtCore.Qt.CrossCursor)
        plotType, axScales, axRanges, normOption, smooth = self.figOpsPanel.curFigOptions

        if plotType == 'Dot plot':
            self.statusbar.showMessage('Left click to confirm, Right click to cancel', 0)
            self.quadEditor = quadrantEditor(self.mpl_canvas.ax, canvasParam=(self.curChnls, axScales))
            self.quadEditor.quadrantConfirmed.connect(self.loadQuadrant)
            self.quadEditor.addQuad_connect()

        elif plotType == 'Histogram':
            self.statusbar.showMessage('Left click to draw a split, Right click to cancel', 0)
            self.splitEditor = splitEditor(self.mpl_canvas.ax, self.curChnls[0])
            self.splitEditor.splitConfirmed.connect(self.loadSplit)
            self.splitEditor.addSplit_connect()
        

    def handle_NewSession(self):
        self.requestNewWindow.emit('', self.pos() + QtCore.QPoint(60, 60))

    def handle_OpenSession(self):
        openFileDir, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Open session', self.dir4Save, filter='*.eflq')
        if not openFileDir:
            return
        # print(openFileDir)

        if self.isWindowAlmostNew():
        #If there is nothing in this current window, update the current window
            self.holdFigureUpdate = True
            sessionSave.loadSessionSave(self, openFileDir)
            self.set_sessionSavePath(openFileDir)
            self.holdFigureUpdate = False
            self.handle_One()

            self.set_saveFlag(False)
        else:
            self.requestNewWindow.emit(openFileDir, self.pos() + QtCore.QPoint(60, 60))

    def handle_Save(self):
        if self.sessionSavePath:
            # if save exist, replace it at the same dir
            sessionSaveFile = sessionSave(self, self.sessionSavePath)
            sessionSaveFile.saveJson()

            self.set_saveFlag(False)
        else: 
            self.handle_SaveAs()

    def handle_SaveAs(self):
        saveFileDir, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save session', self.dir4Save, filter='*.eflq')
        if not saveFileDir:
            return

        self.set_sessionSavePath(saveFileDir)
        sessionSaveFile = sessionSave(self, saveFileDir)
        sessionSaveFile.saveJson()

        self.set_saveFlag(False)
        pass

    def handle_RenameForCF(self):
        if not self.smplTreeWidget.topLevelItemCount():
            msgBox = QtWidgets.QMessageBox.warning(self, 'Error', 'No samples to rename')
            return

        smplNameList = [self.smplTreeWidget.topLevelItem(idx).fcsFileName for idx in range(self.smplTreeWidget.topLevelItemCount())]
        self.renameWindow = renameWindow_CF(self.dir4Save, smplNameList)
        self.renameWindow.setWindowModality(QtCore.Qt.ApplicationModal)
        self.renameWindow.renameConfirmed.connect(self.handle_RenameReturn)
        self.renameWindow.show()

    def handle_RenameMap(self):
        if not self.smplTreeWidget.topLevelItemCount():
            msgBox = QtWidgets.QMessageBox.warning(self, 'Error', 'No samples to rename')
            return

        smplNameList = [self.smplTreeWidget.topLevelItem(idx).fcsFileName for idx in range(self.smplTreeWidget.topLevelItemCount())]
        self.renameWindow = renameWindow_Map(self.dir4Save, smplNameList)
        self.renameWindow.setWindowModality(QtCore.Qt.ApplicationModal)
        self.renameWindow.renameConfirmed.connect(self.handle_RenameReturn)
        self.renameWindow.show()

    def handle_RenameReturn(self, renameDict):
        self.holdFigureUpdate = True
        for idx in range(self.smplTreeWidget.topLevelItemCount()):
            smplItem = self.smplTreeWidget.topLevelItem(idx)
            if smplItem.fcsFileName in renameDict:
                smplItem.displayName = renameDict[smplItem.fcsFileName]
        
        self.holdFigureUpdate = False
        self.handle_One()

    def handle_ExportDataInGates(self):

        self.statWindow.updateStat(self.smplsOnPlot, self.curChnls, self.curGateItems)

        if len(self.statWindow.cur_Name_RawData_Pairs):
            saveFileDir = QtWidgets.QFileDialog.getExistingDirectory(self, caption='Export raw data', directory=self.sessionSavePath)
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
        colorDiag = QtWidgets.QColorDialog()
        cstmColors = self.colorGen.giveColors_div(colorDiag.customCount())
        for idx, cstmColor in enumerate(cstmColors):
            colorDiag.setCustomColor(idx, QtGui.QColor.fromRgbF(*cstmColor))

        color = colorDiag.getColor(initial=QtGui.QColor('black'))

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
        curSelected = self.gateListWidget.selectedItems()
        if len(curSelected) == 0:
            QtWidgets.QMessageBox.warning(self, 'No gate selected', 'Please select a gate to edit')
            return
        else:
            curSelectedGate = curSelected[0].gate

        if isinstance(curSelectedGate, quadrantGate):
            QtWidgets.QMessageBox.warning(self, 'This is a quadrant gate', 'Sorry you cannot edit gate generated from quadrant')
            return

        plotType, axScales, axRanges, normOption, smooth = self.figOpsPanel.curFigOptions

        # Check if it's a polygone gate, and also change the current plot to the state that the gate was created on
        if isinstance(curSelectedGate, polygonGate):
            if not (plotType == 'Dot plot' and list(axScales) == curSelectedGate.axScales and self.curChnls == curSelectedGate.chnls):
                input = QtWidgets.QMessageBox.question(self, 'Change plot?', 'Current ploting parameters does not match those that the gate is created. \
                                                                              Switch to them (current plot will be lost)?')
                if input == QtWidgets.QMessageBox.Yes:
                    self.holdFigureUpdate = True
                    self.set_curChnls(curSelectedGate.chnls)
                    self.figOpsPanel.set_curPlotType('dot')
                    self.figOpsPanel.set_curAxScales(curSelectedGate.axScales)

                    self.holdFigureUpdate = False
                    self.handle_One()
                else:
                    return

            self.figOpsPanel.set_axAuto(True, True)

            self.statusbar.showMessage('Left click to drag gate/point; Right click to delete/add vertex; ENTER to confirm edit; ESC to exit', 0)
            self._disableInputForGate(True)
            self.mpl_canvas.setCursor(QtCore.Qt.OpenHandCursor)

            self.gateEditor = polygonGateEditor(self.mpl_canvas.ax, gate=curSelectedGate)
            self.gateEditor.gateConfirmed.connect(lambda gate : self.loadGate(gate, replace=curSelected[0]))
            self.gateEditor.editGate_connect()

        else:
            QtWidgets.QMessageBox.warning(self, 'Only polygon gate can be edited', 'Sorry you cannot edit gate types that are not polygon gate!')
            return

    def handle_DeleteQuad(self):
        curSelected = self.qsListWidget.selectedItems()
        if len(curSelected) == 0:
            QtWidgets.QMessageBox.warning(self, 'No quadrant selected', 'Please select a gate to delete')
            return
        input = QtWidgets.QMessageBox.question(self, 'Delete quadrant?', 'Are you sure to delete quadrant \"{0}\"'.format(curSelected[0].text()))

        if input == QtWidgets.QMessageBox.Yes:
            self.qsListWidget.takeItem(self.qsListWidget.row(curSelected[0]))
            self.handle_One()

    def handle_Quad2Gate(self):
        curSelected = self.qsListWidget.selectedItems()
        if not len(curSelected) == 0:
            newGates = curSelected[0].quad.generateGates()
            gateNameSuffixes = ['|\U0001F857|', '|\U0001F854|', '|\U0001F856|', '|\U0001F855|']
            for newGate, suffix in zip(newGates, gateNameSuffixes):
                self.loadGate(newGate, gateName='{0} {1}'.format(curSelected[0].text(), suffix))
        
        self.tab_GateQuad.setCurrentWidget(self.tabGate)
        
    def handle_EditComp(self):
        self.compWindow.show()
        self.compWindow.raise_()
        pass

    def handle_ApplyComp(self, state):
        if state == 2:
            if self.compWindow.curComp == (None, None, None):
                QtWidgets.QMessageBox.warning(self, 'No compensation', 'No compensation is set, please check the compensation window.')
            else:
                self.handle_One()
            
        elif state == 0:
            self.handle_One()
        pass

    def handle_CompWizard(self):
        compWizDialog = compWizard(self, self.chnlListModel, self.smplListWidget, self.gateListWidget, self.dir4Save,
                                   self.compWindow.autoFluoModel, self.compWindow.spillMatModel)
        compWizDialog.show()

    def handle_ExportComp(self):
        jDict = self.compWindow.to_json()
        saveFileDir, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Export compensation', self.dir4Save, filter='*.efComp')
        if not saveFileDir:
            return

        with open(saveFileDir, 'w+') as f:
            json.dump(jDict, f, sort_keys=True, indent=4)

    def handle_ImportComp(self):        
        openFileDir, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Import compensation', self.dir4Save, filter='*.efComp')
        if not openFileDir:
            return 
        
        self.statusbar.clearMessage()
        self.statusbar.showMessage('Loading compensation (may take some time)')

        with open(openFileDir, 'r') as f:
            jDict = json.load(f)
            self.compWindow.load_json(jDict)

        self.statusbar.removeWidget(self.progBar)

    def closeEvent(self, event: QtGui.QCloseEvent):
        if self.statWindow.isVisible():
            self.statWindow.close()

        if self.aboutWindow.isVisible():
            self.aboutWindow.close()

        if self.compWindow.isVisible():
            self.compWindow.close()

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


    def _disableInputForGate(self, disable=True):
        self.toolBox.setEnabled(not disable)
        self.smplBox.setEnabled(not disable)
        self.rightFrame.setEnabled(not disable)

    # load fcs file, as well as change check if the current channel is compatible and change accordingly
    def loadFcsFile(self, fileDir, color, displayName=None, selected=False):
        self.set_saveFlag(True)

        newSmplItem = smplPlotItem(fileDir, plotColor=QtGui.QColor.fromRgbF(*color))
        newRootSmplItem = smplItem(self.smplTreeWidget, fileDir, plotColor=QtGui.QColor.fromRgbF(*color))

        self.smplListWidget.addItem(newSmplItem)
        self.smplTreeWidget.addTopLevelItem(newRootSmplItem)
        if displayName:
            newSmplItem.displayName = displayName
            newRootSmplItem.displayName = displayName

        if selected:
            newSmplItem.setSelected(True)
            newRootSmplItem.setSelected(True)

        # merging the channel dictionary. 
        # If two channel with same channel name (key), but different flurophore (value), the former one will be kept
        newChnlFlag = False
        for key in newRootSmplItem.chnlNameDict:
            isNew = self.chnlListModel.addChnl(key, newRootSmplItem.chnlNameDict[key])
            newChnlFlag = newChnlFlag or isNew
            
        # update the compensation model if there are new channels added
        if newChnlFlag:    
            self.compWindow.updateChnls(self.chnlListModel)

    def loadGate(self, gate, replace=None, gateName=None, checkState=0):
        self.set_saveFlag(True)
        self._disableInputForGate(False)
        self.mpl_canvas.unsetCursor()
        self.statusbar.clearMessage()

        if not (replace is None):
            if gate is None:
                self.handle_One()
            else:
                qBox = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Question, 
                                             'Polygon gate edited', 'Do you want to save to overwrite, or to save as a new gate?', 
                                             buttons=QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard)
                newGateButton = qBox.addButton('As New Gate', QtWidgets.QMessageBox.ActionRole)
                
                input = qBox.exec()

                if qBox.clickedButton() == newGateButton:
                    gateName, flag = QtWidgets.QInputDialog.getText(self, 'New gate', 'Name for the new gate')
                    if not flag:
                        self.handle_One()
                        return
                    newQItem = gateWidgetItem(gateName, gate)
                    self.gateListWidget.addItem(newQItem)

                elif input == QtWidgets.QMessageBox.Save:
                    replace.gate = gate

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

                self.gateListWidget.addItem(newQItem)

    def loadQuadrant(self, quadrant, replace=None, quadName=None):
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
                self.qsListWidget.addItem(newQItem)
    
    def loadSplit(self, split, replace=None, splitName=None):
        self.set_saveFlag(True)
        self._disableInputForGate(False)
        self.mpl_canvas.unsetCursor()
        self.statusbar.clearMessage()

        if replace:
            pass
        else:
            if split is None:
                QtWidgets.QMessageBox.warning(self, 'Error', 'Not a valid split')
                self.handle_One()
            else:
                if not splitName:
                    splitName, flag = QtWidgets.QInputDialog.getText(self, 'New split', 'Name for the new split')
                    if not flag:
                        self.handle_One()
                        return
                    
                newSItem = splitWidgetItem(splitName, split)
                self.qsListWidget.addItem(newSItem)

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
    def curGateItems(self):
        allGateItems = [self.gateListWidget.item(idx) for idx in range(self.gateListWidget.count())]

        return [gateItem for gateItem in allGateItems if (gateItem.checkState() == 2)]

    @property
    def curQuadrantItem(self):
        quadList = self.qsListWidget.selectedItems()
        if quadList:
            return quadList[0]
        else:
            return None

    @property
    def saveFlag(self):
        return self._saveFlag

    def set_saveFlag(self, flag: bool):
        if not self._saveFlag == flag:
            self._saveFlag = flag
            self.updateWinTitle()

    def set_sessionSavePath(self, sessionSaveDir):
        # Set the sessionSaveDir, also update the window title
        self.sessionSavePath = sessionSaveDir
        self.statWindow.sessionDir = path.dirname(self.sessionSavePath)
        matplotlib.rcParams['savefig.directory'] = path.dirname(self.sessionSavePath)

        self.updateWinTitle()

    def updateWinTitle(self):
        pathStr = self.sessionSavePath if self.sessionSavePath else 'Not saved'
        self.setWindowTitle('EasyFlowQ v{0:.1f}; ({1}{2})'.format(self.version, ('*' if self.saveFlag else ''), pathStr)) 

    def isWindowAlmostNew(self):
        return not (len(self.chnlListModel.keyList) and self.smplListWidget.count() and self.gateListWidget.count())

    @property
    def dir4Save(self):
        if hasattr(self, 'sessionSavePath') and (not self.sessionSavePath is None):
            return path.dirname(self.sessionSavePath)
        elif self.smplListWidget.count() > 0:
            return path.dirname(self.smplListWidget.item(0).fileDir)
        elif hasattr(self, 'settingDict') and path.exists(self.settingDict['default dir']):
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

