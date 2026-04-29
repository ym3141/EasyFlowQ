from src.EasyFlowQ.backend.gates import polygonGate, lineGate
from src.EasyFlowQ.backend.qtModels import gateWidgetItem
from src.EasyFlowQ.backend.ioSession import _convert_gateItem
from src.EasyFlowQ.FlowCal import plot

import json

# Test if the gates can be seriliazed and saved as json files in backend.efio
class TestGates:
    def test_polygonGate_to_json(self):
        # Create a polygon gate
        gate = polygonGate(['FL1', 'FL2'], ['log', 'logicle'], 
                           [None, (262144, 4.5, 0.5)], verts=[[0.1, 0], [0.001, 1], [1, 1], [1, 0]])
        gateItem = gateWidgetItem('Test Gate', gate)
        gateSave = _convert_gateItem(gateItem)
        json_str = json.dumps(gateSave, indent=4)
        assert gateSave['verts'] == [[0.1, 0], [0.001, 1], [1, 1], [1, 0]]
        assert gate.invLogicleTs[0] == None
        assert type(gate.invLogicleTs[1]) == plot._InterpolatedInverseTransform
        assert gateSave['displayName'] == 'Test Gate'

    def test_lineGate_to_json(self):
        # Create a line gate
        gate = lineGate('FL1', [0, 100])
        gateItem = gateWidgetItem('Test Gate', gate)
        gateSave = _convert_gateItem(gateItem)
        json_str = json.dumps(gateSave, indent=4)
        assert gateSave['displayName'] == 'Test Gate'

