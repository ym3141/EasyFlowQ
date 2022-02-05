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
        self.data = data

        self._meta = meta

        # processing channel names. 
        if '$PnS' in meta['_channels_']:
            if tuple(meta['_channels_']['$PnS']) == meta['_channel_names_']:
                # the normal naming model, in which $PnS should be unique in the fcs
                # change data label to $PnN anyway
                mapper = dict(zip(meta['_channels_']['$PnS'], meta['_channels_']['$PnN']))
                self.data.rename(columns=mapper, inplace=True)
                
            elif tuple(meta['_channels_']['$PnN']) == meta['_channel_names_']:
                # the alternative model, in which $PnS is not unique in the fcs, $PnN is used as naming instead
                # do nothing, this is the safer mode
                pass
            
            # build the dict for $PnN -> $PnS
            self.chnlNameDict = dict(zip(meta['_channels_']['$PnN'], meta['_channels_']['$PnS']))

        else:
            self.chnlNameDict = dict(zip(meta['_channels_']['$PnN'], meta['_channels_']['$PnN']))
        
        # see if there is built-in compensation matrix
        try:
            self.compensationMat = parseCompStr(meta['$SPILLOVER'])
        except KeyError:
            self.compensationMat = None

    @property
    def fileName(self):
        return Path(self.fileDir).stem


def parseCompStr(compStr) -> pd.DataFrame:
    compStr = compStr.split(',')
    compChN = int(compStr[0])

    compDF = pd.DataFrame(np.reshape(compStr[compChN+1:], (compChN, compChN)), columns=compStr[1:1+compChN])

    return compDF

        
