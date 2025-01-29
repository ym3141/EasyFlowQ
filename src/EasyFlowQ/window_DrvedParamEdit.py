import sys
from PySide6 import QtWidgets, QtCore, QtGui, QtUiTools
from .backend.qtModels import chnlModel
from .backend.dataIO import drvedParam
from .uiDesigns import UiLoader

from sympy.parsing.sympy_parser import parse_expr
from sympy import *

regQFmt = QtGui.QTextCharFormat()

errorQFmt = QtGui.QTextCharFormat()
errorQFmt.setBackground(QtGui.QColor('darkRed'))
errorQFmt.setForeground(QtGui.QColor('white'))

succesQFmt = QtGui.QTextCharFormat()
succesQFmt.setBackground(QtGui.QColor('darkGreen'))
succesQFmt.setForeground(QtGui.QColor('white'))


class drvedParamEditWindow(QtWidgets.QWidget):
    newParamRequested = QtCore.Signal()

    def __init__(self, paramListModel) -> None:
        super().__init__()
        UiLoader().loadUi('DrvedParamEditWindow.ui', self)

        self.paramListView.setModel(paramListModel)
        self.paramListView.selectionModel().selectionChanged.connect(self.handle_ParamSelectionChanged)

        self.newPB.clicked.connect(self.handle_NewParam)
        self.deletePB.clicked.connect(self.handle_DeleteParam)

    def handle_NewParam(self):
        self.newParamRequested.emit()

    def handle_DeleteParam(self):
        pass
    
    def handle_ParamSelectionChanged(self):
        selectedIndexes = self.paramListView.selectedIndexes()
        if len(selectedIndexes) == 0:
            self.paramDetailEdit.clear()
            return
        
        selectedIdx = selectedIndexes[0]
        selectedParam = self.paramListView.model().itemFromIndex(selectedIdx)
        self.paramDetailEdit.clear()
        self._outputAppendRichText(f'Name: <b>{selectedParam.name}<\\b>', regQFmt)
        self._outputAppendRichText(f'', regQFmt)
        self._outputAppendRichText(f'Channels involved: ', regQFmt)
        for chnlKey in selectedParam.chnlKeys:
            self.paramDetailEdit.insertHtml(f'<b style="color:white;background-color:green;">{chnlKey}</b>, ')
        self._outputAppendRichText('', regQFmt)
        self._outputAppendRichText(f'Parameter formula: <b>{selectedParam.formula}<\\b>', regQFmt)


    def _outputAppendRichText(self, text, charFmt):
        self.paramDetailEdit.setCurrentCharFormat(charFmt)
        self.paramDetailEdit.append(text)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    test_ViewModel = QtGui.QStandardItemModel()
    x, y = symbols(['fl1', 'fl2'])
    test_ViewModel.appendRow(drvedParam('Test', x + y))
    window = drvedParamEditWindow(test_ViewModel)
    window.show()
    sys.exit(app.exec())