from PySide6 import QtUiTools
from os import path, getcwd

__location__ = path.realpath(path.join(getcwd(), path.dirname(__file__)))
wUi, wBase = QtUiTools.loadUiType(path.join(__location__, 'uiDesigns/AboutWindow.ui')) # Load the .ui file

class aboutWindow(wUi, wBase):
    def __init__(self) -> None:

        wBase.__init__(self)
        self.setupUi(self)

if __name__ == '__main__':
    pass