import json
import traceback
from os import path
from copy import deepcopy

from .gates import polygonGate, lineGate, quadrantGate, quadrant, split
from .qtModels import quadWidgetItem, splitWidgetItem

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QMessageBox

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

        self.save_ver = mainUiWindow.version
        
        self.fileDir = saveFileDir
        baseDir = path.dirname(saveFileDir)

        self.smplSaveList = []
        selectedSmplItems = mainUiWindow.smplTreeWidget.selectedItems()
        for idx in range(mainUiWindow.smplTreeWidget.topLevelItemCount()):
            plotItem = mainUiWindow.smplTreeWidget.topLevelItem(idx)
            self.smplSaveList.append(_convert_smplPlotItem(plotItem, baseDir))

            if plotItem in selectedSmplItems:
                self.smplSaveList[-1]['selected'] = True
            else:
                self.smplSaveList[-1]['selected'] = False


        self.gateSaveList = []
        for idx in range(mainUiWindow.gateListWidget.count()):
            gateItem = mainUiWindow.gateListWidget.item(idx)
            self.gateSaveList.append(_convert_gateItem(gateItem))

        self.qsSaveList = []
        for idx in range(mainUiWindow.qsListWidget.count()):
            qsItem = mainUiWindow.qsListWidget.item(idx)
            self.qsSaveList.append(_convert_qsItem(qsItem))


        self.figOptions = dict()
        self.figOptions['curPlotType'], self.figOptions['curAxScales'], self.figOptions['curAxLims'], self.figOptions['curNormOption'], self.figOptions['curSmooth'] = mainUiWindow.figOpsPanel.curFigOptions
        self.figOptions['curChnls'] = mainUiWindow.curChnls

        self.curComp = mainUiWindow.compWindow.to_json()
        self.applyComp = mainUiWindow.compApplyCheck.isChecked()
        
    def saveJson(self):
        with open(self.fileDir, 'w+') as f:
            json.dump(self.__dict__, f, sort_keys=True, indent=4)

    @classmethod
    def loadSessionSave(cls, mainUiWindow, saveFileDir):
        
        failedFiles = []
        gateLoadFlag = False
        figSettingFlag = False
        compFlag = False

        with open(saveFileDir) as f:
            jDict = json.load(f)
        
        # for really early version, that don't have a save_ver
        if not 'save_ver' in jDict:
            save_ver = 0.1
        else:
            save_ver = jDict['save_ver']

        # load the FCS files
        
        for jSmpl in jDict.get('smplSaveList', []):

            try:
                _fileDir_rel = path.join(path.dirname(saveFileDir), jSmpl['fileDir_rel'])
                confirmedDir = None
                if path.exists(_fileDir_rel):
                    confirmedDir = _fileDir_rel
                elif path.exists(jSmpl['fileDir_abs']):
                    confirmedDir = jSmpl['fileDir_abs']
                elif path.exists(jSmpl['fileDir']):
                    confirmedDir = jSmpl['fileDir']
            
                if confirmedDir:
                    try:
                        mainUiWindow.loadFcsFile(confirmedDir, jSmpl['plotColor'], displayName = jSmpl['displayName'], selected=jSmpl['selected'])
                    except Exception as e:
                        failedFiles.append(path.basename(jSmpl['fileDir_rel']))
                        traceback.print_tb(e.__traceback__)
                else:
                    failedFiles.append(path.basename(jSmpl['fileDir_rel']))

            except KeyError as e:
                failedFiles.append('Unknown FCS')
                traceback.print_tb(e.__traceback__)

        for jGate in jDict.get('gateSaveList', []):
            try:
                if jGate['type'] == 'polygonGate':
                    mainUiWindow.loadGate(polygonGate(jGate['chnls'], jGate['axScales'], verts=jGate['verts']), gateName=jGate['displayName'], checkState=jGate['checkState'])
                elif jGate['type'] == 'lineGate':
                    mainUiWindow.loadGate(lineGate(jGate['chnl'], jGate['ends']), gateName=jGate['displayName'], checkState=jGate['checkState'])
                elif jGate['type'] == 'quadrantGate':
                    mainUiWindow.loadGate(quadrantGate(jGate['chnls'], jGate['center'], jGate['corner']), gateName=jGate['displayName'], checkState=jGate['checkState'])
            
            except Exception as e:
                gateLoadFlag = True
                traceback.print_tb(e.__traceback__)

        try: 
            mainUiWindow.figOpsPanel.set_curAxScales(jDict['figOptions']['curAxScales'])
            mainUiWindow.figOpsPanel.set_curNormOption(jDict['figOptions']['curNormOption'])
            mainUiWindow.figOpsPanel.set_curPlotType(jDict['figOptions']['curPlotType'])

            mainUiWindow.set_curChnls(jDict['figOptions']['curChnls'])
        except Exception as e:
            figSettingFlag = True
            traceback.print_tb(e.__traceback__)


        if save_ver >= 1.0:
            try:
                mainUiWindow.figOpsPanel.set_curSmooth(jDict['figOptions']['curSmooth'])
            except Exception as e:
                figSettingFlag = True
                traceback.print_tb(e.__traceback__)

            for jQS in jDict.get('qsSaveList', []):
                try: 
                    if jQS['type'] == 'quadrant':
                        mainUiWindow.loadQuadrant(quadrant(jQS['chnls'], jQS['center']), quadName=jQS['displayName'])
                    elif jQS['type'] == 'split':
                        mainUiWindow.loadSplit(split(jQS['chnl'], jQS['splitValue']), splitName=jQS['displayName'])
                except Exception as e:
                    gateLoadFlag = True
                    traceback.print_tb(e.__traceback__)

        if save_ver >= 1.2:
            jString = jDict.get('curComp', None)

            try:
                if not (jString is None):
                    mainUiWindow.compWindow.load_json(jString)
                mainUiWindow.compApplyCheck.setChecked(jDict.get('applyComp', False))
            except Exception as e:
                compFlag = True
                traceback.print_tb(e.__traceback__)
            
        # report the potential errors:
        if any([len(failedFiles), gateLoadFlag, figSettingFlag, compFlag]):
            errorMsg = 'The following things are not loaded succesfully:\n'
            if len(failedFiles) > 0:
                errorMsg += 'FCS file: ' + ' ;'.join(failedFiles) + '\n'
            if gateLoadFlag:
                errorMsg += 'We may failed to load some gates.\n'
            if figSettingFlag:
                errorMsg += 'We may failed to load some figure settings.\n'
            if compFlag:
                errorMsg += 'We may failed to load compensation settings or data.\n'
            errorMsg += 'We have loaded everything else, but please double check the data and settings.'

            QMessageBox.warning(mainUiWindow, 'Something went wrong.', errorMsg)
        


def _convert_smplPlotItem(item, saveDir):
    smplSave = deepcopy(item.__dict__)

    smplSave['fileDir_rel'] = path.relpath(smplSave['fileDir'], saveDir)
    smplSave['fileDir_abs'] = path.abspath(smplSave['fileDir'])
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

    elif gateSave['type'] == 'lineGate' or gateSave['type'] == 'quadrantGate':
        pass

    return gateSave

def _convert_qsItem(qsItem):
    if isinstance(qsItem, quadWidgetItem):
        qsSave = deepcopy(qsItem.quad.__dict__)
        qsSave['type'] = 'quadrant'
    elif isinstance(qsItem, splitWidgetItem):
        qsSave = deepcopy(qsItem.split.__dict__)
        qsSave['type'] = 'split'

    qsSave['displayName'] = qsItem.text()

    return qsSave


def getSysDefaultDir():
    if path.exists(path.expanduser('~/Desktop')):
        return path.expanduser('~/Desktop')

    elif path.exists(path.expanduser('./Documents')):
        return path.expanduser('~/Documents')
        
    else:
        return path.expanduser('~/')