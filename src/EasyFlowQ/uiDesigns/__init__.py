from PySide6 import QtUiTools
from os import path, getcwd

__location__ = path.realpath(path.join(getcwd(), path.dirname(__file__)))

# Code from https://stackoverflow.com/a/27610822/18041947
class UiLoader(QtUiTools.QUiLoader):
    _baseinstance = None

    def createWidget(self, classname, parent=None, name=''):
        if parent is None and self._baseinstance is not None:
            widget = self._baseinstance
        else:
            widget = super().createWidget(classname, parent, name)
            if self._baseinstance is not None:
                setattr(self._baseinstance, name, widget)
        return widget

    def loadUi(self, uiFileName, baseinstance=None):
        self._baseinstance = baseinstance
        uiFilePath = path.join(__location__, uiFileName)
        widget = self.load(uiFilePath)
        return widget