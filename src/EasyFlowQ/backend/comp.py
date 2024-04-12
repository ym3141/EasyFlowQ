from PyQt5 import QtGui
from PyQt5.QtCore import Qt
import numpy as np
import pandas as pd
import json

from io import StringIO
import itertools

from .qtModels import pandasTableModel

class autoFluoTbModel(pandasTableModel):

    def __init__(self, chnlList, chnlNameList, editable=True):

        self.chnlList = chnlList
        self.chnlNameList = chnlNameList
        if len(chnlList) != len(chnlNameList):
            raise ValueError('the chnlList and chnlFullname don\'t have the same length')

        self.DFIndices = ['{0}: {1}'.format(key, name) for key, name in zip(self.chnlList, self.chnlNameList)]

        if editable:
            editableDF = pd.DataFrame(np.ones((len(chnlList), 1), dtype=bool), index=self.DFIndices, columns=['AutoFluor'])
        else:
            editableDF = pd.DataFrame(np.zeros((len(chnlList), 1), dtype=bool), index=self.DFIndices, columns=['AutoFluor'])
        
        autoFluoDF = pd.DataFrame(index=self.DFIndices, columns=['AutoFluor']).infer_objects(copy=False).fillna(0)

        super().__init__(autoFluoDF, editableDF=editableDF, validator=QtGui.QDoubleValidator())

    def data(self, index, role):
        if role == Qt.DisplayRole:
            number = float(super().data(index, role))
            return '{0:.5g}'.format(number)
        return super().data(index, role)
    
    def isZeros(self) -> bool:
        return np.allclose(0, self.dfData.to_numpy(dtype=np.double, copy=True))

    # load a DF into the model. The matching is purely based on chnlKey (e.g. 'FL1-A'), and will ignore the name.
    def loadDF(self, inputDF: pd.DataFrame, forceOverwrite=True):
        commonChnls = []
        missedChnls = []
        overwriteFlag = False

        inputChnlFullNames = inputDF.index
        inputChnlKeys = [full.split(':', 1)[0] for full in inputChnlFullNames]
        inputChnlDict = dict(zip(inputChnlKeys, inputChnlFullNames))


        for chnlKey in inputChnlKeys:
            if chnlKey in self.chnlList:
                commonChnls.append(chnlKey)
            else:
                missedChnls.append(chnlKey)

        for chnl in commonChnls:
            idx = self.chnlList.index(chnl)
            if not np.isclose(self.dfData.loc[self.DFIndices[idx], 'AutoFluor'], 0):
                overwriteFlag = True
                if not forceOverwrite:
                    return (overwriteFlag, missedChnls)
            
            self.setData(self.index(idx, 0), inputDF.loc[inputChnlDict[chnl]].iloc[0])
                 
        return (overwriteFlag, missedChnls)
    
    # this function package the df to json
    def to_json(self):
        if self.isZeros():
            return None
        else:
            return self.dfData.to_json(orient='split')

    # this function process JSON 
    def load_json(self, jString: str):
        if jString is None:
            return False, []
        
        with StringIO(jString) as jStringIO:
            spillMatDF = pd.read_json(jStringIO, orient='split')
            overwriteFlag, missedChnls = self.loadDF(spillMatDF)

        return overwriteFlag, missedChnls


# Table model based class for compensention matrix
class spillMatTbModel(pandasTableModel):

    # this create an empty mat. To load a mat, create one using the below __init__, and then use loadMatDF
    def __init__(self, chnlList, editable=True):

        self.chnlList = chnlList

        if editable:
            editableDF = pd.DataFrame(np.logical_not(np.eye(len(chnlList), dtype=bool)), index=chnlList, columns=chnlList)
        else:
            editableDF = pd.DataFrame(np.zeros((len(chnlList), len(chnlList)), dtype=bool), index=chnlList, columns=chnlList)
        
        spillmatDF = pd.DataFrame(np.eye(len(chnlList)) * 100, index=chnlList, columns=chnlList)

        super().__init__(spillmatDF, backgroundDF=getGreyDiagDF(len(chnlList)), editableDF=editableDF, validator=QtGui.QDoubleValidator(bottom=0.))

    def data(self, index, role):
        if role == Qt.DisplayRole:
            number = float(super().data(index, role))
            return '{0:.4g}'.format(number)
        return super().data(index, role)
    
    def isIdentity(self) -> bool:
        identity = np.eye(len(self.chnlList)) * 100
        flag = np.allclose(identity, self.dfData.to_numpy(dtype=np.double, copy=True), atol=1e-6, rtol=0)
        return flag

    # the effeciency here can be improved!
    def loadMatDF(self, spillMatDF: pd.DataFrame, forceOverwrite=True):
        commonChnls = []
        missedChnls = []
        overwriteFlag = False

        loadingChnls = spillMatDF.columns

        for chnl in loadingChnls:
            if chnl in self.chnlList:
                commonChnls.append(chnl)
            else:
                missedChnls.append(chnl)

        for chnlFrom, chnlTo in itertools.permutations(commonChnls, 2):
            if not chnlFrom == chnlTo:
                if not np.isclose(self.dfData.loc[chnlFrom, chnlTo], 0):
                    overwriteFlag = True
                    if not forceOverwrite:
                        return (overwriteFlag, missedChnls)
                
                if np.isclose(spillMatDF.loc[chnlFrom, chnlTo], 0):
                    continue

                idx = self.chnlList.index(chnlFrom)
                jdx = self.chnlList.index(chnlTo)
                self.setData(self.index(idx, jdx), spillMatDF.loc[chnlFrom, chnlTo])
                 
        return (overwriteFlag, missedChnls)

    def dataFromChnlKeys(self, rowChnlKey, colChnlKey):
        idx = self.chnlList.index(rowChnlKey)
        jdx = self.chnlList.index(colChnlKey)

        return self.dfData.iloc(idx, jdx)

    # this function package the df to json
    def to_json(self):
        if self.isIdentity():
            return None
        else:
            return self.dfData.to_json(orient='split')

    # this function process JSON 
    def load_json(self, jString: str):
        if jString is None: # Represent an empty matrix
            return False, []
        
        with StringIO(jString) as jStringIO:
            spillMatDF = pd.read_json(jStringIO, orient='split') 
            overwriteFlag, missedChnls = self.loadMatDF(spillMatDF)

        return overwriteFlag, missedChnls

def getGreyDiagDF(length):
    greyDiagDF = pd.DataFrame(index=range(length), columns=range(length)).fillna('#ffffff')
    if length > 0:
        np.fill_diagonal(greyDiagDF.values, ['#b0b0b0'])
    return greyDiagDF