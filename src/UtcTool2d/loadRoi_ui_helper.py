import os
import csv
import pickle

from PyQt5.QtWidgets import QWidget, QFileDialog
from src.UtcTool2d.loadRoi_ui import Ui_loadRoi
import src.UtcTool2d.roiSelection_ui_helper as RoiSelectionSection

class LoadRoiGUI(Ui_loadRoi, QWidget):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.chooseRoiGUI: RoiSelectionSection.RoiSelectionGUI

        self.chooseFileButton.clicked.connect(self.chooseFile)
        self.clearFileButton.clicked.connect(self.clearFile)
        self.openRoiButton.clicked.connect(self.getRoiPath)
        self.backButton.clicked.connect(self.backToChoice)

    def backToChoice(self):
        self.hide()
        self.chooseRoiGUI.show()

    def chooseFile(self):
        fileName, _ = QFileDialog.getOpenFileName(None, "Open file", filter="*.pkl")
        if fileName != "":
            self.roiPathInput.setText(fileName)

    def clearFile(self):
        self.roiPathInput.clear()

    def getRoiPath(self):
        if os.path.exists(self.roiPathInput.text()):
            with open(self.roiPathInput.text(), "rb") as f:
                AnalysisInfo = pickle.load(f)

                if (self.chooseRoiGUI.imagePathInput.text() != AnalysisInfo.imName or 
                    self.chooseRoiGUI.phantomPathInput.text() != AnalysisInfo.phantomName): 
                    print("Selected ROI for wrong image")
                    return
                
                self.chooseRoiGUI.AnalysisInfo = AnalysisInfo
                self.chooseRoiGUI.ImDisplayInfo = self.chooseRoiGUI.AnalysisInfo.ImDisplayInfo
                self.chooseRoiGUI.RefDisplayInfo = self.chooseRoiGUI.AnalysisInfo.RefDisplayInfo
                self.chooseRoiGUI.pointsPlottedX = self.chooseRoiGUI.AnalysisInfo.pointsPlottedX
                self.chooseRoiGUI.pointsPlottedY = self.chooseRoiGUI.AnalysisInfo.pointsPlottedY
                self.chooseRoiGUI.finalSplineX = self.chooseRoiGUI.AnalysisInfo.finalSplineX
                self.chooseRoiGUI.finalSplineY = self.chooseRoiGUI.AnalysisInfo.finalSplineY
                self.chooseRoiGUI.displayInitialImage()
                self.chooseRoiGUI.acceptLoadedRoiButton.setHidden(False)
                self.chooseRoiGUI.undoLoadedRoiButton.setHidden(False)
                self.chooseRoiGUI.newRoiButton.setHidden(True)
                self.chooseRoiGUI.loadRoiButton.setHidden(True)
                self.chooseRoiGUI.drawRoiButton.setChecked(True)
                self.chooseRoiGUI.drawRoiButton.setCheckable(True)
                self.chooseRoiGUI.redrawRoiButton.setHidden(True)
                self.chooseRoiGUI.drawRectangleButton.setHidden(True)
                self.chooseRoiGUI.closeRoiButton.setHidden(True)


            self.hide()
            self.chooseRoiGUI.show()
