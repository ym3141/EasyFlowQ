import sys
from PyQt5 import QtWidgets, QtCore, QtGui, uic
from matplotlib.colors import to_hex
from os import path

import pandas as pd
import numpy as np
from src.qtModels import pandasTableModel
from src.efio import getSysDefaultDir

import json

wUi, wBase = uic.loadUiType('./uiDesigns/AboutWindow.ui') # Load the .ui file

class aboutWindow(wUi, wBase):

    def __init__(self) -> None:

        wBase.__init__(self)
        self.setupUi(self)

if __name__ == '__main__':
    pass