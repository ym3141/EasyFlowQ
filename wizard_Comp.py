import sys
from PyQt5 import QtWidgets, QtGui, uic
from PyQt5.QtCore import Qt, pyqtSignal
from copy import copy
from os import path, getcwd

from backend.qtModels import gateWidgetItem
from backend.comp import autoFluoTbModel, spillMatTbModel
import numpy as np
from scipy.stats.mstats import gmean
import pandas as pd

import warnings
import json
from backend.efio import getSysDefaultDir

__location__ = path.realpath(path.join(getcwd(), path.dirname(__file__)))
wUi, wBase = uic.loadUiType(path.join(__location__, 'uiDesigns/CompWizard.ui')) # Load the .ui file

class compWizard(wUi, wBase):
    mainCompValueEdited = pyqtSignal()

    def __init__(self, parent, chnlModel, smplWidget, gateWidget, dir4Save,
                 curMainAutoFluoModel:autoFluoTbModel, curMainSpillMatModel:spillMatTbModel) -> None:
        wBase.__init__(self, parent)
        self.setupUi(self)

        # link the vertical scrollbars on page4
        self.spillMatTable.verticalScrollBar().valueChanged.connect(self.autoFluoTable.verticalScrollBar().setValue)
        self.autoFluoTable.verticalScrollBar().valueChanged.connect(self.spillMatTable.verticalScrollBar().setValue)

        # visual tweak for page4
        self.autoFluoTable.verticalHeader().setMaximumSize(125, 16777215)
        self.autoFluoTable.horizontalHeader().setMaximumSectionSize(125)

        # setting up all the model for the page1
        self.wizChnlModel = wPage1Model(chnlItemModel=chnlModel)
        self.wizSmplModel = wPage1Model(smplTreeWidget=smplWidget)
        self.wizGateModel = wPage1Model(gateListWidget=gateWidget)

        self.chnlListView.setModel(self.wizChnlModel)
        self.smplListView.setModel(self.wizSmplModel)
        self.gateListView.setModel(self.wizGateModel)

        # UI boxed from page2
        self.p2AssignBoxes = []

        # Manage the button group at page3
        self.meanMethodBG = QtWidgets.QButtonGroup(self)
        for radio in [self.medRadio, self.gMeanRadio, self.meanRadio]:
            self.meanMethodBG.addButton(radio)

        # Save a copy of the channel name dict
        self.chnlNameDict = chnlModel.chnlNameDict

        # connect buttuns on several pages
        self.clearAllPB.clicked.connect(self.handle_P2ClearAll)
        self.load2MainPB.clicked.connect(self.handle_load2MainComp)
        self.exportPB.clicked.connect(self.handle_ExportMat)

        finish_button = self.button(QtWidgets.QWizard.FinishButton)
        finish_button.disconnect()
        finish_button.clicked.connect(self.handle_WizFinish)

        # other
        self.dir4Save = dir4Save
        self.newCompFlag = False
        self.curMainAutoFluoModel = curMainAutoFluoModel
        self.curMainSpillMatModel = curMainSpillMatModel


    def initializePage(self, id):
        super().initializePage(id)

        if id == 1:
            # The folloing code delet anything in the page2 scrollArea layout, very hecky
            layoutItem = self.wP2Scroll.layout().takeAt(0)
            while not (layoutItem is None):
                if layoutItem.widget() is None:
                    #That's probably the spacer, and the last one.
                    break
                layoutItem.widget().setParent(None)
                layoutItem = self.wP2Scroll.layout().takeAt(0)
            del layoutItem

            # Constract the lists of selected channel/sample/gate
            self.selectedChnlItems = [self.wizChnlModel.item(idx) for idx in range(self.wizChnlModel.rowCount()) if self.wizChnlModel.item(idx).checkState() == 2]
            self.selectedSmplItems = [self.wizSmplModel.item(idx) for idx in range(self.wizSmplModel.rowCount()) if self.wizSmplModel.item(idx).checkState() == 2]
            self.selectedGateItems = [self.wizGateModel.item(idx) for idx in range(self.wizGateModel.rowCount()) if self.wizGateModel.item(idx).checkState() == 2]

            # Model for the comboboxes
            self.selectedSmplModel = QtGui.QStandardItemModel()
            for smplItem in self.selectedSmplItems:
                comboItem = smplItem.clone()
                comboItem.setFlags(comboItem.flags() & (~Qt.ItemIsUserCheckable))
                comboItem.setData(None, role=Qt.CheckStateRole)
                self.selectedSmplModel.appendRow(comboItem)

            # Construct the boxes and add them to the scroll area
            autoFBox = smplAssignBox(self.wP2Scroll, 'temp', self.selectedSmplModel)
            autoFBox.setTitle('No-color control (for auto-fluorescence)')
            self.wP2Scroll.layout().addWidget(autoFBox)
            self.p2AssignBoxes = [autoFBox]
            for chnlItem in self.selectedChnlItems:
                assignUnit = smplAssignBox(self.wP2Scroll, chnlItem.text(), self.selectedSmplModel)
                self.wP2Scroll.layout().addWidget(assignUnit)
                self.p2AssignBoxes.append(assignUnit)
            self.wP2Scroll.layout().addStretch()

        if id == 2:
            self.assignedPairs = []
            for p2AssignBox in self.p2AssignBoxes:
                self.assignedPairs.append((p2AssignBox.chnlName, p2AssignBox.comboBox.currentIndex()))

            if self.assignedPairs[0][1] == -1:
                self.noAutoFCheck.setDisabled(True)
                self.noAutoFCheck.setCheckState(2)
                self.noAutoF = True
            else:
                self.noAutoFCheck.setDisabled(False)
                self.noAutoFCheck.setCheckState(0)
                self.noAutoF = False

        if id == 3:
            self.autoFluoTable.setModel(self.preAutoFluoModel)
            self.spillMatTable.setModel(self.preSpillMatModel)

            self.autoFluoTable.selectionModel().selectionChanged.connect(self.handle_SelectSpillMat)

    def validateCurrentPage(self):
        if self.currentId() == 0:
            chnlN = len([self.wizChnlModel.item(idx) for idx in range(self.wizChnlModel.rowCount()) if self.wizChnlModel.item(idx).checkState() == 2])
            smplN = len([self.wizSmplModel.item(idx) for idx in range(self.wizSmplModel.rowCount()) if self.wizSmplModel.item(idx).checkState() == 2])
            
            if chnlN == 0 or smplN == 0:
                QtWidgets.QMessageBox.critical(self, 
                    'No channel or sample selected!', 'The wizard won\'t be able to work with no sample or channel!')
                return False

            elif smplN - chnlN < 0:
                input = QtWidgets.QMessageBox.warning(self, 
                    'Not enough sample for each channel', 
                    'There is not enough sample for every channel. \nIn the next page, ' + 
                        'channels that don\'t have a sample assigned will be ignored in calculation. Proceed?',
                    buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
                    )

                if input == QtWidgets.QMessageBox.Yes:
                    return True
                else:
                    return False
    
            elif smplN - chnlN < 1:
                input = QtWidgets.QMessageBox.warning(self, 
                    'Not enough sample for each channel and auto-fluoresence', 
                    'There is not enough sample for every channel and auto-fluoresence. \nIn the next page, ' +
                        'auto-fluorescence will be ignored if no-color sample is not assigend. Or, ' +
                        'channels that don\'t have a sample assigned will be ignored in calculation. Proceed?',
                    buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
                    )

                if input == QtWidgets.QMessageBox.Yes:
                    return True
                else:
                    return False

            else:
                return True

        elif self.currentId() == 1:
            assignedIndices = []
            for p2AssignBox in self.p2AssignBoxes:
                assignedIndices.append(p2AssignBox.comboBox.currentIndex())
            
            assignedIndices = np.array(assignedIndices)
            uniqueSmpl, uniqueSmplCount = np.unique(assignedIndices, return_counts=True)

            if np.array_equal(uniqueSmpl, [-1]):
                QtWidgets.QMessageBox.critical(self, 
                    'Nothing is assigned!', 'Please assign the no-color and single-color samples to the channels')
                return False
            else:
                if np.any(uniqueSmplCount[1:] > 1):
                    input = QtWidgets.QMessageBox.warning(self, 
                        'Sample assigned to multiple channels', 
                        'One or more samples are assigned to multiple channels. ' +
                            'This may cause problem in further steps. proceed?',
                        buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
                        )

                    if input == QtWidgets.QMessageBox.No:
                        return False

                if np.any(uniqueSmpl == -1):
                    input = QtWidgets.QMessageBox.warning(self, 
                    'Some channel (or auto-fluorescence) have no sample assigned', 
                    'Channels (or auto-fluorescence) without a assigned sample will be ignored during the calculation later. Proceed?',
                    buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
                    )

                    if input == QtWidgets.QMessageBox.No:
                        return False
                    
                return True

        elif self.currentId() == 2:
            self.progressLabel.setText('Starting...')
            self.progressBar.setValue(5)
                        
            gateList = [item.data(0x100) for item in self.selectedGateItems]
            self.meanFunc = np.mean
            if self.meanMethodBG.checkedButton is self.medRadio:
                self.meanFunc = np.median
            elif self.meanMethodBG.checkedButton is self.gMeanRadio:
                self.meanFunc = gmean

            self.chnlKeyList = [item.data(0x101) for item in self.selectedChnlItems]

            if self.percentileCheck.checkState() == 2:
                self.usePercentile = self.percentileSlider.value()
            else:
                self.usePercentile = -1
            
            self.progressLabel.setText('Calculating for auto-fluorescence...')
            self.progressBar.setValue(10)

            if self.noAutoFCheck.checkState() == 0 and (not self.noAutoF):
                noColorFCS = self.selectedSmplItems[self.assignedPairs[0][1]].data(role=0x100)
                inGateFlag = np.ones(noColorFCS.shape[0], dtype=bool)

                for gate in gateList:
                    if gate.chnls[0] in noColorFCS.channels and gate.chnls[1] in noColorFCS.channels:
                        newFlag = gate.isInsideGate(noColorFCS)
                        inGateFlag = np.logical_and(gate.isInsideGate(noColorFCS), inGateFlag)

                    else: 
                        warnings.warn('Sample does not have channel(s) for this gate, skipping this gate', RuntimeWarning)
                
                gatedFCS = noColorFCS[inGateFlag, :]
                self.autoFs = self.meanFunc(gatedFCS, 0, keepdims=True)
            else: 
                self.autoFs = None

            self.progressLabel.setText('Calculating for spill matrix...')
            self.progressBar.setValue(20)

            smplSpills = dict()
            for idx, chnlKey in enumerate(self.chnlKeyList):
                smplIdx = self.assignedPairs[idx + 1][1]
                if smplIdx != -1:
                    smplFCS = self.selectedSmplItems[smplIdx].data(0x100)

                    inGateFlag = np.ones(smplFCS.shape[0], dtype=bool)
                    for gate in gateList:
                        if gate.chnls[0] in smplFCS.channels and gate.chnls[1] in smplFCS.channels:
                            newFlag = gate.isInsideGate(smplFCS)
                            inGateFlag = np.logical_and(gate.isInsideGate(smplFCS), inGateFlag)

                        else: 
                            warnings.warn('Sample does not have channel(s) for this gate, skipping this gate', RuntimeWarning)
                    
                    gatedFCS = smplFCS[inGateFlag, :]

                    if self.usePercentile != -1:
                        percMask = gatedFCS[:, chnlKey] >= np.percentile(gatedFCS[:, chnlKey], 100 - self.usePercentile / 100)
                        gatedFCS = gatedFCS[percMask, :]

                    if self.noAutoFCheck.checkState() == 0 and not (self.autoFs is None):
                        gatedFCS = gatedFCS - self.autoFs

                    meanFCS = self.meanFunc(gatedFCS, 0, keepdims=True)
                    spills = meanFCS / meanFCS[0, chnlKey]
                    smplSpills[chnlKey] = spills
                else:
                    smplSpills[chnlKey] = None

                self.progressLabel.setText('Finishing calculation on spill matrix: ({0}/{1})'.format(idx, len(self.chnlKeyList)))
                self.progressBar.setValue(10 + 70 * ((idx + 1) / len(self.chnlKeyList)))

            self.progressLabel.setText('Preparing autofluorescence matrix for preview')
            self.progressBar.setValue(80)

            self.preAutoFluoModel = autoFluoTbModel(self.chnlKeyList, [self.chnlNameDict[chnl] for chnl in self.chnlKeyList], editable=False)
            self.preSpillMatModel = spillMatTbModel(self.chnlKeyList, editable=False)

            if not (self.autoFs is None):
                autoDF = pd.DataFrame(self.autoFs.T, index=(self.autoFs.channels))
                self.preAutoFluoModel.loadDF(autoDF)

            self.progressLabel.setText('Preparing spill matrix for preview')
            self.progressBar.setValue(90)
            
            spillDF = pd.DataFrame(columns=self.chnlKeyList)
            for idx, chnlKey in enumerate(self.chnlKeyList):
                if smplSpills[chnlKey] is None:
                    spillDF.loc[chnlKey] = [0] * idx + [1] + [0] * (len(self.chnlKeyList) - idx - 1)
                else:
                    spillDF.loc[chnlKey] = smplSpills[chnlKey][0, (self.chnlKeyList)]
            self.preSpillMatModel.loadMatDF(spillDF * 100)

            self.progressLabel.setText('Done!')
            self.progressBar.setValue(100)
            self.newCompFlag = True

            return True
        else: 
            return True

    def handle_P2ClearAll(self):
        for child in self.wP2Scroll.children():
            if isinstance(child, wAssignBox):
                child.handle_Clear()

    def handle_SelectSpillMat(self, selected):
        index = selected.indexes()[0]
        print(selected.indexes())
        self.spillMatTable.selectRow(index.row())
    
    def handle_load2MainComp(self):
        if not (self.curMainSpillMatModel.isIdentity() and self.curMainAutoFluoModel.isZeros()):
            input = QtWidgets.QMessageBox.warning(self, 
                    'Overwrite current compensation?',
                    'The current compensation is not zero/identity! This action will overwrite some part of the current one.' +
                    'Yes to proceed.',
                    buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel
                    )
            if input == QtWidgets.QMessageBox.Cancel:
                return
            
        self.curMainAutoFluoModel.loadDF(self.preAutoFluoModel.dfData)
        self.curMainSpillMatModel.loadMatDF(self.preSpillMatModel.dfData)
        self.newCompFlag = False

    def handle_ExportMat(self):
        jDict = dict()
        jDict['useAutoFluo'] = None
        
        jDict['keyList'] = self.chnlKeyList
        jDict['autoFluo'] = self.preAutoFluoModel.to_json()
        jDict['spillMat'] = self.preSpillMatModel.to_json()

        saveFileDir, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Export compensation', self.dir4Save, filter='*.efComp')
        if not saveFileDir:
            return

        with open(saveFileDir, 'w+') as f:
            json.dump(jDict, f, sort_keys=True, indent=4)
        self.newCompFlag = False

    def handle_WizFinish(self):
        if self.newCompFlag:
            input = QtWidgets.QMessageBox.warning(self, 'Compenation not used or save!',
                                                  'The new compensation has not been applied into the main window or exported. You will lose it if you exit now. Yes to exist',
                                                  QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel)
        
            if input == QtWidgets.QMessageBox.Yes:
                self.accept()

        else:
            self.accept()

