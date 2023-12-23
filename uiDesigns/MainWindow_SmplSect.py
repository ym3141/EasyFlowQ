'''
This file is intented to seperate some codes from the window_Main.py file.
Currently it will only host codes dealing with the UI aspect of the sample section,
as well as codes that are "self-contained". Core codes about samples, like loading
fcs files, creating subpops, are still handled by the main_Window.py, as they're 
too integrated to the other part of the program.
'''

import sys
from os import environ

from PyQt5 import QtWidgets, QtCore, QtGui, uic
from PyQt5.QtWidgets import QWidget

smplSectUi, smplSectBase = uic.loadUiType('./uiDesigns/MainWindow_SmplSect.ui') # Load the .ui file

class mainUi_SmplSect(smplSectBase, smplSectUi):
    to_handle_One = QtCore.pyqtSignal()
    holdFigure = QtCore.pyqtSignal(bool)

    def __init__(self, parent, colorGen):

        smplSectBase.__init__(self, parent)
        self.setupUi(self)

        self.smplTreeWidget = smplTreeWidgetCls(self)
        self.layout().addWidget(self.smplTreeWidget)

        self.colorGen = colorGen

        # add actions to context manu
        self.smplTreeWidget.addActions([self.actionAdd_subpops_Current_gating])
        self.smplTreeWidget.addActions([self.actionDelete_sample])

        self.smplTreeWidget.itemChanged.connect(self.to_handle_One)
        self.smplTreeWidget.itemSelectionChanged.connect(self.to_handle_One)

        self.colorPB.clicked.connect(self.handle_ChangeSmplColor)
        self.expandAllPB.clicked.connect(lambda : self.handle_ExpandCollapseSmplTree(expand=True))
        self.collapseAllPB.clicked.connect(lambda : self.handle_ExpandCollapseSmplTree(expand=False))
        self.selectRootsPB.clicked.connect(self.handle_SelectAllRoots)
        self.searchSmplEdit.returnPressed.connect(self.handle_SearchSmplTree)


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


class smplTreeWidgetCls(QtWidgets.QTreeWidget):

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        # Customized the look.
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        self.setSelectionMode(3) # ExtendedSelection
        self.setSelectionBehavior(0) # SelectItems
        self.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.setHeaderHidden(True)


if __name__ == '__main__':
    environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
    app = QtWidgets.QApplication(sys.argv)

    window = mainUi_SmplSect(None, None)
    window.show()
    sys.exit(app.exec_())