import sys
import matplotlib
import json
import sympy.utilities.lambdify

from PySide6 import QtWidgets, QtCore, QtGui, QtUiTools
from os import path, getcwd, environ

from . import __version__

from .backend.qtModels import smplItem, subpopItem, chnlModel, gateWidgetItem, quadWidgetItem, splitWidgetItem
from .backend.gates import polygonGateEditor, lineGateEditor, quadrantEditor, polygonGate, lineGate, quadrantGate, split, splitEditor
from .backend.plotWidgets import plotCanvas
from .backend.efio import sessionSave, writeRawFcs, getSysDefaultDir
from .backend.utils import colorGenerator
from .backend.dataIO import drvedParam

from .window_RenameCF import renameWindow_CF
from .window_RenameMap import renameWindow_Map
from .window_Stats import statWindow
from .window_Settings import settingsWindow, localSettings
from .window_About import aboutWindow
from .window_Comp import compWindow
from .wizard_Comp import compWizard
from .window_EditStain import editStainWindow
from .dialog_DrvedParam import drvedParamDialog
from .window_DrvedParamEdit import drvedParamEditWindow

from .uiDesigns.MainWindow_FigOptions import mainUI_figOps
from .uiDesigns.MainWindow_SmplSect import mainUi_SmplSect
from .uiDesigns import UiLoader

matplotlib.use('QT5Agg')


