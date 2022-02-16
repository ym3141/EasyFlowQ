from json import JSONEncoder
from os import path

class sessionSave():
    # This is a json serializable class, used for save the session

    def __init__(self, mainUiWindow, saveFileDir) -> None:
        
        baseDir = path.dirname(saveFileDir)

        self.smplSaveList = []
        selectedSmpls = [mainUiWindow.smplListModel.itemFromIndex(idx) for idx in mainUiWindow.sampleListView.selectedIndexes()]
        for idx in range(mainUiWindow.smplListModel.rowCount()):
            plotItem = mainUiWindow.smplListModel.item(idx)
            self.smplSaveList.append(_convert_smplPlotItem(plotItem, baseDir))

            if plotItem in selectedSmpls:
                self.smplSaveList[-1]['selected'] = True
            else:
                self.smplSaveList[-1]['selected'] = False

        self.gateSaveList = []
        for idx in range(mainUiWindow.gateListModel.rowCount()):
            gateItem = mainUiWindow.gateListModel.item(idx)
            self.gateSaveList.append(_convert_gateItem(gateItem))

        self.plotOptions = dict()

        self.plotOptions['curAxScale'] = mainUiWindow.curAxScales
        self.plotOptions['curChnl'] = mainUiWindow.curChnls
        self.plotOptions['curNormOption'] = mainUiWindow.curNormOption
        self.plotOptions['curPlotType'] = mainUiWindow.curPlotType
        
        pass

def _convert_smplPlotItem(item, saveDir):
    smplSave = item.__dict__

    smplSave['fileDir'] = path.relpath(smplSave['fileDir'], saveDir)
    smplSave['displayName'] = item.displayName
    smplSave['plotColor'] = item.plotColor.getRgbF()

    del smplSave['chnlNameDict']

    return smplSave

def _convert_gateItem(gateItem):
    gateSave = gateItem.data().__dict__

    gateSave['verts'] = gateSave['verts'].tolist()

    gateSave['type'] = str(type(gateItem.data()))
    gateSave['displayName'] = gateItem.text()
    gateSave['checkState'] = gateItem.checkState()

    if gateSave['type'] == "<class 'src.gates.polygonGate'>":
        del gateSave['prebuiltPath']
    else:
        pass

    return gateSave

    






            

class smplSave:
    def __init__(self, smplPlotItem) -> None:
        pass