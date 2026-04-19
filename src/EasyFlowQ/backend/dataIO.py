from ..FlowCal.io import FCSData
from sympy import Expr, lambdify, exp
import numpy as np

from PySide6.QtGui import QStandardItem

class FCSData_ef(FCSData):
    """
    This is an subclass for FCSData from the FlowCal package.
    Added additional code handeling merging and derived parameters 
    """

    def __new__(cls, infile):
        fcsData_obj = super().__new__(cls, infile)

        fcsData_obj._drvedParams = []
        obj = fcsData_obj.view(cls)

        return obj


    def __array_finalize__(self, obj):
        if obj is None: return
        self._drvedParams = getattr(obj, '_drvedParams', [])
        self.dataSecHash = None
        super().__array_finalize__(obj)

    def __hash__(self):
        if self.dataSecHash is None:
            self.dataSecHash = hash(self.tobytes())
        return self.dataSecHash
    
    def __eq__(self, other):
        if not isinstance(other, FCSData_ef):
            return False
        if self.dataSecHash is None:
            self.dataSecHash = hash(self.tobytes())

        return self.dataSecHash == other.dataSecHash
        
    def appendNewParam(self, newDrvedParam):
        self._drvedParams.append(newDrvedParam)

        chnlDataTuple = ()
        for key in newDrvedParam.chnlKeys:
            chnlDataTuple += (self[:, key],)

        newData = newDrvedParam.formulaFunc(*chnlDataTuple)
        newData = newData.reshape((newData.shape[0], 1))
        appendedData = np.append(self, newData, axis=1)

        newFCSData = FCSData_ef.fromArray(self, appendedData)
        newFCSData._infile = self._infile
        newFCSData._channels += (newDrvedParam.name,)
        newFCSData._channel_labels += ('Derived Parameter',)
        newFCSData._amplification_type += ('N/A',)
        newFCSData._detector_voltage += ('N/A',)
        newFCSData._amplifier_gain += ('N/A',)

        newDataRange = [newData.min(), newData.max()]
        newDataResolution = max([chnlData._resolution[0] for chnlData in chnlDataTuple])

        newFCSData._range += (newDataRange,)
        newFCSData._resolution += (newDataResolution,)

        return newFCSData
    
    @classmethod
    def fromArray(cls, template, np_array):
        # Get data from fcs_file object
        obj = np_array.view(cls)

        # Add FCS file attributes
        obj._infile = 'N/A'
        obj._text = template._text
        obj._analysis = template._analysis

        # Add channel-independent attributes
        obj._data_type = template._data_type
        obj._time_step = template._time_step
        obj._acquisition_start_time = template._acquisition_start_time
        obj._acquisition_end_time = template._acquisition_end_time

        # Add channel-dependent attributes
        obj._channels = template._channels
        obj._amplification_type = template._amplification_type
        obj._detector_voltage = template._detector_voltage
        obj._amplifier_gain = template._amplifier_gain
        obj._channel_labels = template._channel_labels
        obj._range = template._range
        obj._resolution = template._resolution

        # Add derived parameters
        obj._drvedParams = template._drvedParams

        return obj
    
    @property
    def drvedParamNames(self):
        return [param.name for param in self._drvedParams]
    
    @property
    def channels_no_drved(self):
        if len(self._drvedParams) == 0:
            return self._channels
        return self._channels[:-len(self._drvedParams)]

    
class drvedParam(QStandardItem):
    def __init__(self, name, formumla: Expr):
        super().__init__(name)
        self.formula = formumla
        
        self.chnlKeys = [str(syb) for syb in list(formumla.free_symbols)]
        self.formulaFunc = lambdify(list(formumla.free_symbols), formumla)

    @property
    def name(self):
        return self.text()

    