'''
Tests for the dialog that renames samples before exporting raw data
'''

import pytest
from src.EasyFlowQ.dialog_ExportRaw import exportRawDialog
from src.EasyFlowQ.backend.utils import sanitizeFileName, illegalFileNameReason

from PySide6 import QtCore, QtWidgets

smplNames = ['Well A1', 'Well B1']
defaultNames = ['Well A1_live', 'Well B1_live']


@pytest.fixture
def mutedWarnings(monkeypatch):
    # Record the warnings the dialog raises, instead of blocking on them
    warnings = []
    monkeypatch.setattr(QtWidgets.QMessageBox, 'warning',
                        lambda parent, title, text, *args, **kwargs: warnings.append(title))
    return warnings


def setName(dialog, row, name):
    dialog.nameTableModel.setData(dialog.nameTableModel.index(row, 1), name, QtCore.Qt.EditRole)


def test_sanitizeFileName():
    assert sanitizeFileName('Well A1') == 'Well A1'
    assert sanitizeFileName('Well/A1') == 'Well_A1'
    assert sanitizeFileName('Well:A1?') == 'Well_A1_'
    assert sanitizeFileName('trailing. ') == 'trailing'
    assert sanitizeFileName('   ') == 'sample', 'A name that is empty after cleaning needs a fallback'

    assert illegalFileNameReason('Well A1') is None
    assert illegalFileNameReason('') is not None
    assert illegalFileNameReason('Well/A1') is not None


def test_exportRawDialog_prefill(qtbot, tmp_path):
    # The default names are what the caller passes, cleaned up if needed
    dialog = exportRawDialog(smplNames, ['Well A1_live', 'Well/B1_live'], 'fcs', str(tmp_path))
    qtbot.addWidget(dialog)

    assert list(dialog.nameTableModel.dfData.iloc[:, 0]) == smplNames
    assert list(dialog.nameTableModel.dfData.iloc[:, 1]) == ['Well A1_live', 'Well_B1_live']
    assert dialog.dirEdit.text() == str(tmp_path)


def test_exportRawDialog_accept(qtbot, tmp_path):
    dialog = exportRawDialog(smplNames, defaultNames, 'fcs', str(tmp_path))
    qtbot.addWidget(dialog)

    setName(dialog, 0, ' gated_A1 ')
    dialog.accept()

    assert dialog.result() == QtWidgets.QDialog.Accepted
    assert dialog.newNames == ['gated_A1', 'Well B1_live'], 'Edited names should be picked up and stripped'
    assert dialog.saveDir == str(tmp_path)


@pytest.mark.parametrize('badName', ['', '   ', 'with/slash', 'trailingDot.'])
def test_exportRawDialog_rejectsBadNames(qtbot, tmp_path, mutedWarnings, badName):
    dialog = exportRawDialog(smplNames, defaultNames, 'fcs', str(tmp_path))
    qtbot.addWidget(dialog)

    setName(dialog, 0, badName)
    dialog.accept()

    assert dialog.result() != QtWidgets.QDialog.Accepted
    assert dialog.newNames == [], 'An invalid file name should not be exported'
    assert mutedWarnings == ['Invalid file name']


def test_exportRawDialog_rejectsDuplicates(qtbot, tmp_path, mutedWarnings):
    dialog = exportRawDialog(smplNames, defaultNames, 'fcs', str(tmp_path))
    qtbot.addWidget(dialog)

    setName(dialog, 1, defaultNames[0])
    dialog.accept()

    assert dialog.newNames == [], 'Samples should not be allowed to overwrite each other'
    assert mutedWarnings == ['Duplicated file names']


def test_exportRawDialog_confirmsOverwrite(qtbot, tmp_path, monkeypatch):
    (tmp_path / '{0}.fcs'.format(defaultNames[0])).write_text('existing file')

    answers = []
    monkeypatch.setattr(QtWidgets.QMessageBox, 'question',
                        lambda *args, **kwargs: answers.pop(0))

    dialog = exportRawDialog(smplNames, defaultNames, 'fcs', str(tmp_path))
    qtbot.addWidget(dialog)

    answers.append(QtWidgets.QMessageBox.No)
    dialog.accept()
    assert dialog.newNames == [], 'Declining the overwrite should keep the dialog open'

    answers.append(QtWidgets.QMessageBox.Yes)
    dialog.accept()
    assert dialog.newNames == defaultNames, 'Confirming the overwrite should export'
