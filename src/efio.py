import json
from os import path
from copy import deepcopy

from .gates import polygonGate, lineGate

from PyQt5.QtCore import QThread, pyqtSignal

from FlowCal.io import FCSData
from typing import List

import pandas as pd

class writeRawFcs(QThread):
    prograssChanged = pyqtSignal(str, float)

    def __init__(self, parent, names, rawDatas: List[FCSData], saveDir: str) -> None:
        super().__init__(parent)

        self.names = names
        self.rawDatas = rawDatas
        self.saveDir = saveDir

    def run(self):

        for idx, name, fcsData in zip(range(len(self.names)), self.names, self.rawDatas):
            df2Write = pd.DataFrame(fcsData, columns=fcsData.channels)

            if not path.exists('{0}.csv'.format(path.join(self.saveDir, name))):
                df2Write.to_csv('{0}.csv'.format(path.join(self.saveDir, name)))

            else:
                alterName = 1
                while path.exists('{0}_{1}.csv'.format(path.join(self.saveDir, name), alterName)):
                    alterName += 1
                
                df2Write.to_csv('{0}_{1}.csv'.format(path.join(self.saveDir, name), alterName))

            self.prograssChanged.emit(name, idx/len(self.names))


class sessionSave():
    # This is a json serializable class, used for save the session

    def __init__(self, mainUiWindow, saveFileDir) -> None:
        
        self.fileDir = saveFileDir
        baseDir = path.dirname(saveFileDir)

        self.smplSaveList = []
        selectedSmplItems = mainUiWindow.smplListWidget.selectedItems()
        for idx in range(mainUiWindow.smplListWidget.count()):
            plotItem = mainUiWindow.smplListWidget.item(idx)
            self.smplSaveList.append(_convert_smplPlotItem(plotItem, baseDir))

            if plotItem in selectedSmplItems:
                self.smplSaveList[-1]['selected'] = True
            else:
                self.smplSaveList[-1]['selected'] = False



        self.gateSaveList = []
        for idx in range(mainUiWindow.gateListWidget.count()):
            gateItem = mainUiWindow.gateListWidget.item(idx)
            self.gateSaveList.append(_convert_gateItem(gateItem))

        self.figOptions = dict()
        self.figOptions['curAxScales'] = mainUiWindow.curAxScales
        self.figOptions['curNormOption'] = mainUiWindow.curNormOption
        self.figOptions['curPlotType'] = mainUiWindow.curPlotType
        self.figOptions['curAxScales'] = mainUiWindow.curAxScales
        self.figOptions['curChnls'] = mainUiWindow.curChnls

        
    def saveJson(self):
        with open(self.fileDir, 'w+') as f:
            json.dump(self.__dict__, f, sort_keys=True, indent=4)

    @classmethod
    def loadSessionSave(cls, mainUiWindow, saveFileDir):
        with open(saveFileDir) as f:
            jDict = json.load(f)
        
        failedFiles = []
        for jSmpl in jDict['smplSaveList']:

            _fileDir_rel = path.join(path.dirname(saveFileDir), jSmpl['fileDir_rel'])

            confirmedDir = None
            if path.exists(_fileDir_rel):
                confirmedDir = _fileDir_rel
            elif path.exists(jSmpl['fileDir_abs']):
                confirmedDir = jSmpl['fileDir_rel']
            else:
                pass
            
            if confirmedDir:
                mainUiWindow.loadFcsFile(confirmedDir, jSmpl['plotColor'], displayName = jSmpl['displayName'], selected=jSmpl['selected'])
            else:
                failedFiles.append(jSmpl)

        for jGate in jDict['gateSaveList']:
            if jGate['type'] == 'polygonGate':
                mainUiWindow.loadGate(polygonGate(jGate['chnls'], jGate['axScales'], verts=jGate['verts']), gateName=jGate['displayName'], checkState=jGate['checkState'])
            elif jGate['type'] == 'lineGate':
                mainUiWindow.loadGate(lineGate(jGate['chnl'], jGate['ends']), gateName=jGate['displayName'], checkState=jGate['checkState'])

        
        mainUiWindow.set_curAxScales(jDict['figOptions']['curAxScales'])
        mainUiWindow.set_curNormOption(jDict['figOptions']['curNormOption'])
        mainUiWindow.set_curPlotType(jDict['figOptions']['curPlotType'])
        mainUiWindow.set_curChnls(jDict['figOptions']['curChnls'])

        # print(failedFiles)


def _convert_smplPlotItem(item, saveDir):
    smplSave = deepcopy(item.__dict__)

    smplSave['fileDir_rel'] = path.relpath(smplSave['fileDir'], saveDir)
    smplSave['fileDir_abs'] = path.abspath(saveDir)
    smplSave['displayName'] = item.displayName
    smplSave['plotColor'] = item.plotColor.getRgbF()

    del smplSave['chnlNameDict']

    return smplSave

def _convert_gateItem(gateItem):
    gateSave = deepcopy(gateItem.gate.__dict__)

    gateSave['type'] = gateItem.gate.__class__.__name__
    gateSave['displayName'] = gateItem.text()
    gateSave['checkState'] = gateItem.checkState()

    if gateSave['type'] == 'polygonGate':
        gateSave['verts'] = gateSave['verts'].tolist()
        del gateSave['prebuiltPath']

    elif gateSave['type'] == 'lineGate':
        pass

    return gateSave


def getSysDefaultDir():
    if path.exists(path.expanduser('~/Desktop')):
        return path.expanduser('~/Desktop')

    elif path.exists(path.expanduser('./Documents')):
        return path.expanduser('~/Documents')
        
    else:
        return path.expanduser('~/')