import pytest
from src.EasyFlowQ.backend.dataIO import FCSData_ef, drvedParam

from sympy import symbols, lambdify
import numpy as np

@pytest.fixture
def fcs_data():
    testData = FCSData_ef('./demo_sample/01-Well-A1.fcs')
    return testData

def test_appendNewParam(fcs_data):    
    x, y = symbols('x y')    
    formula = lambdify((x, y), x + y)
    newdata = fcs_data.appendNewParam(drvedParam('sum', formula, ['FL1-A', 'FL6-A']))    
    assert 'sum' in newdata.drvedParamNames
    assert newdata.shape[1] == fcs_data.shape[1] + 1
    np.testing.assert_array_equal(newdata[:, 'sum'], fcs_data[:, 'FL1-A'] + fcs_data[:, 'FL6-A'])

def test_fromArray(fcs_data):
    mock_data = np.random.rand(100, 5)
    new_fcs_data = FCSData_ef.fromArray(fcs_data, mock_data)
    np.testing.assert_array_equal(new_fcs_data, mock_data)
    assert new_fcs_data._channels == fcs_data._channels
    assert new_fcs_data._drvedParams == fcs_data._drvedParams