import sys
import pandas as pd
from PyQt5.QtWidgets import QApplication, QWidget

from src.CeusTool3d.selectImage_ui_helper import SelectImageGUI_CeusTool3d
from src.CeusMcTool2d.selectImage_ui_helper import SelectImageGUI_CeusMcTool2d
from src.UtcTool2d.selectImage_ui_helper import SelectImageGUI_UtcTool2dIQ
from welcome_ui import Ui_qusPage


class QusGui(Ui_qusPage, QWidget):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.utc2dButton.clicked.connect(self.moveToUtc2d)
        self.ceus3dButton.clicked.connect(self.moveToCeus3d)
        self.ceus2dButton.clicked.connect(self.moveToCeusMc2d)
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

    def moveToUtc2d(self):
        del self.nextPage
        self.nextPage = SelectImageGUI_UtcTool2dIQ()
        self.nextPage.show()
        self.nextPage.welcomeGui = self
        self.hide()

    def moveToCeus3d(self):
        del self.nextPage
        self.nextPage = SelectImageGUI_CeusTool3d()
        self.nextPage.show()
        self.nextPage.resize(self.size())
        self.nextPage.welcomeGui = self
        self.hide()

    def moveToCeusMc2d(self):
        del self.nextPage
        self.nextPage = SelectImageGUI_CeusMcTool2d()
        self.nextPage.dataFrame = self.ceus2dMcData
        self.nextPage.show()
        self.nextPage.welcomeGui = self
        self.hide()


# -----------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------
if __name__ == "__main__":
    welcomeApp = QApplication(sys.argv)
    welcomeUI = QusGui()
    welcomeUI.show()
    sys.exit(welcomeApp.exec())
