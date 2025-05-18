'''
Tests for the main window 
'''

import pytest
from src.EasyFlowQ.window_Main import mainUi
from src.EasyFlowQ.window_Settings import localSettings
from src.EasyFlowQ.backend.efio import sessionSave
from src.EasyFlowQ.backend.qtModels import pandasTableModel


def test_window_Main(qtbot): 
    mWindow = mainUi(localSettings(testMode=True))
    qtbot.addWidget(mWindow)
    mWindow.show()

    assert mWindow.isVisible()

    # Test loading a fcs sample
    mWindow.loadFcsFile('./demo_sample/01-Well-A1.fcs', mWindow.colorGen.giveColors(1)[0], 'Test Sample', True)
    selectedSmpls = mWindow.smplTreeWidget.selectedItems()
    mWindow.set_saveFlag(False) # Avoid prompting the save dialog

    assert len(selectedSmpls) == 1
    assert selectedSmpls[0].text(0) == 'Test Sample' , 'Sample name wrong'

    # Test of the plot widegt
    artistN = len(mWindow.mpl_canvas.ax.get_children())
    assert artistN == 12, 'Artists number on plot is {0}, instead'.format(artistN)

    mWindow.close()


def test_loading_eflq1_4(qtbot):
    mWindow = mainUi(localSettings(testMode=True))
    qtbot.addWidget(mWindow)
    mWindow.show()

    assert mWindow.isVisible()

    # Test loading the v1.4 save file
    sessionSave.loadSessionSave(mWindow, './demo_sample/SaveTestSimple_v1.4.eflq')
    mWindow.set_saveFlag(False) # Avoid prompting the save dialog

    selectedSmpls = mWindow.smplTreeWidget.selectedItems()
    assert len(selectedSmpls) == 4
    assert selectedSmpls[3].text(0) == '01-Well-C3_er_uy' , 'Sample name wrong, in loading the v1.4 save file'

    # Test of the plot widegt
    artistN = len(mWindow.mpl_canvas.ax.get_children())
    # print(artistN)
    assert artistN == 15, 'Artists number on plot is {0}, instead'.format(artistN)

    mWindow.close()


def test_loading_eflq1_6b(qtbot):
    mWindow = mainUi(localSettings(testMode=True))
    qtbot.addWidget(mWindow)
    mWindow.show()

    assert mWindow.isVisible()

    # Test loading the v1.6b save file
    with pytest.warns(UserWarning, 
                      match='Creating new gate: Logicle parameters are not provided for logicle scaled axis. Using default parameters'):
        sessionSave.loadSessionSave(mWindow, './demo_sample/SaveTestSimple_v1.6b.eflq')
    mWindow.set_saveFlag(False) # Avoid prompting the save dialog

    selectedSmpls = mWindow.smplTreeWidget.selectedItems()
    assert len(selectedSmpls) == 2
    assert selectedSmpls[1].text(0) == '01-Well-C2', 'Sample name wrong, in loading the v1.6b save file'

    # Test of the plot widegt
    artistN = len(mWindow.mpl_canvas.ax.get_children())
    # print(artistN)
    assert artistN == 15, 'Artists number on plot is {0}, instead'.format(artistN)

    # Test of the stat window
    mWindow.actionStats_window.trigger()
    assert mWindow.statWindow.isVisible()

    statDF = mWindow.statWindow.tableView.model()
    assert type(statDF) == pandasTableModel, 'Stat window does not have a pandasTableModel'
    assert statDF.dfData.shape == (2, 9), 'Stat window does not have the correct number of rows and columns'
    
    logicle_in_gate = statDF.dfData['% of parent in: \nlogicleGate (selected)']
    assert list(logicle_in_gate) == ['11.07%', '17.06%'], 'Stat window does not have the correct in gate percentage values'

    mWindow.close()


def test_loading_eflq1_6b(qtbot):
    mWindow = mainUi(localSettings(testMode=True))
    qtbot.addWidget(mWindow)
    mWindow.show()

    assert mWindow.isVisible()

    # Test loading the v1.6b save file
    sessionSave.loadSessionSave(mWindow, './demo_sample/SaveTestSimple_v1.7_micro.eflq')
    mWindow.set_saveFlag(False) # Avoid prompting the save dialog

    selectedSmpls = mWindow.smplTreeWidget.selectedItems()
    assert len(selectedSmpls) == 1
    assert selectedSmpls[0].text(0) == 'micro-cytometry', 'Sample name wrong, in loading the micro-cytometry save file'

    mWindow.figOpsPanel.stackhistRadio.setChecked(True)

    mWindow.close()


