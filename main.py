import sys
from PyQt5 import QtWidgets
from mainWindow import mainUi

from os import getpid

class eflqApplication(QtWidgets.QApplication):
    def __init__(self, argv) -> None:
        super().__init__(argv)
        
        self.instanceList = []
        self.pid = getpid()

        firstWindow = mainUi(self.addInstanceToList)
        firstWindow.show()

    def addInstanceToList(self, newInstance):
        self.instanceList.append(newInstance)
        print('{0} of instance is runnign with PID={1}'.format(len(self.instanceList), self.pid))


if __name__ == "__main__":
    app = eflqApplication(sys.argv)

    sys.exit(app.exec_())

