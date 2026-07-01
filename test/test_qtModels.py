import pandas as pd

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIntValidator

from src.EasyFlowQ.backend.qtModels import pandasTableModel


def test_pandasTableModel_color_roles_fall_back_for_missing_or_invalid_values(qapp):
    table_df = pd.DataFrame({"value": [1, 2]})
    foreground_df = pd.DataFrame({"value": ["#112233", None]})
    background_df = pd.DataFrame({"value": ["not-a-color", "#abcdef"]})

    model = pandasTableModel(table_df, foregroundDF=foreground_df, backgroundDF=background_df)

    first_index = model.index(0, 0)
    second_index = model.index(1, 0)

    assert model.data(first_index, Qt.ForegroundRole) == QColor("#112233")
    assert model.data(second_index, Qt.ForegroundRole) == QColor("#000000")
    assert model.data(first_index, Qt.BackgroundRole) == QColor("#ffffff")
    assert model.data(second_index, Qt.BackgroundRole) == QColor("#abcdef")


def test_pandasTableModel_setData_uses_validator(qapp):
    table_df = pd.DataFrame({"value": [1]})
    model = pandasTableModel(table_df, validator=QIntValidator())
    index = model.index(0, 0)

    assert model.setData(index, "42")
    assert model.dfData.iloc[0, 0] == 42

    assert not model.setData(index, "bad")
    assert model.dfData.iloc[0, 0] == 42


def test_pandasTableModel_color_df_preserves_values_when_shape_matches_but_labels_differ(qapp):
    table_df = pd.DataFrame([[1, 2]], index=["row_a"], columns=["col_a", "col_b"])
    foreground_df = pd.DataFrame([["#112233", "#abcdef"]], index=[0], columns=[0, 1])

    model = pandasTableModel(table_df, foregroundDF=foreground_df)

    first_index = model.index(0, 0)
    second_index = model.index(0, 1)

    assert model.data(first_index, Qt.ForegroundRole) == QColor("#112233")
    assert model.data(second_index, Qt.ForegroundRole) == QColor("#abcdef")
