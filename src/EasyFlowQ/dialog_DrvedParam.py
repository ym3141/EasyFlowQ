import sys
from PySide6 import QtWidgets, QtCore, QtGui, QtUiTools
from .backend.qtModels import chnlModel
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


class drvedParamDialog(QtWidgets.QDialog):
    addParamConfirmed = QtCore.Signal(object)

    def __init__(self, chnlListModel) -> None:
        super().__init__()
        UiLoader().loadUi('DrvedParamWindow.ui', self)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.chnlListModel = chnlListModel
        for idx, chnlCombo in enumerate([self.chnl1Combo, self.chnl2Combo, self.chnl3Combo, self.chnl4Combo]):
            chnlCombo.setModel(self.chnlListModel)
            if len(chnlListModel.keyList) > idx:
                chnlCombo.setCurrentIndex(idx)
            else:
                chnlCombo.setCurrentIndex(-1)

        self.saveButton = self.buttonBox.button(QtWidgets.QDialogButtonBox.Save)
        self.saveButton.setEnabled(False)
        self.parsedFormula = None
        self.newParamName = None
            
        # self.parsePB.clicked.connect(self.handle_parseFormula)
        self.formulaEdit.textChanged.connect(self.handle_parseFormula)
        for comboBox in [self.chnl1Combo, self.chnl2Combo, self.chnl3Combo, self.chnl4Combo]:
            comboBox.currentIndexChanged.connect(self.handle_parseFormula)

    def handle_parseFormula(self):

        self.parseOutputEdit.clear()
        self.saveButton.setEnabled(False)

        # compiling a list of symbols and channel keys assigned to them
        fl1, fl2, fl3, fl4 = symbols('fl1, fl2, fl3, fl4')
        chnlKeys = []
        for chnlCombo in [self.chnl1Combo, self.chnl2Combo, self.chnl3Combo, self.chnl4Combo]:
            if chnlCombo.currentIndex() == -1:
                chnlKeys.append(None)
            else:
                chnlKeys.append(self.chnlListModel.keyList[chnlCombo.currentIndex()])
        
        assignedSybs = []
        assignedChnlKeys = []
        for syb, key in zip([fl1, fl2, fl3, fl4], chnlKeys):
            if key:
                assignedSybs.append(syb)
                assignedChnlKeys.append(key)
        sybs2chnlKeys = dict(zip(assignedSybs, symbols(assignedChnlKeys)))

        # parsing the formula
        formulaStr = self.formulaEdit.toPlainText()
        try:
            formulaExpr = parse_expr(formulaStr)
            self._outputAppendRichText('Formula parsed successfully!', succesQFmt)

        except Exception as e:
            self._outputAppendRichText('Formula parsing failed with error:', errorQFmt)
            self._outputAppendRichText(str(e), regQFmt)
            return

        # checking if the symbols in the formula are legal and assigned
        for syb in formulaExpr.free_symbols:
            if syb not in [fl1, fl2, fl3, fl4]:
                self._outputAppendRichText(f'Symbol check error: {syb} not a legal symbol.', errorQFmt)
                return
            elif syb not in assignedSybs:
                self._outputAppendRichText(f'Symbol check error: {syb} is legal but not assigned.', errorQFmt)
                return
            
        self._outputAppendRichText('Symbol check passed!', succesQFmt)

        self.parsedFormula = formulaExpr.subs(sybs2chnlKeys)
        
        self._outputAppendRichText('Formula for new parameter:', regQFmt)
        self._outputAppendRichText(str(self.parsedFormula), regQFmt)
        self.parseOutputEdit.setAlignment(QtGui.Qt.AlignCenter)

        self.saveButton.setEnabled(True)
    
    def accept(self):
        if self.nameEdit.text() == '':
            QtWidgets.QMessageBox.warning(self, 'Empty name', 'Please provide a name for the new parameter.')
            self.nameEdit.setFocus()
            return
        else:
            self.newParamName = self.nameEdit.text()

        super().accept()


    def _outputAppendRichText(self, text, charFmt):
        self.parseOutputEdit.setCurrentCharFormat(charFmt)
        self.parseOutputEdit.append(text)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    test_chnlModel = chnlModel()
    for testChnl in ['FL0:Test', 'FL1:Test2', 'FL2:Test3']:
        test_chnlModel.addChnl(testChnl, testChnl)
    window = drvedParamDialog(test_chnlModel)
    window.formulaEdit.setPlainText('(fl1 + fl2) / fl3')
    window.show()
    sys.exit(app.exec())