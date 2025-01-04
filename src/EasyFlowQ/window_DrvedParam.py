import sys
from PySide6 import QtWidgets, QtCore, QtGui, QtUiTools
from .backend.qtModels import chnlModel
from .uiDesigns import UiLoader

from sympy.parsing.sympy_parser import parse_expr
from sympy import *

class drvedParamWindow(QtWidgets.QDialog):
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

        self.parsedFormulaFunc = None
        self.chnlKeys_as_param = []
            
        self.parsePB.clicked.connect(self.handle_parseFormula)

    def handle_parseFormula(self):
        
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

        # parsing the formula
        formulaStr = self.formulaEdit.toPlainText()
        try:
            formulaExpr = parse_expr(formulaStr)
        except Exception as e:
            print(e)
            return

        # checking if the symbols in the formula are legal and assigned
        for syb in formulaExpr.free_symbols:
            if syb not in [fl1, fl2, fl3, fl4]:
                print(f'Error: {syb} not a legal symbol')
                return
            elif syb not in assignedSybs:
                print(f'Error: {syb} is legal but not assigned')
                return
        print('Symbol check all good')

        self.parsedFormulaFunc = lambdify(assignedSybs, formulaExpr)
        self.chnlKeys_as_param = assignedChnlKeys
        pass

            
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    test_chnlModel = chnlModel()
    for testChnl in ['FL0:Test', 'FL1:Test2', 'FL2:Test3']:
        test_chnlModel.addChnl(testChnl, testChnl)
    window = drvedParamWindow(test_chnlModel)
    window.formulaEdit.setPlainText('(fl1 + fl2) / fl3')
    window.show()
    sys.exit(app.exec())