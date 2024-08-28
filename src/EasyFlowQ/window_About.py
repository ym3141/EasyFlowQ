from PySide6 import QtWidgets
from os import path, getcwd
from .uiDesigns import UiLoader


class aboutWindow(QtWidgets.QWidget):
    def __init__(self) -> None:

        super().__init__()
        UiLoader().loadUi('AboutWindow.ui', self)

if __name__ == '__main__':
    pass
