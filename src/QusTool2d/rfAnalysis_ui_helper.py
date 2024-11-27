import platform

import cv2
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import pyqtgraph as pg
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtWidgets import QWidget, QHBoxLayout

from pyquantus.qus import SpectralData
from src.QusTool2d.rfAnalysis_ui import Ui_rfAnalysis
from src.QusTool2d.exportData_ui_helper import ExportDataGUI
import src.QusTool2d.analysisParamsSelection_ui_helper as AnalysisParamsSelection
from src.QusTool2d.psGraphDisplay_ui_helper import PsGraphDisplay
from src.QusTool2d.saveConfig_ui_helper import SaveConfigGUI
from src.QusTool2d.windowsTooLarge_ui_helper import WindowsTooLargeGUI

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

        self.exportDataGUI = ExportDataGUI()
        self.lastGui: AnalysisParamsSelection.AnalysisParamsGUI
        self.spectralData: SpectralData
        self.newData = None
        self.cid = None; self.lastPlot = None
        self.psGraphDisplay = PsGraphDisplay()
        self.saveConfigGUI = SaveConfigGUI()
        self.windowsTooLargeGUI = WindowsTooLargeGUI()
        self.selectedImage: np.ndarray | None = None

        # Display B-Mode
        self.horizontalLayout = QHBoxLayout(self.imDisplayFrame)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.figure = plt.figure()
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self.figure)
        self.horizontalLayout.addWidget(self.canvas)

        self.displayMbfButton.setCheckable(True)
        self.displaySiButton.setCheckable(True)
        self.displaySsButton.setCheckable(True)

        self.displayMbfButton.clicked.connect(self.mbfChecked)
        self.displaySsButton.clicked.connect(self.ssChecked)
        self.displaySiButton.clicked.connect(self.siChecked)

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
        self.displayNpsButton.clicked.connect(self.displayNps)
        self.displayNpsButton.setCheckable(True)
        self.saveConfigButton.clicked.connect(self.saveConfig)
        self.updateLegend("clear")

    def saveConfig(self):
        self.saveConfigGUI.imName = self.imagePathInput.text()
        self.saveConfigGUI.phantomName = self.phantomPathInput.text()
        self.saveConfigGUI.config = self.spectralData.spectralAnalysis.config
        self.saveConfigGUI.show()

    def completeSpectralAnalysis(self) -> int:
        if hasattr(self.spectralData, 'scConfig'):
            self.spectralData.spectralAnalysis.splineToPreSc()
        self.spectralData.spectralAnalysis.generateRoiWindows()
        success = self.spectralData.spectralAnalysis.computeSpecWindows()
        if success < 0:
            self.windowsTooLargeGUI.show()
            return -1
        self.attCoefVal.setText(f"{np.round(self.spectralData.spectralAnalysis.attenuationCoef, decimals=2)}")
        self.attCorrVal.setText(f"{np.round(self.spectralData.spectralAnalysis.attenuationCorr, decimals=2)}")
        self.bscVal.setText(f"{np.round(self.spectralData.spectralAnalysis.backScatterCoef, decimals=2)}")
        self.spectralData.drawCmaps()
        if hasattr(self.spectralData, 'scConfig'):
            self.spectralData.scanConvertCmaps()

        mbfMean = np.mean(self.spectralData.mbfArr)
        ssMean = np.mean(self.spectralData.ssArr)
        siMean = np.mean(self.spectralData.siArr)
        self.avMbfVal.setText(f"{np.round(mbfMean, decimals=1)}")
        self.avSsVal.setText(f"{np.round(ssMean*1e6, decimals=2)}")
        self.avSiVal.setText(f"{np.round(siMean, decimals=1)}")

        npsArr = [window.results.nps for window in self.spectralData.spectralAnalysis.roiWindows]
        avNps = np.mean(npsArr, axis=0)
        f = self.spectralData.spectralAnalysis.roiWindows[0].results.f
        x = np.linspace(min(f), max(f), 100)
        y = ssMean*x + siMean

        del self.psGraphDisplay
        self.psGraphDisplay = PsGraphDisplay()

        # ps = self.spectralData.spectralAnalysis.roiWindows[0].results.ps
        # rps = self.spectralData.spectralAnalysis.roiWindows[0].results.rPs
        # nps = self.spectralData.spectralAnalysis.roiWindows[0].results.nps
        # self.psGraphDisplay.plotGraph.plot(f/1e6, ps, pen=pg.mkPen(color="b"), name="PS")
        # self.psGraphDisplay.plotGraph.plot(f/1e6, rps, pen=pg.mkPen(color="r"), name="rPS")
        # self.psGraphDisplay.plotGraph.plot(f/1e6, nps+np.amin(ps), pen=pg.mkPen(color="g"), name="NPS")

        for nps in npsArr:
            self.psGraphDisplay.plotGraph.plot(f/1e6, nps, pen=pg.mkPen(color=(0, 0, 255, 51)))
        self.psGraphDisplay.plotGraph.plot(f/1e6, avNps, pen=pg.mkPen(color="r", width=2))
        self.psGraphDisplay.plotGraph.plot(x/1e6, y, pen=pg.mkPen(color=(255, 172, 28), width=2))
        self.psGraphDisplay.plotGraph.plot(2*[self.spectralData.analysisFreqBand[0]/1e6], [np.amin(npsArr), np.amax(npsArr)], 
                                            pen=pg.mkPen(color="m", width=2))
        self.psGraphDisplay.plotGraph.plot(2*[self.spectralData.analysisFreqBand[1]/1e6], [np.amin(npsArr), np.amax(npsArr)], 
                                            pen=pg.mkPen(color="m", width=2))
        self.psGraphDisplay.plotGraph.setYRange(np.amin(npsArr), np.amax(npsArr))

        self.plotOnCanvas()
        return 0

    def displayNps(self):
        if self.displayNpsButton.isChecked():
            self.psGraphDisplay.show()
        else:
            self.psGraphDisplay.hide()

    def moveToExport(self):
        # if len(self.spectralData.dataFrame):
        del self.exportDataGUI
        self.exportDataGUI = ExportDataGUI()
        curData = {
                "Patient": [self.imagePathInput.text()],
                "Phantom": [self.phantomPathInput.text()],
                "Midband Fit (MBF)": [np.mean(self.spectralData.mbfArr)],
                "Spectral Slope (SS)": [np.mean(self.spectralData.ssArr)],
                "Spectral Intercept (SI)": [np.mean(self.spectralData.siArr)],
                "Attenuation Coefficient": [self.spectralData.spectralAnalysis.attenuationCoef],
                "Attenuation Coefficient R-Score": [self.spectralData.spectralAnalysis.attenuationCorr],
                "Backscatter Coefficient": [self.spectralData.spectralAnalysis.backScatterCoef],
                "Nakagami Params": [f"{self.spectralData.spectralAnalysis.nakagamiParams}"],
                "Effective Scatterer Diameter": [self.spectralData.spectralAnalysis.effectiveScattererDiameter],
                "Effective Scatterer Concentration": [self.spectralData.spectralAnalysis.effectiveScattererConcentration],
                "ROI Name": ""
            }
        self.exportDataGUI.dataFrame = pd.DataFrame.from_dict(curData)
        self.exportDataGUI.lastGui = self
        self.exportDataGUI.setFilenameDisplays(
            self.imagePathInput.text(), self.phantomPathInput.text()
        )
        self.exportDataGUI.show()
        self.hide()

    def backToLastScreen(self):
        self.psGraphDisplay.hide()
        del self.psGraphDisplay
        self.lastGui.spectralData = self.spectralData
        self.lastGui.show()
        self.hide()

    def setFilenameDisplays(self, imageName, phantomName):
        self.imagePathInput.setHidden(False)
        self.phantomPathInput.setHidden(False)
        self.imagePathInput.setText(imageName)
        self.phantomPathInput.setText(phantomName)

    def plotOnCanvas(self):  # Plot current image on GUI
        self.ax.clear()
        self.selectedImage = self.spectralData.finalBmode if self.selectedImage is None else self.selectedImage
        quotient = self.spectralData.depth / self.spectralData.width
        self.ax.imshow(self.selectedImage, aspect=quotient*(self.selectedImage.shape[1]/self.selectedImage.shape[0]))
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

        if self.cid is None:
            self.cid = self.figure.canvas.mpl_connect("button_press_event", self.onClick)
        self.canvas.draw()  # Refresh canvas

    def onClick(self, event):
        xCoord = round(event.xdata)
        yCoord = round(event.ydata)
        windowIdx = self.spectralData.finalWindowIdxMap[yCoord, xCoord]
        if self.figLeg.get_visible() and windowIdx:
            mask = self.spectralData.finalWindowIdxMap == windowIdx
            contours, _ = cv2.findContours(np.transpose(mask).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            mask_coords = np.array(contours).reshape((-1, 2))
            mask_coords = np.append(mask_coords, [mask_coords[0]], axis=0)
            if self.lastPlot is not None:
                self.lastPlot[0].remove()
            self.lastPlot = self.ax.plot(mask_coords[:, 1], mask_coords[:, 0], color="white", linewidth=2)
            self.canvas.draw()

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
        self.plotOnCanvas()
        
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
        self.plotOnCanvas()
        
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
        self.plotOnCanvas()

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