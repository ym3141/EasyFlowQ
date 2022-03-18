import json
from os import path
from copy import deepcopy

from .gates import polygonGate

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
            mainUiWindow.loadGate(polygonGate(jGate['chnls'], jGate['axScales'], verts=jGate['verts']), gateName=jGate['displayName'])

        
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

    gateSave['verts'] = gateSave['verts'].tolist()

    gateSave['type'] = gateItem.gate.__class__.__name__
    gateSave['displayName'] = gateItem.text()
    gateSave['checkState'] = gateItem.checkState()

    if gateSave['type'] == 'polygonGate':
        del gateSave['prebuiltPath']
    else:
        pass

    return gateSave
            

class smplSave:
    def __init__(self, smplPlotItem) -> None:
        pass