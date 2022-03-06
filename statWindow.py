import sys
from PyQt5 import QtWidgets, QtCore, QtGui, uic
from matplotlib.colors import to_hex
from os import path

import pandas as pd
import numpy as np
from src import pandasTableModel

import re

wUi, wBase = uic.loadUiType('./uiDesignes/StatWindow.ui') # Load the .ui file

class statWindow(wUi, wBase):
    def __init__(self) -> None:

        wBase.__init__(self)
        self.setupUi(self)

        self.move(self.pos() + QtCore.QPoint(100, 60))

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = statWindow()
    window.show()
    sys.exit(app.exec_())