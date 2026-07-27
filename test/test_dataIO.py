import pytest
from src.EasyFlowQ.backend.ioData import FCSData_ef, drvedParam, processFCS2List
from src.EasyFlowQ.backend.fcsWriter import writeFCS, exportKeywords

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

def test_writeFCS_gatedSubset(fcs_data, tmp_path):
    # Export the events above the median FSC-A, as a gate would
    gated = fcs_data[fcs_data[:, 'FSC-A'] > np.median(fcs_data[:, 'FSC-A']), :]

    savePath = str(tmp_path / 'gated.fcs')
    writeFCS(savePath, gated, extraKeywords=exportKeywords(gateNames=['testGate'], compensated=False))
    readBack = FCSData_ef(savePath)

    assert readBack.shape == gated.shape, 'The exported FCS has the wrong shape'
    assert tuple(readBack.channels) == tuple(gated.channels), 'The exported channels are not correct'
    assert tuple(readBack.channel_labels()) == tuple(gated.channel_labels()), 'The exported channel labels are not correct'
    assert np.all(np.equal(np.asarray(readBack), np.asarray(gated))), 'The exported values are not correct'

    # The data is written linear (already in RFI), and the spillover of the
    # source file no longer applies to the exported events
    assert readBack.text['$P1E'] == '0,0'
    assert '$SPILLOVER' not in readBack.text
    assert readBack.text['EASYFLOWQ_GATES'] == 'testGate'
    assert readBack.text['EASYFLOWQ_COMPENSATED'] == 'False'
    # Keywords describing the source acquisition are kept
    assert readBack.text['$CYT'] == fcs_data.text['$CYT']

def test_writeFCS_drvedParam(fcs_data, tmp_path):
    x, y = symbols(['FL1-A', 'FL6-A'])
    withDrved = fcs_data.appendNewParam(drvedParam('sum', x + y))

    savePath = str(tmp_path / 'drved.fcs')
    writeFCS(savePath, withDrved, dataType='D')
    readBack = FCSData_ef(savePath)

    assert readBack.channels[-1] == 'sum', 'The derived parameter was not exported'
    assert readBack.shape == withDrved.shape
    assert np.all(np.equal(np.asarray(readBack), np.asarray(withDrved))), 'The exported values are not correct'

def test_writeFCS_emptyGate(fcs_data, tmp_path):
    savePath = str(tmp_path / 'empty.fcs')
    writeFCS(savePath, fcs_data[0:0, :])
    readBack = FCSData_ef(savePath)

    assert readBack.shape == (0, fcs_data.shape[1]), 'An empty gate should export an FCS with no events'

def test_writeFCS_multiSample(fcsDataList, tmp_path):
    # Samples read out of a multi-sample file should not carry $NEXTDATA over
    savePath = str(tmp_path / 'single.fcs')
    writeFCS(savePath, fcsDataList[1])
    readBack = FCSData_ef(savePath)

    assert readBack.text['$NEXTDATA'] == '0'
    assert readBack.shape == fcsDataList[1].shape