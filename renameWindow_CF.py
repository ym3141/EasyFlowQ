import sys
from PyQt5 import QtWidgets, QtCore, QtGui, uic

import pandas as pd
from src import pandasTableModel

wUi, wBase = uic.loadUiType('./uiDesignes/RenameWindow_CF.ui') # Load the .ui file

class renameWindow_CF(wUi, wBase):
    def __init__(self, renamingFileDir) -> None:
        wBase.__init__(self)
        self.setupUi(self)
        
        names = pd.read_excel(renamingFileDir, sheet_name=None, header=None)
        renames = names.popitem()[1].fillna('').astype(str)
        while not len(names) == 0:
            nameTable = names.popitem()[1].astype(str)
            print(nameTable)
            newRenames = nameTable.fillna('') + '_' + renames.astype(str)
            newRenames = newRenames.fillna(renames)
            newRenames = newRenames.fillna(nameTable)
            renames = newRenames

        # renames.set_index(['A', 'B', 'C', 'D', 'E', 'F', 'G'])
        renames.columns = list(range(13))[1:]
        renames['col_name'] = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
        renames.set_index('col_name', inplace=True)
        self.renameTableModel = pandasTableModel(renames)
        self.tableView1.setModel(self.renameTableModel)




if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = renameWindow_CF(renamingFileDir='./demoSamples/renamingCF.xlsx')
    window.show()
    sys.exit(app.exec_())