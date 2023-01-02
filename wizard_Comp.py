import sys
from PyQt5 import QtWidgets, QtGui, uic
from PyQt5.QtCore import Qt
from copy import copy

from src.qtModels import smplPlotItem, gateWidgetItem
import numpy as np

wUi, wBase = uic.loadUiType('./uiDesigns/CompWizard.ui') # Load the .ui file

class compWizard(wUi, wBase):
    def __init__(self, parent, chnlModel, smplWidget, gateWidget) -> None:
        wBase.__init__(self, parent)
        self.setupUi(self)

        # setting up all the model for the page1
        self.wizChnlModel = wPage1Model(itemModel=chnlModel)
        self.wizSmplModel = wPage1Model(listWidget=smplWidget)
        self.wizGateModel = wPage1Model(listWidget=gateWidget)

        self.chnlListView.setModel(self.wizChnlModel)
        self.smplListView.setModel(self.wizSmplModel)
        self.gateListView.setModel(self.wizGateModel)

        self.clearAllPB.clicked.connect(self.handle_P2ClearAll)

        self.p2AssignBoxes = []

    
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

        else: 
            return True


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

    def handle_P2ClearAll(self):
        for child in self.wP2Scroll.children():
            if isinstance(child, wAssignBox):
                child.handle_Clear()

wAssignBox, wBaseAssignBox = uic.loadUiType('./uiDesigns/CompWizard_SmplAssignBox.ui')
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
    def __init__(self, listWidget=None, itemModel=None):
        super().__init__()

        items = []
        if not (listWidget is None):
            # Copying items fror listWidget
            for idx in range(listWidget.count()):
                newItem = QtGui.QStandardItem(listWidget.item(idx).data(Qt.DisplayRole))
                newItem.setData(listWidget.item(idx).data(0x100), 0x100)
                newItem.setData(listWidget.item(idx).data(1), 1)
                items.append(newItem)
        elif not (itemModel is None):
            # Copying items from standardItemModel
            for idx in range(itemModel.rowCount()):
                items.append(itemModel.item(idx).clone())
        else:
            return

        for newItem in items:
            newItem.setFlags(newItem.flags() | Qt.ItemIsUserCheckable)
            newItem.setFlags(newItem.flags() & (~Qt.ItemIsEditable))
            newItem.setCheckState(0)
            self.appendRow(newItem)


if __name__ == '__main__':

    app = QtWidgets.QApplication(sys.argv)

    dialog = compWizard(None)
    dialog.show()
    sys.exit(app.exec_())