class mainUi(QtWidgets.QMainWindow):
    requestNewWindow = QtCore.Signal(str, QtCore.QPoint)

    def __init__(self, settings: localSettings, sessionSaveFile=None, pos=None):

        # init and setup UI
        super().__init__()
        UiLoader().loadUi('MainWindow.ui', self)

        # load the seetings:
        self.settingDict = settings
        
        # other init
        self._saveFlag = False
        self.chnlDict = dict()
        self.colorGen = colorGenerator()
        self.sessionSavePath = None
        self.holdFigureUpdate = True
        self.gateEditor = None

        self.showLegendCheck.setCheckState(QtCore.Qt.PartiallyChecked)

        # initiate ui models and other windows
        self.gateListWidgetModel = self.gateListWidget.model()

        self.chnlListModel = chnlModel()
        self.xComboBox.setModel(self.chnlListModel)
        self.yComboBox.setModel(self.chnlListModel)

        self.renameWindow = None
        self.settingsWindow = None
        self.compWindow = compWindow()
        self.statWindow = statWindow(self.sessionSavePath if self.sessionSavePath else self.get_dir4Save(),
                                     lambda : self.curGateItems, 
                                     lambda : self.curQuadSplitItem)
        self.aboutWindow = aboutWindow()
        
        self.drvedParamModel = QtGui.QStandardItemModel()
        self.drvedParamEditWindow = drvedParamEditWindow(self.drvedParamModel)
        self.drvedParamEditWindow.newParamRequested.connect(self.handle_DrvedParam)

        # add the matplotlib ui
        matplotlib.rcParams['savefig.directory'] = self.get_dir4Save()
        matplotlib.rcParams['savefig.dpi'] = 600

        self.mpl_canvas = plotCanvas(dpiScale=self.settingDict['plot dpi scale'])

        self.plotLayout = QtWidgets.QVBoxLayout(self.plotBox)
        self.plotLayout.addWidget(self.mpl_canvas.navigationBar)
        self.plotLayout.addWidget(self.mpl_canvas)
        self.mpl_canvas.signal_PlotUpdated.connect(self.statWindow.updateStat)
        self.mpl_canvas.to_load_session.connect(self.handle_OpenSession)

        self.smplsOnPlot = []

        # add the figure property panel
        self.figOpsLayout = QtWidgets.QVBoxLayout(self.figOpsFrame)
        self.figOpsLayout.setContentsMargins(0, 0, 0, 0)
        self.figOpsPanel = mainUI_figOps(self.figOpsFrame)
        self.figOpsLayout.addWidget(self.figOpsPanel)

        # add the sample section
        self.smplSect = mainUi_SmplSect(self, self.colorGen, lambda : self.curGateItems)
        self.smplBox.layout().addWidget(self.smplSect)

        self.smplSect.to_handle_One.connect(self.handle_One)
        self.smplSect.holdFigure.connect(self.handle_HoldFigure)

        self.smplSect.to_load_samples.connect(self.handle_LoadData)
        self.smplSect.loadDataPB.clicked.connect(self.handle_LoadData)
        self.smplTreeWidget = self.smplSect.smplTreeWidget

        # add the progress bar
        self.progBar = QtWidgets.QProgressBar(self)
        self.progBar.reset()
        self.statusbar.addPermanentWidget(self.progBar)

        # add recent file actions
        for filePath in self.settingDict['recent sessions']:
            if path.isfile(filePath) and filePath.endswith('.eflq'):
                normFilePath = path.normpath(filePath)

                if len(normFilePath) > 43:
                    shortenPath = '...' + normFilePath[-40:]
                else:
                    shortenPath = normFilePath

                newAction = self.menuOpen_Recent.addAction(shortenPath)
                newAction.setData(normFilePath)
                newAction.triggered.connect(self.handle_OpenRecentSession)
            else:
                self.settingDict['recent sessions'].remove(filePath)


        # add actions to context memu
        self.gateListWidget.addActions([self.actionDelete_Gate, self.actionEdit_Gate])
        self.qsListWidget.addActions([self.actionDelete_Quad, self.actionQuad2Gate])

        # add the secret testing shortcut
        secretShortcut = QtGui.QShortcut(QtGui.QKeySequence('Alt+C'), self, self.secretCrash)

        # link triggers:
        # menu
        self.actionNew_Session.triggered.connect(self.handle_NewSession)
        self.actionSave.triggered.connect(self.handle_Save)
        self.actionOpen_Session.triggered.connect(self.handle_OpenSession)
        self.actionSave_as.triggered.connect(self.handle_SaveAs)
        self.actionShow_in_folder.triggered.connect(self.handle_ShowInFolder)

        self.actionLoad_Data_Files.triggered.connect(self.handle_LoadData)
        self.actionFor_Cytoflex.triggered.connect(self.handle_RenameForCF)
        self.actionSimple_mapping.triggered.connect(self.handle_RenameMap)
        self.actionDerivedParamNew.triggered.connect(self.handle_DrvedParam)
        self.actionDerivedParamView_Delete.triggered.connect(lambda : self.drvedParamEditWindow.show())
        self.actionEdit_stain_labels.triggered.connect(self.handle_EditStain)

        # actions for exporting raw data
        for action in [self.action_csv, self.action_npy, self.action_npz, self.action_mat]:
            action.triggered.connect(self.handle_ExportDataInGates)

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
        self.qsListWidget.itemSelectionChanged.connect(self.handle_One)
        self.gateListWidget.itemSelectionChanged.connect(self.handle_One)

        self.gateListWidget.itemChanged.connect(self.handle_One)
        self.gateListWidgetModel.rowsMoved.connect(self.handle_One)

        self.xComboBox.currentIndexChanged.connect(self.handle_One)
        self.yComboBox.currentIndexChanged.connect(self.handle_One)

        self.perfCheck.stateChanged.connect(self.handle_One)
        self.showLegendCheck.stateChanged.connect(self.handle_One)
        self.showGatePercCheck.stateChanged.connect(self.handle_One)

        self.figOpsPanel.signal_PlotRedraw.connect(self.handle_One)
        self.compWindow.compValueEdited.connect(self.handle_One)

        # gates
        self.addGateButton.clicked.connect(self.handle_AddGate)
        self.addQuadButton.clicked.connect(self.handle_AddQuad)
        self.gateListWidget.itemSelectionChanged.connect(self.handle_GateSelectionChanged)

        # axes lims
        self.mpl_canvas.signal_AxLimsUpdated.connect(self.figOpsPanel.set_curAxLims)
        self.figOpsPanel.signal_AxLimsNeedUpdate.connect(self.mpl_canvas.updateAxLims)
        self.figOpsPanel.noExtremePB.clicked.connect(self.mpl_canvas.adjustLim_noExtreme)

        # compensation:
        self.compEditPB.clicked.connect(self.handle_EditComp)
        self.compApplyCheck.stateChanged.connect(self.handle_ApplyComp)
        self.compWindow.compValueEdited.connect(lambda : self.set_saveFlag(True))

        # others
        self.clearQuadPB.clicked.connect(lambda : self.qsListWidget.clearSelection())
        self.clearGatePB.clicked.connect(lambda : self.gateListWidget.clearSelection())
        self.axisSwapPB.clicked.connect(self.handle_SwapAxis)

        # load the session if there is a session save file:
        if sessionSaveFile:
            sessionSave.loadSessionSave(self, sessionSaveFile)
            self.set_sessionSavePath(sessionSaveFile)
            self.releaseFigureUpdateHold()
            self.set_saveFlag(False)

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
        self.statusbar.showMessage('Randering plot...')
        QtCore.QCoreApplication.processEvents()
        selectedSmpls = self.smplTreeWidget.selectedItems()

        if len(self.gateListWidget.selectedItems()) > 0:
            selectedGateItem = self.gateListWidget.selectedItems()[0]
        else:
            selectedGateItem = None

        if self.perfCheck.isChecked():
            try:
                perfModeN = self.settingDict['dot N in perf mode']
            except:
                perfModeN = 20000
        else:
            perfModeN = None

        plotType, axScales, axRanges, normOption, smooth, dotSize, dotOpacity, *_ = self.figOpsPanel.curFigOptions

        if isinstance(self.curQuadSplitItem, quadWidgetItem):
            quad_split = self.curQuadSplitItem.quad
        elif isinstance(self.curQuadSplitItem, splitWidgetItem):
            quad_split = self.curQuadSplitItem.split
        else:
            quad_split = None

        compValues = self.compWindow.curComp if self.compApplyCheck.isChecked() else None

        smplsOnPlot = self.mpl_canvas.redraw(
            selectedSmpls,
            chnls=self.curChnls, 
            axisNames=(self.xComboBox.currentText(), self.yComboBox.currentText()),
            compValues = compValues,
            gateList=[gateItem.gate for gateItem in self.curGateItems],
            quad_split = quad_split,
            plotType = plotType, axScales = axScales, axRanges = axRanges, normOption=normOption, smooth=smooth,
            perfModeN = perfModeN, legendOps = self.showLegendCheck.checkState(), gatePercOps = self.showGatePercCheck.isChecked(),
            selectedGateItem=selectedGateItem,
            dotSize=dotSize, dotOpacity=dotOpacity
        )
        self.statusbar.clearMessage()
        self.smplsOnPlot = smplsOnPlot

    def handle_LoadData(self, fileNames=False):
        if (not fileNames) or (fileNames is None):
            fileNames, _ = QtWidgets.QFileDialog.getOpenFileNames(self, 'Open data files', self.get_dir4Save(), filter='*.fcs')
        else:
            fileNames = [name for name in fileNames if name.endswith('.fcs')]

        if len(fileNames) == 0:
            return

        loadingBarDiag = QtWidgets.QProgressDialog('Initializing...', None, 0, len(fileNames) + 1, self)
        loadingBarDiag.setMinimumDuration(500)
        loadingBarDiag.setWindowTitle('Loading FCS files...')
        loadingBarDiag.setWindowModality(QtCore.Qt.WindowModal)
        loadingBarDiag.setValue(0)
        
        newColorList = self.colorGen.giveColors(len(fileNames))

        self.holdFigureUpdate = True
        if len(self.smplTreeWidget.selectedItems()) == 0:
            self.smplTreeWidget.clearSelection()
            setSelectedFlag = True
        else:
            setSelectedFlag = False

        for idx in range(len(fileNames)):
            loadingBarDiag.setLabelText('Loading FCS file {0} of {1}'.format(idx, len(fileNames)))
            loadingBarDiag.setValue(idx + 1)
            self.loadFcsFile(fileNames[idx], newColorList[idx], selected=setSelectedFlag)

        self.smplTreeWidget.resizeColumnToContents(0)
        loadingBarDiag.setValue(idx + 2)
        self.releaseFigureUpdateHold()
        
    def handle_AddGate(self):
        plotType, axScales, *_ = self.figOpsPanel.curFigOptions

        logicleParams = []
        # check if the current plot has logical scales

        revTransforms = [self.mpl_canvas.ax.xaxis.get_transform(), self.mpl_canvas.ax.yaxis.get_transform()]
        for scale, revTransform in zip(axScales, revTransforms):
            if scale == 'logicle':
                transform = revTransform._transform
                logicleParams.append([transform._T, transform._M, transform._W])
            else:
                logicleParams.append(None)

        if plotType == 'Dot plot' or plotType == 'Density plot':
            self.statusbar.showMessage('Left click to draw, Right click to close the gate and confirm, ESC to cancel.', 0)
            self.gateEditor = polygonGateEditor(self.mpl_canvas.ax, canvasParam=(self.curChnls, axScales, logicleParams))
        
        elif plotType == 'Histogram':
            self.statusbar.showMessage('Left click to draw a line gate, Right click or ESC to cancel', 0)
            self.gateEditor = lineGateEditor(self.mpl_canvas.ax, self.curChnls[0])
        
        else:
            return

        self._disableInputForGate(True)
        self.mpl_canvas.setCursor(QtCore.Qt.CrossCursor)
        self.gateEditor.gateConfirmed.connect(self.loadGate)
        self.gateEditor.connectInputs(add_or_edit='add')

    def handle_AddQuad(self):
        plotType, axScales, *_ = self.figOpsPanel.curFigOptions

        if plotType == 'Dot plot' or plotType == 'Density plot':
            self.statusbar.showMessage('Left click to confirm, Right click to cancel', 0)
            self.quadEditor = quadrantEditor(self.mpl_canvas.ax, canvasParam=(self.curChnls, axScales))
            self.quadEditor.quadrantConfirmed.connect(self.loadQuadrant)
            self.quadEditor.addQuad_connect()

        elif plotType == 'Histogram':
            self.statusbar.showMessage('Left click to draw a split, Right click to cancel', 0)
            self.splitEditor = splitEditor(self.mpl_canvas.ax, self.curChnls[0])
            self.splitEditor.splitConfirmed.connect(self.loadSplit)
            self.splitEditor.addSplit_connect()
        
        self._disableInputForGate(True)
        self.mpl_canvas.setCursor(QtCore.Qt.CrossCursor)

    def handle_NewSession(self):
        self.requestNewWindow.emit('', self.pos() + QtCore.QPoint(60, 60))

    def handle_OpenRecentSession(self):
        wichAction = self.sender()
        self.handle_OpenSession(wichAction.data())

    def handle_OpenSession(self, openFileDir=None):
        if not openFileDir:
            openFileDir, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Open session', self.get_dir4Save(), filter='*.eflq')
            self.settingDict.updateRecentSessions(openFileDir)
        if not openFileDir:
            return
        
        if not openFileDir.endswith('.eflq'):
            QtWidgets.QMessageBox.critical(self, 'Open session error!', 
                                           'EasyFlowQ can only open files ends with .eflq at this moment.')

        if self.isWindowAlmostNew():
        #If there is nothing in this current window, update the current window
            self.holdFigureUpdate = True
            errorMsg = sessionSave.loadSessionSave(self, openFileDir)
            if errorMsg is False:
                QtWidgets.QMessageBox.critical(self, 'Load session error!', 
                                               'The session file is eiter corrupted or not a valid session file.')
                return
            elif type(errorMsg) == str:
                QtWidgets.QMessageBox.warning(self, 'Session loaded partially.', errorMsg)

            self.set_sessionSavePath(openFileDir)
            self.releaseFigureUpdateHold()

            self.set_saveFlag(False)
        else:
            self.requestNewWindow.emit(openFileDir, self.pos() + QtCore.QPoint(60, 60))

    def handle_Save(self):
        if self.sessionSavePath:
            # if save exist, replace it at the same dir
            sessionSaveFile = sessionSave(self, self.sessionSavePath)
            sessionSaveFile.saveJson()

            self.settingDict.updateRecentSessions(self.sessionSavePath)
            self.set_saveFlag(False)
        else: 
            self.handle_SaveAs()

    def handle_SaveAs(self):
        saveFilePath, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save session', self.get_dir4Save(), filter='*.eflq')
        self.settingDict.updateRecentSessions(saveFilePath)
        if not saveFilePath:
            return

        self.set_sessionSavePath(saveFilePath)
        sessionSaveFile = sessionSave(self, saveFilePath)
        sessionSaveFile.saveJson()

        self.set_saveFlag(False)
        pass

    def handle_ShowInFolder(self):
        if not (self.sessionSavePath is None):
            qUrl = QtCore.QUrl.fromLocalFile(path.dirname(self.sessionSavePath))
            successFlag = QtGui.QDesktopServices.openUrl(qUrl)
            if successFlag:
                return
        
        QtWidgets.QMessageBox.critical(self, 'Not a proper location', 'Cannot open folder here, or session file not saved yet.')

    def handle_RenameForCF(self):
        if not self.smplTreeWidget.topLevelItemCount():
            QtWidgets.QMessageBox.warning(self, 'Error', 'No samples to rename')
            return

        smplNameList = [self.smplTreeWidget.topLevelItem(idx).fcsFileName for idx in range(self.smplTreeWidget.topLevelItemCount())]

        try:
            self.renameWindow = renameWindow_CF(self.get_dir4Save(), smplNameList)
            self.renameWindow.setWindowModality(QtCore.Qt.ApplicationModal)
            self.renameWindow.renameConfirmed.connect(self.handle_RenameReturn)
            self.renameWindow.show()

        except RuntimeError as e:
            QtWidgets.QMessageBox.warning(self, 'Error', e.args[0])
            return

    def handle_RenameMap(self):
        if not self.smplTreeWidget.topLevelItemCount():
            msgBox = QtWidgets.QMessageBox.warning(self, 'Error', 'No samples to rename')
            return

        smplNameList = [self.smplTreeWidget.topLevelItem(idx).fcsFileName for idx in range(self.smplTreeWidget.topLevelItemCount())]
        self.renameWindow = renameWindow_Map(self.get_dir4Save(), smplNameList)
        self.renameWindow.setWindowModality(QtCore.Qt.ApplicationModal)
        self.renameWindow.renameConfirmed.connect(self.handle_RenameReturn)
        self.renameWindow.show()

    def handle_RenameReturn(self, renameDict):
        self.holdFigureUpdate = True
        for idx in range(self.smplTreeWidget.topLevelItemCount()):
            smplItem = self.smplTreeWidget.topLevelItem(idx)
            if smplItem.fcsFileName in renameDict:
                smplItem.displayName = renameDict[smplItem.fcsFileName]
        
        self.releaseFigureUpdateHold()

    def handle_EditStain(self):
        editStainDict = {}
        self.editStainWindow = editStainWindow(self.chnlListModel, editStainDict)
        isEditAccept = self.editStainWindow.exec_()
        if isEditAccept:
            for chnlKey, stainName in editStainDict.items():
                self.chnlListModel.setStainName(chnlKey, stainName)        

            self.handle_One()

    def handle_DrvedParam(self):
        self.drvedParamDialog = drvedParamDialog(self.chnlListModel)
        isParamAccepted = self.drvedParamDialog.exec()
        if isParamAccepted:
            newParamFormula = self.drvedParamDialog.parsedFormula
            newParamName = self.drvedParamDialog.newParamName

            newDrvedParam = drvedParam(newParamName, newParamFormula)
            self.drvedParamModel.appendRow(newDrvedParam)
            
            self.statusbar.showMessage('Adding derived parameter to samples...')
            self.progBar.reset()
            self.progBar.setMaximum(self.smplTreeWidget.topLevelItemCount())
            self.setDisabled(True)
            for idx in range(self.smplTreeWidget.topLevelItemCount()):
                item = self.smplTreeWidget.topLevelItem(idx)
                item.addDrvedParam_recursively(newDrvedParam)
                self.progBar.setValue(idx + 1)
            
            self.chnlListModel.addChnl(newParamName, 'Derived Parameter')            

            self.statusbar.clearMessage()
            self.progBar.reset()
            self.setEnabled(True)
        else:
            return


    # This function export fcs data that are in gates to csv/npy files, 
    def handle_ExportDataInGates(self):

        # check the sender with the action text to get the output type
        senderAction = self.sender()
        if senderAction.text() == 'as .csv':
            outputType = 'csv'
        elif senderAction.text().startswith('as .npy'):
            outputType = 'npy'
        elif senderAction.text().startswith('as .npz'):
            outputType = 'npz'
        elif senderAction.text().startswith('as .mat'):
            outputType = 'mat'

        if len(self.mpl_canvas.cachedPlotStats.smplItems):
            saveFileDir = QtWidgets.QFileDialog.getExistingDirectory(self, caption='Export raw data', dir=self.sessionSavePath)
            if not saveFileDir:
                return

            self.statusbar.showMessage('Export starting...')

            names = [item.displayName for item in self.mpl_canvas.cachedPlotStats.smplItems]
            fcsDatas = [smpl for smpl in self.mpl_canvas.cachedPlotStats.gatedSmpls]

            writterThread = writeRawFcs(self, names, fcsDatas, saveFileDir, outputType=outputType)
            writterThread.prograssChanged.connect(lambda a, b: self.handle_UpdateProgBar(a, b, 'Exporting: '))
            writterThread.finished.connect(self.handle_ExportDataFinished)

            writterThread.start()

        else:
            QtWidgets.QMessageBox.warning(self, 'Error', 'No sample selected to export')

    def handle_StatWindow(self):
        if not self.statWindow.isVisible():
            self.statWindow.updateStat(self.mpl_canvas.cachedPlotStats, forceUpdate=True)
            self.statWindow.show()
        self.statWindow.raise_()
        self.statWindow.move(self.pos() + QtCore.QPoint(100, 60))
        pass

    def handle_Settings(self, firstTime=False):
        self.settingsWindow = settingsWindow(firstTime=firstTime)
        self.settingsWindow.setWindowModality(QtCore.Qt.ApplicationModal)

        self.settingsWindow.newLocalSettingConfimed.connect(self.handle_NewSetting)

        self.settingsWindow.show()

    def handle_NewSetting(self, newSetting):
        self.settingDict = newSetting

    def handle_SwapAxis(self):
        self.holdFigureUpdate = True
        xAxisTempIndex = self.xComboBox.currentIndex()
        self.xComboBox.setCurrentIndex(self.yComboBox.currentIndex())
        self.yComboBox.setCurrentIndex(xAxisTempIndex)

        self.holdFigureUpdate = False
        self.handle_One()

    def handle_UpdateProgBar(self, curName, progFrac, prefixText=''):
        self.statusbar.showMessage(prefixText + curName)
        self.progBar.setValue(int(progFrac*100))

    def handle_ExportDataFinished(self):
        self.progBar.reset()
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

        plotType, axScales, *_ = self.figOpsPanel.curFigOptions

        # Check if it's a polygone gate, and also change the current plot to the state that the gate was created on
        if isinstance(curSelectedGate, polygonGate):

            # check if the current plot is compatible with the gate
            rightPlotFlag = (plotType in ['Dot plot', 'Density plot']) and list(axScales) == curSelectedGate.axScales and self.curChnls == curSelectedGate.chnls
            if not rightPlotFlag:
                input = QtWidgets.QMessageBox.question(self, 'Change plot?', 'Current ploting parameters does not match those that the gate is created. \
                                                                              Switch to them (current plot will be lost)?')
                if input == QtWidgets.QMessageBox.Yes:
                    self.holdFigureUpdate = True
                    self.set_curChnls(curSelectedGate.chnls)
                    self.figOpsPanel.set_curPlotType('Dot plot')
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
            self.gateEditor.connectInputs(add_or_edit='edit')
        
        elif isinstance(curSelectedGate, lineGate):
            if not (plotType == 'Histogram' and self.curChnls[0] == curSelectedGate.chnl):
                input = QtWidgets.QMessageBox.question(self, 'Change plot?', 'Current ploting parameters does not match those that the gate is created. \
                                                                              Switch to them (current plot will be lost)?')
                if input == QtWidgets.QMessageBox.Yes:
                    self.holdFigureUpdate = True
                    self.set_curChnls(curSelectedGate.chnls)
                    self.figOpsPanel.set_curPlotType('Histogram')

                    self.holdFigureUpdate = False
                    self.handle_One()
                else:
                    return

            self.figOpsPanel.set_axAuto(True, True)

            self.statusbar.showMessage('Left click to drag gate/point; ENTER to confirm edit; ESC to exit', 0)
            self._disableInputForGate(True)
            self.mpl_canvas.setCursor(QtCore.Qt.OpenHandCursor)

            self.gateEditor = lineGateEditor(self.mpl_canvas.ax, gate=curSelectedGate)
            self.gateEditor.gateConfirmed.connect(lambda gate : self.loadGate(gate, replace=curSelected[0]))
            self.gateEditor.connectInputs(add_or_edit='edit')
            pass

        else:
            QtWidgets.QMessageBox.warning(self, 'Editing of this gate type not supported', 'Sorry you cannot edit this type of gates right now!')
            return

    # This function decide if a redraw is recalled when the selection of gate changes.
    def handle_GateSelectionChanged(self):
        if self.mpl_canvas.drawnGates:
            self.handle_One()
            return
        
        if len(self.gateListWidget.selectedItems()) == 0:
            return 

        selectedGate = self.gateListWidget.selectedItems()[0].gate
        if isinstance(selectedGate, polygonGate):
            if selectedGate.chnls == self.curChnls and self.figOpsPanel.curPlotType == 'Dot plot':
                self.handle_One()
            else:
                return
        elif isinstance(selectedGate, lineGate):
            if selectedGate.chnl == self.curChnls[0] and self.figOpsPanel.curPlotType == 'Histogram':
                self.handle_One()
            else:
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
        curSelected = self.qsListWidget.selectedItems()[0]
        if isinstance(curSelected, splitWidgetItem):
            QtWidgets.QMessageBox.warning(self, 'This is a split (1D)', 
                                          'Cannot create gates from 1D split. Please consider using a 1D gate in the \"gate tab\" instead')
            return
        
        newGates = curSelected.quad.generateGates()
        gateNameSuffixes = ['|LL', '|UL', '|LR', '|UR']
        for newGate, suffix in zip(newGates, gateNameSuffixes):
            self.loadGate(newGate, gateName='{0}{1}'.format(curSelected.text(), suffix))
        
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
        compWizDialog = compWizard(self, self.chnlListModel, self.smplTreeWidget, self.gateListWidget, self.get_dir4Save(),
                                   self.compWindow.autoFluoModel, self.compWindow.spillMatModel)
        compWizDialog.finished.connect(self.handle_CompWizardFinished)
        compWizDialog.show()

    def handle_CompWizardFinished(self, result):
        if result == QtWidgets.QDialog.Accepted:
            # deactivate auto-fluorescence compensation for direct loading from wizard
            self.compWindow.autoFluoCheck.setChecked(False)
            self.compApplyCheck.setChecked(True)

    def handle_ExportComp(self):
        jDict = self.compWindow.to_json()
        saveFileDir, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Export compensation', self.get_dir4Save(), filter='*.efComp')
        if not saveFileDir:
            return

        with open(saveFileDir, 'w+') as f:
            json.dump(jDict, f, sort_keys=True, indent=4)

    def handle_ImportComp(self):        
        openFileDir, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Import compensation', self.get_dir4Save(), filter='*.efComp')
        if not openFileDir:
            return 
        
        self.statusbar.clearMessage()
        self.statusbar.showMessage('Loading compensation (may take some time)')

        with open(openFileDir, 'r') as f:
            jDict = json.load(f)
            self.compWindow.load_json(jDict)

        self.statusbar.removeWidget(self.progBar)

    def handle_HoldFigure(self, holdFlag):
        self.holdFigureUpdate = holdFlag
        
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
        # disable inputs that may interfere with gate drawing/editing
        self.toolBox.setEnabled(not disable)
        self.smplBox.setEnabled(not disable)
        self.rightFrame.setEnabled(not disable)

        if self.mpl_canvas.legend:
            self.mpl_canvas.legend.set_draggable(not disable)

    # load fcs file, as well as check if the current channel is compatible and change accordingly
    def loadFcsFile(self, fileDir, color, displayName=None, selected=False):
        self.set_saveFlag(True)
        
        curDrvedParams = [self.drvedParamModel.item(idx) for idx in range(self.drvedParamModel.rowCount())]
        newRootSmplItem = smplItem(self.smplTreeWidget, fileDir, plotColor=QtGui.QColor.fromRgbF(*color), addDrvedParams=curDrvedParams)

        self.smplTreeWidget.addTopLevelItem(newRootSmplItem)
        if displayName:
            newRootSmplItem.displayName = displayName

        if selected:
            newRootSmplItem.setSelected(True)

        # merging the channel dictionary. 
        # If two channel with same channel name (key), but different flurophore (value), the former one will be kept
        newChnlFlag = False
        for key in newRootSmplItem.chnlNameDict:
            isNew = self.chnlListModel.addChnl(key, newRootSmplItem.chnlNameDict[key])
            newChnlFlag = newChnlFlag or isNew
            
        # update the compensation model if there are new channels added
        if newChnlFlag:    
            try:
                self.compWindow.updateChnls(self.chnlListModel)
            except Exception as e:
                self.compWindow.chnlLoadedSuccess = False
                pass

        return newRootSmplItem

    def loadGate(self, gate, replace=None, gateName=None, checkState=QtCore.Qt.Unchecked):
        self.set_saveFlag(True)
        self._disableInputForGate(False)
        self.mpl_canvas.unsetCursor()
        self.statusbar.clearMessage()

        if not (replace is None):
        # trying to replace a gate
            if gate is None:
                self.handle_One()
            else:
                qBox = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Question, 
                                             'Gate edited', 'Do you want to overwrite, or to save as a new gate?', 
                                             QtWidgets.QMessageBox.Discard)
                newGateButton = qBox.addButton('New gate', QtWidgets.QMessageBox.YesRole)
                overwriteButton = qBox.addButton('Overwrite', QtWidgets.QMessageBox.DestructiveRole)
                
                
                input = qBox.exec()

                if qBox.clickedButton() == newGateButton:
                    gateName, flag = QtWidgets.QInputDialog.getText(self, 'New gate', 'Name for the new gate')
                    if not flag:
                        self.handle_One()
                        return
                    newQItem = gateWidgetItem(gateName, gate)
                    self.gateListWidget.addItem(newQItem)

                elif qBox.clickedButton() == overwriteButton:
                    input = QtWidgets.QMessageBox.warning(self, 'Refresh subpopulations?', 
                                                          'Do you want to also regenerate all the affected subpopulations? \n' +
                                                          'Proceeding without regeneration may cause unexpected inconsistency in the future!',
                                                          QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                    
                    replace.gate = gate

                    if input == QtWidgets.QMessageBox.Yes:
                        treeIterator = QtWidgets.QTreeWidgetItemIterator(self.smplTreeWidget)
                        while treeIterator.value():
                            treeItem = treeIterator.value()
                            if isinstance(treeItem, subpopItem):
                                allGateItems = [self.gateListWidget.item(idx) for idx in range(self.gateListWidget.count())]
                                treeItem.gateUpdated(replace, allGateItems)
                            treeIterator += 1
                return replace

        else:
        # this is a new gate, or loading from a save file.
            if gate is None:
                QtWidgets.QMessageBox.warning(self, 'Error', 'Not a valid gate')
                self.handle_One()
            else:
                if not gateName:
                # no name. likely a new gate
                    gateName, flag = QtWidgets.QInputDialog.getText(self, 'New gate', 'Name for the new gate')
                    if not flag:
                        self.handle_One()
                        return
                    
                newQItem = gateWidgetItem(gateName, gate)
                if checkState: 
                    newQItem.setCheckState(checkState)

                self.gateListWidget.addItem(newQItem)
                self.gateListWidget.setCurrentItem(newQItem)
                return newQItem

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

        return [gateItem for gateItem in allGateItems if (gateItem.checkState() is QtCore.Qt.Checked)]

    @property
    def curQuadSplitItem(self):
        qsList = self.qsListWidget.selectedItems()
        if qsList:
            return qsList[0]
        else:
            return None

    @property 
    def saveFlag(self):
        return self._saveFlag

    def set_saveFlag(self, flag: bool):
        if not self._saveFlag == flag:
            self._saveFlag = flag
            self.updateWinTitle()

    # Set the sessionSaveDir, also update the window title
    def set_sessionSavePath(self, sessionSaveDir):
        self.sessionSavePath = sessionSaveDir
        self.statWindow.sessionDir = path.dirname(self.sessionSavePath)
        matplotlib.rcParams['savefig.directory'] = path.dirname(self.sessionSavePath)

        self.updateWinTitle()

    def releaseFigureUpdateHold(self):
        self.holdFigureUpdate = False
        self.handle_One()

    def updateWinTitle(self):
        pathStr = self.sessionSavePath if self.sessionSavePath else 'Not saved'
        self.setWindowTitle('EasyFlowQ v{0}; ({1}{2})'.format(__version__, ('*' if self.saveFlag else ''), pathStr)) 

    def isWindowAlmostNew(self):
        return not (len(self.chnlListModel.keyList) and self.smplTreeWidget.topLevelItemCount() and self.gateListWidget.count())

    def get_dir4Save(self):
        if hasattr(self, 'sessionSavePath') and (not self.sessionSavePath is None):
            return path.dirname(self.sessionSavePath)
        elif hasattr(self, 'smplTreeWidget') and self.smplTreeWidget.topLevelItemCount() > 0:
            return path.dirname(self.smplTreeWidget.topLevelItem(0).fileDir)
        elif path.exists(self.settingDict['default dir']):
            return self.settingDict['default dir']
        else:
            return path.abspath(getSysDefaultDir())

if __name__ == '__main__':

    _excepthook = sys.excepthook
    def myexcepthook(type, value, traceback, oldhook=sys.excepthook):
        _excepthook(type, value, traceback)

    sys.excepthook = myexcepthook

    app = QtWidgets.QApplication(sys.argv)

    testSettings = localSettings(testMode=True)
    window = mainUi(testSettings)
    window.show()
    sys.exit(app.exec_())

