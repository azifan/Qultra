import sys
import pandas as pd
from PyQt5.QtWidgets import QApplication
from CeusTool3d.selectImage_ui_helper import *
from UtcTool2d.selectImage_ui_helper import *
from CeusMcTool2d.selectImage_ui_helper import *
from UtcTool2dIQ.selectImage_ui_helper import *
from welcome_ui import *

class QusGui(Ui_qusPage, QWidget):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.utc2dButton.clicked.connect(self.moveToUtc2d)
        self.ceus3dButton.clicked.connect(self.moveToCeus3d)
        self.ceus2dButton.clicked.connect(self.moveToCeusMc2d)
        self.nextPage = None
        self.utc2dRfData = pd.DataFrame(columns=["Patient", "Phantom", "Midband Fit (MBF)", "Spectral Slope (SS)", "Spectral Intercept (SI)"])
        self.ceus2dMcData = pd.DataFrame(columns=["Patient", "Area Under Curve (AUC)", "Peak Enhancement (PE)", "Time to Peak (TP)", "Mean Transit Time (MTT)", "TMPPV", "ROI Area (mm^2)"])
        self.ceus3dData = pd.DataFrame(columns=["Patient",  "Area Under Curve (AUC)", "Peak Enhancement (PE)", "Time to Peak (TP)", "Mean Transit Time (MTT)", "TMPPV", "VOI Volume (mm^3)"])

    def moveToUtc2d(self):
        del self.nextPage
        self.nextPage = SelectImageGUI_UtcTool2dIQ()
        self.nextPage.dataFrame = self.utc2dRfData
        self.nextPage.show()
        self.nextPage.welcomeGui = self
        self.hide()

    def moveToCeus3d(self):
        del self.nextPage
        self.nextPage = SelectImageGUI_CeusTool3d()
        self.nextPage.dataFrame = self.ceus3dData
        self.nextPage.show()
        self.nextPage.welcomeGui = self
        self.hide()

    def moveToCeusMc2d(self):
        del self.nextPage
        self.nextPage = SelectImageGUI_CeusMcTool2d()
        self.nextPage.dataFrame = self.ceus2dMcData
        self.nextPage.show()
        self.nextPage.welcomeGui = self
        self.hide()

#-----------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------
if __name__ == "__main__":
    welcomeApp = QApplication(sys.argv)
    welcomeUI = QusGui()
    welcomeUI.show()
    sys.exit(welcomeApp.exec())