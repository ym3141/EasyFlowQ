'''
Tests for the main window 
'''

import pytest
from src.EasyFlowQ.window_Main import mainUi
from src.EasyFlowQ.window_Settings import localSettings
from src.EasyFlowQ.backend.efio import sessionSave


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
    # print(artistN)
    assert artistN == 12, 'Artists number on plot is {0}, instead'.format(artistN)


def test_loading_eflq(qtbot):
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