# UI box on page2
wAssignBox, wBaseAssignBox = uic.loadUiType(path.join(__location__, 'uiDesigns/CompWizard_SmplAssignBox.ui'))
class smplAssignBox(wAssignBox, wBaseAssignBox):

    def __init__(self, parent, chnlName, comboModel):
        super().__init__(chnlName, parent)
        self.setupUi(self)
        
        self.chnlName = chnlName
        self.setTitle('Single-color sample for {0}'.format(chnlName))
        self.comboBox.setModel(comboModel)
        self.comboBox.setCurrentIndex(-1)

        self.clearPB.clicked.connect(self.handle_Clear)

    def handle_Clear(self):
        self.comboBox.setCurrentIndex(-1)


class wPage1Model(QtGui.QStandardItemModel):
    def __init__(self, smplTreeWidget=None, gateListWidget=None, chnlItemModel=None):
        super().__init__()

        items = []
        if smplTreeWidget is not None:
            # Copying items fror smplListWidget
            for idx in range(smplTreeWidget.topLevelItemCount()):
                newItem = QtGui.QStandardItem(smplTreeWidget.topLevelItem(idx).data(0, Qt.DisplayRole))
                newItem.setData(smplTreeWidget.topLevelItem(idx).data(0, 0x100), 0x100)
                newItem.setData(smplTreeWidget.topLevelItem(idx).data(0, 1), 1)
                newItem.setCheckState(2)
                items.append(newItem)

        elif gateListWidget is not None:
            # Copying items fror gatelListWidget
            for idx in range(gateListWidget.count()):
                newItem = QtGui.QStandardItem(gateListWidget.item(idx).data(Qt.DisplayRole))
                newItem.setData(gateListWidget.item(idx).data(0x100), 0x100)
                newItem.setData(gateListWidget.item(idx).data(1), 1)
                newItem.setCheckState(gateListWidget.item(idx).checkState())
                items.append(newItem)
            
        elif chnlItemModel is not None:
            # Copying items from standardItemModel / (channels)
            for idx in range(chnlItemModel.rowCount()):
                items.append(chnlItemModel.item(idx).clone())
                items[-1].setCheckState(0)
        else:
            return

        for newItem in items:
            newItem.setFlags(newItem.flags() | Qt.ItemIsUserCheckable)
            newItem.setFlags(newItem.flags() & (~Qt.ItemIsEditable))
            # newItem.setCheckState(0)
            self.appendRow(newItem)


if __name__ == '__main__':

    app = QtWidgets.QApplication(sys.argv)

    dialog = compWizard(None)
    dialog.show()
    sys.exit(app.exec_())