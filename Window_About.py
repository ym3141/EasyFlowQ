from PyQt5 import uic
from os import path

import pandas as pd
import numpy as np


wUi, wBase = uic.loadUiType('./uiDesigns/AboutWindow.ui') # Load the .ui file

class aboutWindow(wUi, wBase):

    def __init__(self) -> None:

        wBase.__init__(self)
        self.setupUi(self)

if __name__ == '__main__':
    pass