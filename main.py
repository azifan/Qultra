import sys
import pandas as pd
from PyQt6.QtWidgets import QApplication, QWidget

from src.CeusTool3d.selectImage_ui_helper import SelectImageGUI_CeusTool3d
from src.CeusMcTool2d.selectImage_ui_helper import SelectImageGUI_CeusMcTool2d
from src.QusTool2d.selectImage_ui_helper import SelectImageGUI_QusTool2dIQ
from welcome_ui import Ui_qusPage


class QusGui(Ui_qusPage, QWidget):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.qus2dButton.clicked.connect(self.moveToQus2d)
        self.dceus3dButton.clicked.connect(self.moveToDceus3d)
        self.dceus2dButton.clicked.connect(self.moveToDceusMc2d)
        self.nextPage = None
        self.setLayout(self.verticalLayout)
        self.ceus2dMcData = pd.DataFrame(
            columns=[
                "Patient",
                "Area Under Curve (AUC)",
                "Peak Enhancement (PE)",
                "Time to Peak (TP)",
                "Mean Transit Time (MTT)",
                "TMPPV",
                "ROI Area (mm^2)",
            ]
        )

    def moveToQus2d(self):
        del self.nextPage
        self.nextPage = SelectImageGUI_QusTool2dIQ()
        self.nextPage.show()
        self.nextPage.welcomeGui = self
        self.hide()

    def moveToDceus3d(self):
        del self.nextPage
        self.nextPage = SelectImageGUI_CeusTool3d()
        self.nextPage.show()
        self.nextPage.resize(self.size())
        self.nextPage.welcomeGui = self
        self.hide()

    def moveToDceusMc2d(self):
        del self.nextPage
        self.nextPage = SelectImageGUI_CeusMcTool2d()
        self.nextPage.dataFrame = self.ceus2dMcData
        self.nextPage.show()
        self.nextPage.welcomeGui = self
        self.hide()


# -----------------------------------------------------------------------------------------------
if __name__ == "__main__":
    welcomeApp = QApplication(sys.argv)
    welcomeUI = QusGui()
    welcomeUI.show()
    sys.exit(welcomeApp.exec())
