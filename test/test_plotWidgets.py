from PySide6.QtWidgets import QWidget

from src.EasyFlowQ.backend.plotWidgets import plotCanvas


def test_edit_in_figure_forge_opens_copied_figure_without_splash(qtbot, monkeypatch):
    from FigureForge import main as figureForgeMain

    canvas = plotCanvas()
    qtbot.addWidget(canvas)
    sourceLine = canvas.ax.plot([0, 1], [0, 1])[0]
    sourceDots = canvas.ax.scatter([0, 1], [1, 0])
    opened = []

    def create_main_window(figure, no_show_splash, block_set_theme):
        window = QWidget()
        qtbot.addWidget(window)
        opened.append((window, figure, no_show_splash, block_set_theme))
        return window

    monkeypatch.setattr(figureForgeMain, 'create_MainWindow', create_main_window)

    canvas.navigationBar.ffEvokeAction.trigger()

    window, figure, no_show_splash, block_set_theme = opened[0]
    assert window.isVisible()
    assert no_show_splash is True
    assert block_set_theme is True
    assert figure is not canvas.fig
    assert figure.axes[0] is not canvas.fig.axes[0]
    assert figure.axes[0].lines[0].get_rasterized() is True
    assert figure.axes[0].collections[0].get_rasterized() is True
    assert sourceLine.get_rasterized() is False
    assert sourceDots.get_rasterized() is False
    assert canvas.figureForgeWindows == [window]
