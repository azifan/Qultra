import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QApplication

from src.CeusTool3d.legend_ui import Ui_legend

class LegendDisplay(Ui_legend, QWidget):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Display Cur Legend
        self.horizontalLayout = QHBoxLayout(self.legendFrame)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.horizontalLayout.addWidget(self.canvas)

    def truncate_colormap(self, cmap, minval=0.0, maxval=1.0, n=100):
        import matplotlib.colors as colors

        new_cmap = colors.LinearSegmentedColormap.from_list(
            "trunc({n},{a:.2f},{b:.2f})".format(n=cmap.name, a=minval, b=maxval),
            cmap(np.linspace(minval, maxval, n)),
        )
        return new_cmap


if __name__ == "__main__":
    import sys

    welcomeApp = QApplication(sys.argv)
    welcomeUI = LegendDisplay()
    welcomeUI.show()
    sys.exit(welcomeApp.exec())

