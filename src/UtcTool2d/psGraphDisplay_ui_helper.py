import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QWidget, QHBoxLayout

from src.UtcTool2d.psGraphDisplay_ui import Ui_psGraphWidget

class PsGraphDisplay(Ui_psGraphWidget, QWidget):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Display PS Graph
        self.horizontalLayout = QHBoxLayout(self.psGraphFrame)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_xlabel("Frequency (MHz)", fontsize=8)
        self.ax.set_ylabel("Power (dB)", fontsize=8)
        self.horizontalLayout.addWidget(self.canvas)

