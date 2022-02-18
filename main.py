import sys
from PyQt5 import QtWidgets
from mainWindow import mainUi

class eflqApplication(QtWidgets.QApplication):
    def __init__(self, argv) -> None:
        super().__init__(argv)
        
        self.instanceList = []

        firstWindow = mainUi(self.addInstanceToList)
        firstWindow.show()

    def addInstanceToList(self, newInstance):
        self.instanceList.append(newInstance)


if __name__ == "__main__":
    app = eflqApplication(sys.argv)

    sys.exit(app.exec_())

