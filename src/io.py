import json
from os import path
from copy import deepcopy

class sessionSave():
    # This is a json serializable class, used for save the session

    def __init__(self, mainUiWindow, saveFileDir) -> None:
        
        self.fileDir = saveFileDir
        baseDir = path.dirname(saveFileDir)

        self.smplSaveList = []
        selectedSmplItems = [mainUiWindow.smplListModel.itemFromIndex(idx) for idx in mainUiWindow.sampleListView.selectedIndexes()]
        for idx in range(mainUiWindow.smplListModel.rowCount()):
            plotItem = mainUiWindow.smplListModel.item(idx)
            self.smplSaveList.append(_convert_smplPlotItem(plotItem, baseDir))

            if plotItem in selectedSmplItems:
                self.smplSaveList[-1]['selected'] = True
            else:
                self.smplSaveList[-1]['selected'] = False



        self.gateSaveList = []
        for idx in range(mainUiWindow.gateListModel.rowCount()):
            gateItem = mainUiWindow.gateListModel.item(idx)
            self.gateSaveList.append(_convert_gateItem(gateItem))

        self.figOptions = dict()
        self.figOptions['curAxScales'] = mainUiWindow.curAxScales
        self.figOptions['curNormOption'] = mainUiWindow.curNormOption
        self.figOptions['curPlotType'] = mainUiWindow.curPlotType
        self.figOptions['curAxScales'] = mainUiWindow.curAxScales

        
    def saveJson(self):
        with open(self.fileDir, 'w+') as f:
            json.dump(self.__dict__, f, sort_keys=True, indent=4)

def _convert_smplPlotItem(item, saveDir):
    smplSave = deepcopy(item.__dict__)

    smplSave['fileDir_rel'] = path.relpath(smplSave['fileDir'], saveDir)
    smplSave['fileDir_abs'] = path.abspath(saveDir)
    smplSave['displayName'] = item.displayName
    smplSave['plotColor'] = item.plotColor.getRgbF()

    del smplSave['chnlNameDict']

    return smplSave

def _convert_gateItem(gateItem):
    gateSave = deepcopy(gateItem.data().__dict__)

    gateSave['verts'] = gateSave['verts'].tolist()

    gateSave['type'] = gateItem.data().__class__.__name__
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