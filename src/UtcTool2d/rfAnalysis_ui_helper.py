import os
import platform

import numpy as np
import matplotlib
import scipy.interpolate as interpolate
import matplotlib.pyplot as plt
from PIL import Image, ImageEnhance
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QWidget, QHBoxLayout

from src.DataLayer.spectral import SpectralData
from src.UtcTool2d.editImageDisplay_ui_helper import EditImageDisplayGUI
from src.UtcTool2d.rfAnalysis_ui import Ui_rfAnalysis
from src.UtcTool2d.exportData_ui_helper import ExportDataGUI
from src.UtcTool2d.saveRoi_ui_helper import SaveRoiGUI
import src.UtcTool2d.analysisParamsSelection_ui_helper as AnalysisParamsSelection
from src.UtcTool2d.psGraphDisplay_ui_helper import PsGraphDisplay

system = platform.system()


class RfAnalysisGUI(QWidget, Ui_rfAnalysis):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        if system == "Windows":
            self.roiSidebarLabel.setStyleSheet(
                """QLabel {
                font-size: 18px;
                color: rgb(255, 255, 255);
                background-color: rgba(255, 255, 255, 0);
                border: 0px;
                font-weight: bold;
            }"""
            )
            self.imageSelectionLabelSidebar.setStyleSheet(
                """QLabel {
                font-size: 18px;
                color: rgb(255, 255, 255);
                background-color: rgba(255, 255, 255, 0);
                border: 0px;
                font-weight: bold;
            }"""
            )
            self.imageLabel.setStyleSheet(
                """QLabel {
                font-size: 13px;
                color: rgb(255, 255, 255);
                background-color: rgba(255, 255, 255, 0);
                border: 0px;
                font-weight: bold;
            }"""
            )
            self.phantomLabel.setStyleSheet(
                """QLabel {
                font-size: 13px;
                color: rgb(255, 255, 255);
                background-color: rgba(255, 255, 255, 0);
                border: 0px;
                font-weight: bold;
            }"""
            )
            self.imagePathInput.setStyleSheet(
                """QLabel {
                font-size: 11px;
                color: rgb(255, 255, 255);
                background-color: rgba(255, 255, 255, 0);
                border: 0px;
            }"""
            )
            self.phantomPathInput.setStyleSheet(
                """QLabel {
                font-size: 11px;
                color: rgb(255, 255, 255);
                background-color: rgba(255, 255, 255, 0);
                border: 0px;
            }"""
            )
            self.analysisParamsLabel.setStyleSheet(
                """QLabel {
                font-size: 18px;
                color: rgb(255, 255, 255);
                background-color: rgba(255, 255, 255, 0);
                border: 0px;
                font-weight:bold;
            }"""
            )
            self.rfAnalysisLabel.setStyleSheet(
                """QLabel {
                font-size: 18px;
                color: rgb(255, 255, 255);
                background-color: rgba(255, 255, 255, 0);
                border: 0px;
                font-weight:bold;
            }"""
            )
            self.exportResultsLabel.setStyleSheet(
                """QLabel {
                font-size: 18px;
                color: rgb(255, 255, 255);
                background-color: rgba(255, 255, 255, 0);
                border: 0px;
                font-weight:bold;
            }"""
            )
            self.avMbfLabel.setStyleSheet(
                """QLabel {
                font-size: 14px;
                color: white;
            background-color: rgba(0,0,0,0);
            }"""
            )
            self.avSsLabel.setStyleSheet(
                """QLabel {
                font-size: 14px;
                color: white;
                background-color: rgba(0,0,0,0);
            }"""
            )
            self.avSiLabel.setStyleSheet(
                """QLabel {
                font-size: 14px;
                color: white;
                background-color: rgba(0,0,0,0);
            }"""
            )
            self.avMbfVal.setStyleSheet(
                """QLabel {
                font-size: 14px;
                color: white;
                background-color: rgba(0,0,0,0);
            }"""
            )
            self.avSsVal.setStyleSheet(
                """QLabel {
                font-size: 14px;
                color: white;
                background-color: rgba(0,0,0,0);
            }"""
            )
            self.avSiVal.setStyleSheet(
                """QLabel {
                font-size: 14px;
                color: white;
                background-color: rgba(0,0,0,0);
            }"""
            )
            self.indMbfLabel.setStyleSheet(
                """QLabel {
                font-size: 14px;
                color: white;
                background-color: rgba(0,0,0,0);
            }"""
            )
            self.indMbfVal.setStyleSheet(
                """QLabel {
                font-size: 14px;
                color: white;
                background-color: rgba(0,0,0,0);
            }"""
            )
            self.indSsLabel.setStyleSheet(
                """QLabel {
                font-size: 14px;
                color: white;
                background-color: rgba(0,0,0,0);
            }"""
            )
            self.indSsVal.setStyleSheet(
                """QLabel {
                font-size: 14px;
                color: white;
                background-color: rgba(0,0,0,0);
            }"""
            )
            self.indSiVal.setStyleSheet(
                """QLabel {
                font-size: 14px;
                color: white;
                background-color: rgba(0,0,0,0);
            }"""
            )
            self.indSiLabel.setStyleSheet(
                """QLabel {
                font-size: 14px;
                color: white;
                background-color: rgba(0,0,0,0);
            }"""
            )

        self.exportDataGUI: ExportDataGUI
        self.lastGui: AnalysisParamsSelection.AnalysisParamsGUI
        self.spectralData: SpectralData
        self.newData = None
        self.saveRoiGUI = SaveRoiGUI()
        self.psGraphDisplay = PsGraphDisplay()
        self.selectedImage: np.ndarray

        self.indMbfVal.setText("")
        self.indSiVal.setText("")
        self.indSsVal.setText("")

        # Display B-Mode
        self.horizontalLayout = QHBoxLayout(self.imDisplayFrame)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.figure = plt.figure()
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self.figure)
        self.horizontalLayout.addWidget(self.canvas)

        self.editImageDisplayGUI = EditImageDisplayGUI()
        self.editImageDisplayButton.clicked.connect(self.openImageEditor)

        self.chooseWindowButton.setCheckable(True)
        self.displayMbfButton.setCheckable(True)
        self.displaySiButton.setCheckable(True)
        self.displaySsButton.setCheckable(True)

        self.displayMbfButton.clicked.connect(self.mbfChecked)
        self.displaySsButton.clicked.connect(self.ssChecked)
        self.displaySiButton.clicked.connect(self.siChecked)
        self.chooseWindowButton.clicked.connect(self.chooseWindow)
        self.editImageDisplayGUI.contrastVal.setValue(1)
        self.editImageDisplayGUI.brightnessVal.setValue(1)
        self.editImageDisplayGUI.sharpnessVal.setValue(1)
        self.editImageDisplayGUI.contrastVal.valueChanged.connect(self.changeContrast)
        self.editImageDisplayGUI.brightnessVal.valueChanged.connect(
            self.changeBrightness
        )
        self.editImageDisplayGUI.sharpnessVal.valueChanged.connect(self.changeSharpness)

        # Prepare heatmap legend plot
        self.horizLayoutLeg = QHBoxLayout(self.legend)
        self.horizLayoutLeg.setObjectName("horizLayoutLeg")
        self.figLeg = plt.figure()
        self.legAx = self.figLeg.add_subplot(111)
        self.cax = self.figLeg.add_axes([0, 0.1, 0.35, 0.8])
        self.canvasLeg = FigureCanvas(self.figLeg)
        self.horizLayoutLeg.addWidget(self.canvasLeg)
        self.canvasLeg.draw()
        self.backButton.clicked.connect(self.backToLastScreen)
        self.exportDataButton.clicked.connect(self.moveToExport)
        self.saveDataButton.clicked.connect(self.saveData)
        self.saveRoiButton.clicked.connect(self.saveRoi)
        self.displayNpsButton.clicked.connect(self.displayNps)
        self.displayNpsButton.setCheckable(True)

    def completeSpectralAnalysis(self):
        if self.spectralData.scConfig is not None:
            self.spectralData.spectralAnalysis.splineToPreSc()
        self.spectralData.spectralAnalysis.generateRoiWindows()
        self.spectralData.spectralAnalysis.computeSpecWindows()
        self.spectralData.drawCmaps()
        if self.spectralData.scConfig is not None:
            self.spectralData.scanConvertCmaps()

        self.plotOnCanvas()

    def displayNps(self):
        if self.displayNpsButton.isChecked():
            self.psGraphDisplay.show()
        else:
            self.psGraphDisplay.hide()

    def saveRoi(self):
        self.saveRoiGUI.rfAnalysisGUI = self
        self.saveRoiGUI.show()

    def moveToExport(self):
        if len(self.spectralData.dataFrame):
            del self.exportDataGUI
            self.exportDataGUI = ExportDataGUI()
            self.exportDataGUI.dataFrame = self.spectralData.dataFrame
            self.exportDataGUI.lastGui = self
            self.exportDataGUI.setFilenameDisplays(
                self.imagePathInput.text(), self.phantomPathInput.text()
            )
            self.exportDataGUI.show()
            self.hide()

    def saveData(self):
        if self.newData is None:
            self.newData = {
                "Patient": self.imagePathInput.text(),
                "Phantom": self.phantomPathInput.text(),
                "Midband Fit (MBF)": np.average(self.spectralData.mbfArr),
                "Spectral Slope (SS)": np.average(self.spectralData.ssArr),
                "Spectral Intercept (SI)": np.average(self.spectralData.siArr),
            }
            self.spectralData.dataFrame = self.spectralData.dataFrame.append(
                self.newData, ignore_index=True
            )

    def backToLastScreen(self):
        self.psGraphDisplay.hide()
        del self.psGraphDisplay
        self.lastGui.spectralData = self.spectralData
        self.lastGui.show()
        self.hide()

    def changeContrast(self):
        self.editImageDisplayGUI.contrastValDisplay.setValue(
            int(self.editImageDisplayGUI.contrastVal.value() * 10)
        )
        self.updateBModeSettings()

    def changeBrightness(self):
        self.editImageDisplayGUI.brightnessValDisplay.setValue(
            int(self.editImageDisplayGUI.brightnessVal.value() * 10)
        )
        self.updateBModeSettings()

    def changeSharpness(self):
        self.editImageDisplayGUI.sharpnessValDisplay.setValue(
            int(self.editImageDisplayGUI.sharpnessVal.value() * 10)
        )
        self.updateBModeSettings()

    def openImageEditor(self):
        if self.editImageDisplayGUI.isVisible():
            self.editImageDisplayGUI.hide()
        else:
            self.editImageDisplayGUI.show()

    def setFilenameDisplays(self, imageName, phantomName):
        self.imagePathInput.setHidden(False)
        self.phantomPathInput.setHidden(False)
        self.imagePathInput.setText(imageName)
        self.phantomPathInput.setText(phantomName)

    def plotOnCanvas(self):  # Plot current image on GUI
        self.ax.clear()
        self.selectedImage = self.spectralData.finalBmode if self.selectedImage is None else self.selectedImage
        self.ax.imshow(self.selectedImage, cmap="Greys_r")
        self.figure.set_facecolor((0, 0, 0, 0))
        self.ax.axis("off")

        self.ax.plot(
            self.spectralData.splineX,
            self.spectralData.splineY,
            color="cyan",
            zorder=1,
            linewidth=0.75,
        )
        self.figure.subplots_adjust(
            left=0, right=1, bottom=0, top=1, hspace=0.2, wspace=0.2
        )
        self.cursor = matplotlib.widgets.Cursor(
            self.ax, color="gold", linewidth=0.4, useblit=True
        )
        self.cursor.set_active(False)
        plt.tick_params(bottom=False, left=False, labelbottom=False, labelleft=False)
        self.canvas.draw()  # Refresh canvas

    def updateBModeSettings(
        self,
    ):  # Updates background photo when image settings are modified
        self.cvIm = Image.open(os.path.join("Junk", "bModeImRaw.png"))
        contrast = ImageEnhance.Contrast(self.cvIm)
        self.editImageDisplayGUI.contrastVal.value()
        imOutput = contrast.enhance(self.editImageDisplayGUI.contrastVal.value())
        brightness = ImageEnhance.Brightness(imOutput)
        self.editImageDisplayGUI.brightnessVal.value()
        imOutput = brightness.enhance(self.editImageDisplayGUI.brightnessVal.value())
        sharpness = ImageEnhance.Sharpness(imOutput)
        self.editImageDisplayGUI.sharpnessVal.value()
        imOutput = sharpness.enhance(self.editImageDisplayGUI.sharpnessVal.value())
        self.spectralData.finalBmode = imOutput
        self.selectedImage = self.spectralData.finalBmode
        self.displayMbfButton.setChecked(False); self.displaySsButton.setChecked(False)
        self.displaySiButton.setChecked(False)
        self.udpateLegend("clear")
        self.plotOnCanvas()

    def mbfChecked(self):
        if self.displayMbfButton.isChecked():
            if self.displaySsButton.isChecked() or self.displaySiButton.isChecked():
                self.displaySsButton.setChecked(False)
                self.displaySiButton.setChecked(False)
            self.selectedImage = self.spectralData.finalMbfIm
            self.updateLegend("MBF")
        else:
            self.selectedImage = self.spectralData.finalBmode
            self.updateLegend("clear")
        
    def ssChecked(self):
        if self.displaySsButton.isChecked():
            if self.displayMbfButton.isChecked() or self.displaySiButton.isChecked():
                self.displayMbfButton.setChecked(False)
                self.displaySiButton.setChecked(False)
            self.selectedImage = self.spectralData.finalSsIm
            self.updateLegend("SS")
        else:
            self.selectedImage = self.spectralData.finalBmode
            self.updateLegend("clear")
        
    def siChecked(self):
        global curDisp
        if self.displaySiButton.isChecked():
            if self.displayMbfButton.isChecked() or self.displaySsButton.isChecked():
                self.displayMbfButton.setChecked(False)
                self.displaySsButton.setChecked(False)
            self.selectedImage = self.spectralData.finalSiIm
            self.updateLegend("SI")
        else:
            self.selectedImage = self.spectralData.finalBmode
            self.updateLegend("clear")

    def updateLegend(self, curDisp):
        self.legAx.clear()
        self.figLeg.set_visible(True)
        a = np.array([[0, 1]])
        if curDisp == "MBF":
            img = self.legAx.imshow(a, cmap="viridis")
            self.legAx.set_visible(False)
            # cax = plt.axes([0, 0.1, 0.25, 0.8])
            self.figLeg.colorbar(
                orientation="vertical", cax=self.cax, mappable=img
            )
            self.legAx.text(2.1, 0.21, "Midband Fit", rotation=270, size=9)
            self.legAx.tick_params("y", labelsize=7, pad=0.5)
            # plt.text(3, 0.17, "Midband Fit", rotation=270, size=5)
            # plt.tick_params('y', labelsize=5, pad=0.7)
            self.cax.set_yticks([0, 0.25, 0.5, 0.75, 1])
            self.cax.set_yticklabels(
                [
                    int(self.spectralData.minMbf * 10) / 10,
                    int((((self.spectralData.maxMbf - self.spectralData.minMbf) / 4) + self.spectralData.minMbf) * 10) / 10,
                    int((((self.spectralData.maxMbf - self.spectralData.minMbf) / 2) + self.spectralData.minMbf) * 10) / 10,
                    int(((3 * (self.spectralData.maxMbf - self.spectralData.minMbf) / 4) + self.spectralData.minMbf) * 10) / 10,
                    int(self.spectralData.maxMbf * 10) / 10,
                ]
            )
        elif curDisp == "SS":
            img = self.legAx.imshow(a, cmap="magma")
            self.legAx.set_visible(False)
            # cax = plt.axes([0, 0.1, 0.25, 0.8])
            self.figLeg.colorbar(orientation="vertical", cax=self.cax, mappable=img)
            self.legAx.text(2.2, 0, "Spectral Slope (1e-6)", rotation=270, size=6)
            self.legAx.tick_params("y", labelsize=7, pad=0.7)
            # plt.text(3, 0.02, "Spectral Slope (1e-6)", rotation=270, size=4)
            # plt.tick_params('y', labelsize=4, pad=0.3)
            self.cax.set_yticks([0, 0.25, 0.5, 0.75, 1])
            self.cax.set_yticklabels(
                [
                    int(self.spectralData.minSs * 100000000) / 100,
                    int((((self.spectralData.maxSs - self.spectralData.minSs) / 4) + self.spectralData.minSs) * 10000000) / 100,
                    int((((self.spectralData.maxSs - self.spectralData.minSs) / 2) + self.spectralData.minSs) * 100000000) / 100,
                    int(((3 * (self.spectralData.maxSs - self.spectralData.minSs) / 4) + self.spectralData.minSs) * 100000000) / 100,
                    int(self.spectralData.maxSs * 100000000) / 100,
                ]
            )
        elif curDisp == "SI":
            img = self.legAx.imshow(a, cmap="plasma")
            self.legAx.set_visible(False)
            # cax = plt.axes([0, 0.1, 0.25, 0.8])
            self.figLeg.colorbar(orientation="vertical", cax=self.cax, mappable=img)
            self.legAx.text(2.2, 0.09, "Spectral Intercept", rotation=270, size=6)
            self.legAx.tick_params("y", labelsize=7, pad=0.7)
            # plt.text(3, 0, "Spectral Intercept", rotation=270, size=5)
            # plt.tick_params('y', labelsize=5, pad=0.7)
            self.cax.set_yticks([0, 0.25, 0.5, 0.75, 1])
            self.cax.set_yticklabels(
                [
                    int(self.spectralData.minSi * 10) / 10,
                    int((((self.spectralData.maxSi - self.spectralData.minSi) / 4) + self.spectralData.minSi) * 10) / 10,
                    int((((self.spectralData.maxSi - self.spectralData.minSi) / 2) + self.spectralData.minSi) * 10) / 10,
                    int(((3 * (self.spectralData.maxSi - self.spectralData.minSi) / 4) + self.spectralData.minSi) * 10) / 10,
                    int(self.spectralData.maxSi * 10) / 10,
                ]
            )
        elif curDisp == "" or curDisp == "clear":
            self.figLeg.set_visible(False)
        self.figLeg.set_facecolor((1, 1, 1, 1))
        # self.horizLayoutLeg.removeWidget(self.canvasLeg)
        # self.canvasLeg = FigureCanvas(self.figLeg)
        # self.horizLayoutLeg.addWidget(self.canvasLeg)
        self.canvasLeg.draw()