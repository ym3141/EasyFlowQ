import pytest

from os import path
from src.EasyFlowQ.window_Settings import localSettings, settingsWindow

def test_localSettings():
    testSettings = localSettings(testMode=True)
    assert testSettings['default dir'] == path.abspath('./demoSamples')

    sysSettings = localSettings()
    assert type(sysSettings['default dir']) is str
    assert type(sysSettings['dot N in perf mode']) is int
    
def test_settingsWindow(qtbot):
    sWindow = settingsWindow()
    qtbot.addWidget(sWindow)
    sWindow.show()

    assert sWindow.isVisible()

    sWindow.defaultPB.click()
    assert int(sWindow.dotNEdit.text()) == 20000
    assert float(sWindow.dpiSpinBox.value()) == 1.25
        