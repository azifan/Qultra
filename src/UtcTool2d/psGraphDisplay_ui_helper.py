import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QWidget, QHBoxLayout
import pyqtgraph as pg

from src.UtcTool2d.psGraphDisplay_ui import Ui_psGraphWidget

class PsGraphDisplay(Ui_psGraphWidget, QWidget):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Display PS Graph
        self.horizontalLayout = QHBoxLayout(self.psGraphFrame)
        self.horizontalLayout.setObjectName("horizontalLayout")
        # plt.style.use("default")
        # self.figure = plt.figure()
        # self.canvas = FigureCanvas(self.figure)
        # self.ax = self.figure.add_axes([0, 0.1, 0.35, 0.8])
        # self.ax.set_xlabel("Frequency (MHz)", fontsize=8)
        # self.ax.set_ylabel("Power (dB)", fontsize=8)

        self.plot_graph = pg.PlotWidget()
        self.plot_graph.addLegend()
        self.plot_graph.setBackground("w")
        self.plot_graph.setLabel("left", "Power (dB)")
        self.plot_graph.setLabel("bottom", "Frequency (MHz)")
        self.horizontalLayout.addWidget(self.plot_graph)

