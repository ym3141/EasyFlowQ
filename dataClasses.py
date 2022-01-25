from pathlib import Path

import fcsparser
import numpy as np
import pandas as pd


class fcsSample:
    def __init__(self, fileDir) -> None:
        meta, data = fcsparser.parse(fileDir, reformat_meta=True)
        self.fileDir = fileDir
        self.smplName = self.fileName
        self.fileHeader = meta['__header__']
        self.compensationMat = parseCompStr(meta['$SPILLOVER'])
        self.chnlNames = meta['_channel_names_']
        self._meta = meta
        self.data = data

    @property
    def fileName(self):
        return Path(self.fileDir).stem


def parseCompStr(compStr) -> pd.DataFrame:
    compStr = compStr.split(',')
    compChN = int(compStr[0])

    compDF = pd.DataFrame(np.reshape(compStr[compChN+1:], (compChN, compChN)), columns=compStr[1:1+compChN])

    return compDF

        
