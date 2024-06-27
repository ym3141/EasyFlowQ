'''
This file is intented to seperate some codes from the window_Main.py file.
Currently it will only host codes dealing with the UI aspect of the sample section,
as well as codes that are "self-contained". Core codes about loading
fcs files are still handled by the main_Window.py, as they're 
too integrated to the other part of the program.
'''

import sys
from os import environ, path, getcwd

from PySide6 import QtWidgets, QtCore, QtGui, QtUiTools

from ..backend.qtModels import smplItem, subpopItem

__location__ = path.realpath(path.join(getcwd(), path.dirname(__file__)))
sys.path.append(path.join(__location__, 'resource'))
smplSectUi, smplSectBase = QtUiTools.loadUiType(path.join(__location__, 'MainWindow_SmplSect.ui')) # Load the .ui file

class mainUi_SmplSect(smplSectBase, smplSectUi):
    to_handle_One = QtCore.Signal()
    to_load_samples = QtCore.Signal(list)
    holdFigure = QtCore.Signal(bool)

    def __init__(self, parent, colorGen, curGateItems_func):

        smplSectBase.__init__(self, parent)
        self.setupUi(self)

        # self.smplTreeWidget = smplTreeWidgetCls(self)
        # self.layout().addWidget(self.smplTreeWidget)

        self.colorGen = colorGen
        self.curGateItems_func = curGateItems_func

        # Give the color button a icon
        self.colorPB.setIcon(QtGui.QIcon(path.join(__location__, 'resource/PelatteIcon2.png')))

        # add actions to context manu and link functions
        self.smplTreeWidget.addActions([self.actionAdd_subpops_Current_gating])
        self.smplTreeWidget.addActions([self.actionDelete_sample])
        self.actionDelete_sample.triggered.connect(self.handle_DeleteSmpls)
        self.actionAdd_subpops_Current_gating.triggered.connect(self.handle_AddSubpops)


        self.smplTreeWidget.itemChanged.connect(self.to_handle_One)
        self.smplTreeWidget.itemSelectionChanged.connect(self.to_handle_One)

        # Connect signals for UI elements
        # Note: The load data PB is handled in window_Main.py
        self.colorPB.clicked.connect(self.handle_ChangeSmplColor)
        self.expandAllPB.clicked.connect(lambda : self.handle_ExpandCollapseSmplTree(expand=True))
        self.collapseAllPB.clicked.connect(lambda : self.handle_ExpandCollapseSmplTree(expand=False))
        self.selectRootsPB.clicked.connect(self.handle_SelectAllRoots)
        self.searchSmplEdit.returnPressed.connect(self.handle_SearchSmplTree)

        # Set up drag and drop
        self.setAcceptDrops(True)

    def handle_ChangeSmplColor(self):
        colorDiag = QtWidgets.QColorDialog()
        cstmColors = self.colorGen.giveColors_div(colorDiag.customCount())
        for idx, cstmColor in enumerate(cstmColors):
            colorDiag.setCustomColor(idx, QtGui.QColor.fromRgbF(*cstmColor))

        color = colorDiag.getColor(initial=QtGui.QColor('black'))

        if color.isValid():
            for item in self.smplTreeWidget.selectedItems():
                item.plotColor = color


    def handle_ExpandCollapseSmplTree(self, expand=True):
        treeIterator = QtWidgets.QTreeWidgetItemIterator(self.smplTreeWidget)
        while treeIterator.value():
            if expand:
                treeIterator.value().setExpanded(True)
            else:
                treeIterator.value().setExpanded(False)
            treeIterator += 1

    def handle_SelectAllRoots(self):
        self.holdFigure.emit(True)
        self.smplTreeWidget.clearSelection()
        for idx in range(self.smplTreeWidget.topLevelItemCount()):
            self.smplTreeWidget.topLevelItem(idx).setSelected(True)
        self.holdFigure.emit(False)
        self.to_handle_One.emit()

    def handle_SearchSmplTree(self):
        self.holdFigure.emit(True)
        self.smplTreeWidget.clearSelection()

        keyword = self.searchSmplEdit.text()
        treeIterator = QtWidgets.QTreeWidgetItemIterator(self.smplTreeWidget)
        while treeIterator.value():
            smplItem = treeIterator.value()
            if keyword in smplItem.text(0):
                smplItem.setSelected(True)
            treeIterator += 1
        
        self.holdFigure.emit(False)
        self.to_handle_One.emit()

    def handle_DeleteSmpls(self):
        curSelected = self.smplTreeWidget.selectedItems()
        if len(curSelected) == 0:
            QtWidgets.QMessageBox.warning(self, 'No sample selected', 'Please select sample(s) to delete')
            return
        delSmplNameList = [smpl.text(0) for smpl in curSelected]
        delSmplNameList_str = '\n' + '\n'.join(delSmplNameList)
        input = QtWidgets.QMessageBox.question(self, 'Delete samples or subpops?', 
                                               'Are you sure to delete the following samples or subpops?' + delSmplNameList_str)

        if input == QtWidgets.QMessageBox.Yes:
            self.holdFigure.emit(True)
            for item in curSelected:
                if isinstance(item, subpopItem):
                    parentItem = item.parent()
                    parentItem.removeChild(item)
                    del item
                elif isinstance(item, smplItem):
                    deleteIdx = self.smplTreeWidget.indexOfTopLevelItem(item)
                    deletedItem = self.smplTreeWidget.takeTopLevelItem(deleteIdx)
                    del deletedItem
            self.holdFigure.emit(False)
            self.to_handle_One.emit()

    def handle_AddSubpops(self):
        selectedSmpls = self.smplTreeWidget.selectedItems()
        curGateItems = self.curGateItems_func()

        if len(curGateItems) == 0:
            QtWidgets.QMessageBox.warning(self, 'No gate selected', 'You need to at least have one gate to create sub-populations')

        inputStr, flag = QtWidgets.QInputDialog.getText(self, 'Name for subpopulation', 
                                                        'Name (\"$\" will be replaced by parent name):', text='$_')
        
        if flag == False:
            return

        for selectedSmpl in selectedSmpls:
            subpopColor = self.colorGen.giveColors(1)[0]
            subpopName = inputStr.replace('$', selectedSmpl.displayName)
            newSubpopItem = subpopItem(selectedSmpl, QtGui.QColor.fromRgbF(*subpopColor), subpopName, curGateItems)
          
            selectedSmpl.setExpanded(True)
        
        self.smplTreeWidget.resizeColumnToContents(0)

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
            smpls_to_load = [url.toLocalFile() for url in event.mimeData().urls()]
            self.to_load_samples.emit(smpls_to_load)
            event.accept()
        else:
            event.ignore()

# class smplTreeWidgetCls(QtWidgets.QTreeWidget):

#     def __init__(self, parent: QtWidgets.QWidget) -> None:
#         super().__init__(parent)

#         # Customized the look.
#         self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
#         self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection) # ExtendedSelection
#         self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectItems) # SelectItems
#         self.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
#         self.setHeaderHidden(True)


if __name__ == '__main__':
    environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
    app = QtWidgets.QApplication(sys.argv)

    window = mainUi_SmplSect(None, None, lambda : [])
    window.show()
    sys.exit(app.exec_())