import sys
from PyQt5 import QtWidgets, QtGui, uic
from PyQt5.QtCore import Qt
from copy import copy

from src.qtModels import smplPlotItem, gateWidgetItem

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

    
    def initializePage(self, id):
        super().initializePage(id)

        if id == 1:
            layoutItem = self.wPage2.layout().takeAt(0)
            while not (layoutItem is None):
                widget = layoutItem.widget()
                del widget
                del layoutItem
                layoutItem = self.wPage2.layout().takeAt(0)
                pass

            self.selectedChnlItems = [self.wizChnlModel.item(idx) for idx in range(self.wizChnlModel.rowCount()) if self.wizChnlModel.item(idx).checkState() == 2]
            self.selectedSmplItems = [self.wizSmplModel.item(idx) for idx in range(self.wizSmplModel.rowCount()) if self.wizSmplModel.item(idx).checkState() == 2]
            self.selectedGateItems = [self.wizGateModel.item(idx) for idx in range(self.wizGateModel.rowCount()) if self.wizGateModel.item(idx).checkState() == 2]

            self.selectedSmplModel = QtGui.QStandardItemModel()
            for smplItem in self.selectedSmplItems:
                self.selectedSmplModel.appendRow(smplItem.clone())

            for chnlItem in self.selectedChnlItems:
                assignUnit = smplAssignBox(self.wPage2, chnlItem.text(), self.selectedSmplModel)
                self.wPage2.layout().addWidget(assignUnit)


# class selectListModel(QtGui.listmod)

wAssignBox, wBaseAssignBox = uic.loadUiType('./uiDesigns/CompWizard_SmplAssignBox.ui')
class smplAssignBox(wAssignBox, wBaseAssignBox):

    def __init__(self, parent, chnlName, comboModel):
        super().__init__(chnlName, parent)
        self.setupUi(self)

        self.setTitle(chnlName)
        self.comboBox.setModel(comboModel)


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
            newItem.setCheckState(0)
            self.appendRow(newItem)


if __name__ == '__main__':

    app = QtWidgets.QApplication(sys.argv)

    dialog = compWizard(None)
    dialog.show()
    sys.exit(app.exec_())