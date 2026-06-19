import pytest
from src.EasyFlowQ.backend.ioData import FCSData_ef, drvedParam, processFCS2List

from sympy import symbols, lambdify
import numpy as np

@pytest.fixture
def fcs_data():
    testData = FCSData_ef('./demo_sample/01-Well-A1.fcs')
    return testData

@pytest.fixture
def fcsDataList():
    return processFCS2List('./demo_sample/multisample_example_1.FCS')

def test_fcsDataList(fcsDataList):
    assert len(fcsDataList) == 48, 'The number of samples in the multi-sample FCS file is not correct'

def test_appendNewParam(fcs_data):    
    x, y = symbols(['FL1-A', 'FL6-A'])    
    newdata = fcs_data.appendNewParam(drvedParam('sum', x + y))    
    assert 'sum' in newdata.drvedParamNames
    assert newdata.shape[1] == fcs_data.shape[1] + 1

    all_equal = np.equal(fcs_data[:, 'FL1-A'] + fcs_data[:, 'FL6-A'], newdata[:, 'sum'])
    assert np.all(all_equal), 'The new parameter values are not correct'

def test_fromArray(fcs_data):
    mock_data = np.random.rand(100, 5)
    new_fcs_data = FCSData_ef.fromArray(fcs_data, mock_data)

    all_equal = np.equal(new_fcs_data, mock_data)
    assert np.all(all_equal), 'The new FCS data values are not correct'