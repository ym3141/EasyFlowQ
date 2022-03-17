import sys
import matplotlib
import pandas as pd
from PyQt5 import QtWidgets, QtCore, QtGui, uic

from src.qtModels import smplPlotItem, chnlModel, gateWidgetItem
from src.gates import polygonGateEditor
from src.plotWidgets import plotCanvas
from src.io import sessionSave
from src.utils import colorGenerator

from window_RenameCF import renameWindow_CF
from window_Stats import statWindow

matplotlib.use('QT5Agg')

mainWindowUi, mainWindowBase = uic.loadUiType('./uiDesigns/MainWindow.ui') # Load the .ui file

class mainUi(mainWindowBase, mainWindowUi):
    requestNewWindow = QtCore.pyqtSignal(str, QtCore.QPoint)

    def __init__(self, sessionSaveFile=None, pos=None):

        # init and setup UI
        mainWindowBase.__init__(self)
        self.setupUi(self)

        buttonGroups = self._organizeButtonGroups()
        self.plotOptionBG, self.xAxisOptionBG, self.yAxisOptionBG, self.normOptionBG = buttonGroups
        
        # other init
        self.version = 0.1
        self.baseDir = './demoSamples/'
        self.set_sessionSaveDir(sessionSaveFile)

        self.chnlDict = dict()
        self.colorGen = colorGenerator()
        self.sessionSaveDir = None
        self.holdFigureUpdate = True
        self.gateEditor = None

        self.renameWindow = None
        self.statWindow = statWindow(self.sessionSaveDir if self.sessionSaveDir else self.baseDir)

        # add the matplotlib ui
        matplotlib.rcParams['savefig.directory'] = self.baseDir

        self.mpl_canvas = plotCanvas()

        self.plotLayout = QtWidgets.QVBoxLayout(self.plotBox)
        self.plotLayout.addWidget(self.mpl_canvas.navigationBar)
        self.plotLayout.addWidget(self.mpl_canvas)

        self.smplsOnPlot = []

        # init ui models
        self.smplListModel = QtGui.QStandardItemModel(self.sampleListView)
        self.sampleListView.setModel(self.smplListModel)
        self.smplSelectionModel = self.sampleListView.selectionModel()

        self.gateListWidgetModel = self.gateListWidget.model()
        # self.gateListView.setModel(self.gateListModel)
        # self.gateSelectionModel = self.gateListView.selectionModel()

        self.chnlListModel = chnlModel()
        self.xComboBox.setModel(self.chnlListModel)
        self.yComboBox.setModel(self.chnlListModel)

        # link triggers:
        # manu
        self.actionNew_Session.triggered.connect(self.handle_NewSession)
        self.actionSave.triggered.connect(self.handle_Save)
        self.actionOpen_Session.triggered.connect(self.handle_OpenSession)
        self.actionSave_as.triggered.connect(self.handle_SaveAs)

        self.actionLoad_Data_Files.triggered.connect(self.handle_LoadData)
        self.actionFor_Cytoflex.triggered.connect(self.handle_RenameForCF)
        self.actionExport_data_in_current_gates.triggered.connect(self.handle_ExportDataInGates)

        self.actionStats_window.triggered.connect(self.handle_StatWindow)

        # everything update figure
        self.smplSelectionModel.selectionChanged.connect(self.handle_FigureUpdate)

        self.gateListWidget.itemChanged.connect(self.handle_FigureUpdate)
        self.gateListWidgetModel.rowsMoved.connect(self.handle_FigureUpdate)

        self.xComboBox.currentIndexChanged.connect(self.handle_FigureUpdate)
        self.yComboBox.currentIndexChanged.connect(self.handle_FigureUpdate)

        for bg in buttonGroups:
            for radio in bg.buttons():
                radio.clicked.connect(self.handle_FigureUpdate)
        self.perfCheck.stateChanged.connect(self.handle_FigureUpdate)

        self.smoothSlider.valueChanged.connect(self.handle_FigureUpdate)

        # gates
        self.addGateButton.clicked.connect(self.handle_AddGate)

        # load the session if there is a session save file:
        if sessionSaveFile:
            sessionSave.loadSessionSave(self, sessionSaveFile)
            self.holdFigureUpdate = False
            self.handle_FigureUpdate()

        if pos:
            self.move(pos)

        self.holdFigureUpdate = False


    def handle_LoadData(self):
        fileNames, _ = QtWidgets.QFileDialog.getOpenFileNames(self, 'Open data files', self.baseDir, filter='*.fcs')
        newColorList = self.colorGen.giveColors(len(fileNames))

        for fileName, newColor in zip(fileNames, newColorList):
            self.loadFcsFile(fileName, newColor)

    def handle_FigureUpdate(self):
        # this function is used to process info for the canvas to redraw

        if self.holdFigureUpdate:
            return

        selectedSmpls = [self.smplListModel.itemFromIndex(idx) for idx in self.sampleListView.selectedIndexes()]

        perfModeN = 20000 if self.perfCheck.isChecked() else None

        smplsOnPlot = self.mpl_canvas.redraw(selectedSmpls, 
                                             chnlNames=self.curChnls, 
                                             axisNames=(self.xComboBox.currentText(), self.yComboBox.currentText()),
                                             axScales=self.curAxScales,
                                             gateList=[gateItem.gate for gateItem in self.curGateItems],
                                             plotType = self.curPlotType,
                                             normOption = self.curNormOption,
                                             perfModeN = perfModeN,
                                             smooth = self.smoothSlider.value()
        )

        self.smplsOnPlot = smplsOnPlot

        if self.statWindow.isVisible() and len(self.smplsOnPlot):
            self.statWindow.updateStat(self.smplsOnPlot, self.curChnls, self.curGateItems)

    def handle_AddGate(self):
        self._disableInputForGate(True)
        self.mpl_canvas.setCursor(QtCore.Qt.CrossCursor)

        self.statusbar.showMessage('Left click to draw, Right click to close the gate and confirm', 0)

        self.gateEditor = polygonGateEditor(self.mpl_canvas.ax, self.loadGate, 
                                            canvasParam=(self.curChnls, self.curAxScales))
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
            self.handle_FigureUpdate()
        else:
            self.requestNewWindow.emit(openFileDir, self.pos() + QtCore.QPoint(60, 60))

    def handle_Save(self):
        if self.sessionSaveDir:
            # if save exist, replace it at the same dir
            sessionSaveFile = sessionSave(self, self.sessionSaveDir)
            sessionSaveFile.saveJson()
        else: 
            self.handle_SaveAs()

    def handle_SaveAs(self):
        saveFileDir, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save session', self.baseDir, filter='*.eflq')
        if not saveFileDir:
            return

        self.set_sessionSaveDir(saveFileDir)
        sessionSaveFile = sessionSave(self, saveFileDir)
        sessionSaveFile.saveJson()
        pass

    def handle_RenameForCF(self):
        if  not self.smplListModel.rowCount():
            msgBox = QtWidgets.QMessageBox.warning(self, 'Error', 'No samples to rename')
            return

        openFileDir, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Load xlsx file for renaming', self.baseDir, filter='*.xlsx')
        if not openFileDir:
            return

        smplNameList = [self.smplListModel.item(idx).fcsFileName for idx in range(self.smplListModel.rowCount())]
        self.renameWindow = renameWindow_CF(openFileDir, smplNameList)
        self.renameWindow.setWindowModality(QtCore.Qt.ApplicationModal)
        self.renameWindow.renameConfirmed.connect(self.handle_RenameForCF_return)
        self.renameWindow.show()

    def handle_RenameForCF_return(self, renameDict):
        for idx in range(self.smplListModel.rowCount()):
            smplItem = self.smplListModel.item(idx)
            if smplItem.fcsFileName in renameDict:
                smplItem.displayName = renameDict[smplItem.fcsFileName]

        self.handle_FigureUpdate()

    def handle_ExportDataInGates(self):

        if len(self.statWindow.cur_Name_RawData_Pairs):
            saveFileDir, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Export raw data', self.sessionSaveDir, filter='*.xlsx')
            if not saveFileDir:
                return

            self.statusbar.showMessage('Start exporting')
    
            with pd.ExcelWriter(saveFileDir) as writer:
                for idx, pair in enumerate(self.statWindow.cur_Name_RawData_Pairs):
                    name, fcsData = pair
                    df2write = pd.DataFrame(fcsData, columns=fcsData.channels)
                    df2write.to_excel(writer, sheet_name=name)

            self.statusbar.showMessage('Fished exporting')
        else:
            QtWidgets.QMessageBox.warning(self, 'Error', 'No sample selected to export')

    def handle_StatWindow(self):
        if not self.statWindow.isVisible():
            self.statWindow.updateStat(self.smplsOnPlot, self.curChnls, self.curGateItems)
            self.statWindow.show()
        self.statWindow.raise_()
        self.statWindow.move(self.pos() + QtCore.QPoint(100, 60))
        pass

    def _organizeButtonGroups(self):
        # Create button groups to manage the radio button for plot options

        plotOptionBG, xAxisOptionBG, yAxisOptionBG, normOptionBG = [QtWidgets.QButtonGroup(self) for i in range(4)]

        plotOptionBG.addButton(self.dotRadio, 0)
        plotOptionBG.addButton(self.histRadio, 1)

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

    def _disableInputForGate(self, disable=True):
        self.toolBox.setEnabled(not disable)
        for idx in range(self.leftLayout.count()):
            self.leftLayout.itemAt(idx).widget().setEnabled(not disable)
        for idx in range(self.rightLayout.count()):
            self.rightLayout.itemAt(idx).widget().setEnabled(not disable)

    def loadFcsFile(self, fileDir, color, displayName=None, selected=False):
        newSmplItem = smplPlotItem(fileDir, plotColor=QtGui.QColor.fromRgbF(*color))
        self.smplListModel.appendRow(newSmplItem)

        if selected:
            self.smplSelectionModel.select(self.smplListModel.indexFromItem(newSmplItem), QtCore.QItemSelectionModel.Select)

        # merging the channel dictionary. 
        # If two channel with same channel name (key), but different flurophore (value), the former one will be kept
        for key in newSmplItem.chnlNameDict:
            self.chnlListModel.addChnl(key, newSmplItem.chnlNameDict[key])

    def loadGate(self, gate, replace=None, gateName=None):
        self._disableInputForGate(False)
        self.mpl_canvas.unsetCursor()
        self.statusbar.clearMessage()
        if replace:
            pass
        else:
            if gate is None:
                QtWidgets.QMessageBox.warning(self, 'Error', 'Not a valid gate')
                self.handle_FigureUpdate()
            else:
                if not gateName:
                    gateName, flag = QtWidgets.QInputDialog.getText(self, 'New gate', 'Name for the new gate')
                    if not flag:
                        self.handle_FigureUpdate()
                        return
                
                self._disableInputForGate(False)

                newQItem = gateWidgetItem(gateName, gate)
                # newQItem.setData(0x100, gate)
                # newQItem.setCheckable(True)
                self.gateListWidget.addItem(newQItem)

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

    def set_sessionSaveDir(self, sessionSaveDir):
        # Set the sessionSaveDir, also update the window title
        self.sessionSaveDir = sessionSaveDir
        self.setWindowTitle('EasyFlowQ v{0:.1f}; ({1})'.format(self.version, (self.sessionSaveDir if self.sessionSaveDir else 'Not saved')))

    def isWindowAlmostNew(self):
        return not (len(self.chnlListModel.keyList) and self.smplListModel.rowCount() and self.gateListWidget.count())


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = mainUi()
    window.show()
    sys.exit(app.exec_())
