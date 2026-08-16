import sys
from os import path

import pandas as pd
from PySide6 import QtWidgets, QtCore

from .backend.qtModels import pandasTableModel
from .backend.utils import sanitizeFileName, illegalFileNameReason
from .uiDesigns import UiLoader


class exportRawDialog(QtWidgets.QDialog):
    # Dialog to pick the destination folder and the file name of each sample,
    # used when more than one sample is exported at once. A single sample is
    # handled by a plain "save as" dialog instead, see window_Main.

    def __init__(self, smplNames, defaultNames, outputType, dir4Save) -> None:
        super().__init__()
        UiLoader().loadUi('ExportRawWindow.ui', self)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.outputType = outputType
        self.saveDir = dir4Save
        self.newNames = []

        self.dirEdit.setText(self.saveDir)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Save).setText('Export')

        tableDF = pd.DataFrame({
            'Sample': list(smplNames),
            'File name (.{0})'.format(outputType): [sanitizeFileName(name) for name in defaultNames],
        })
        editableDF = pd.DataFrame({
            column: [colIdx == 1] * len(tableDF) for colIdx, column in enumerate(tableDF.columns)
        })
        self.nameTableModel = pandasTableModel(tableDF, editableDF=editableDF)
        self.tableView.setModel(self.nameTableModel)

        self.browsePB.clicked.connect(self.handle_Browse)

    def handle_Browse(self):
        newDir = QtWidgets.QFileDialog.getExistingDirectory(self, caption='Export raw data', dir=self.saveDir)
        if newDir:
            self.saveDir = newDir
            self.dirEdit.setText(newDir)

    def accept(self):
        newNames = [str(name).strip() for name in self.nameTableModel.dfData.iloc[:, 1]]

        for name in newNames:
            reason = illegalFileNameReason(name)
            if reason:
                QtWidgets.QMessageBox.warning(
                    self, 'Invalid file name',
                    'Cannot export "{0}", because {1}. Please edit it.'.format(name, reason))
                return

        duplicates = sorted({name for name in newNames if newNames.count(name) > 1})
        if duplicates:
            QtWidgets.QMessageBox.warning(
                self, 'Duplicated file names',
                'The following file names are used more than once, so samples would overwrite '
                'each other: {0}. Please make them unique.'.format(', '.join(duplicates)))
            return

        if not path.isdir(self.saveDir):
            QtWidgets.QMessageBox.warning(
                self, 'Invalid folder', 'Please pick an existing folder to export into.')
            return

        existing = [name for name in newNames
                    if path.exists(path.join(self.saveDir, '{0}.{1}'.format(name, self.outputType)))]
        if existing:
            reply = QtWidgets.QMessageBox.question(
                self, 'Overwrite files?',
                'The following file(s) already exist in this folder and will be overwritten: '
                '{0}. Continue?'.format(', '.join(existing)),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            if reply != QtWidgets.QMessageBox.Yes:
                return

        self.newNames = newNames
        super().accept()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    window = exportRawDialog(['Sample 1', 'Sample 2', 'Sample/3'],
                             ['Sample 1_live', 'Sample 2_live', 'Sample/3_live'],
                             'fcs', path.expanduser('~'))
    window.show()
    sys.exit(app.exec())
