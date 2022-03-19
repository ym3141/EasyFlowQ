import sys
from PyQt5 import QtWidgets, QtCore, QtGui, uic
from matplotlib.colors import to_hex
from os import path

import pandas as pd
import numpy as np
from src.qtModels import pandasTableModel

import re
from xlsxwriter.utility import xl_col_to_name

wUi, wBase = uic.loadUiType('./uiDesigns/settingsWindow.ui') # Load the .ui file

class settingsWindow(wUi, wBase):
    def __init__(self, sessionDir) -> None:

        wBase.__init__(self)
        self.setupUi(self)