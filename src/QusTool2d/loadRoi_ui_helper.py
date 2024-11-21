import os
import pickle
from pathlib import Path

from PyQt6.QtWidgets import QWidget, QFileDialog
from src.QusTool2d.loadRoi_ui import Ui_loadRoi
import src.QusTool2d.roiSelection_ui_helper as RoiSelectionSection

class LoadRoiGUI(Ui_loadRoi, QWidget):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.chooseRoiGUI: RoiSelectionSection.RoiSelectionGUI

        self.wrongImageWarning.hide()
        self.chooseFileButton.clicked.connect(self.chooseFile)
        self.clearFileButton.clicked.connect(self.clearFile)
        self.openRoiButton.clicked.connect(self.getRoiPath)
        self.backButton.clicked.connect(self.backToChoice)

    def backToChoice(self):
        self.wrongImageWarning.hide()
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
                roiInfo = pickle.load(f)

            if (Path(self.chooseRoiGUI.imagePathInput.text()).stem != Path(roiInfo["Image Name"]).stem or 
                self.chooseRoiGUI.phantomPathInput.text() != roiInfo["Phantom Name"]): 
                print("Selected ROI for wrong image")
                self.wrongImageWarning.show()
                return
            
            self.chooseRoiGUI.spectralData.splineX = roiInfo["Spline X"]
            self.chooseRoiGUI.spectralData.splineY = roiInfo["Spline Y"]
            self.chooseRoiGUI.plotOnCanvas()
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
