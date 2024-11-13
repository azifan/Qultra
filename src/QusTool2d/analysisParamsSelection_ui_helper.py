import platform

import numpy as np
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtGui import QImage, QPixmap

from pyquantus.qus import SpectralData
from src.QusTool2d.analysisParamsSelection_ui import Ui_analysisParams
from src.QusTool2d.rfAnalysis_ui_helper import RfAnalysisGUI
from src.QusTool2d.loadConfig_ui_helper import LoadConfigGUI
import src.QusTool2d.roiSelection_ui_helper as RoiSelectionSection

system = platform.system()


class AnalysisParamsGUI(Ui_analysisParams, QWidget):
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
            self.imageDepthLabel.setStyleSheet(
                """QLabel {
                color: white;
                background-color: rgba(0,0,0,0);
                font-size: 18px;
            }"""
            )
            self.imageWidthLabel.setStyleSheet(
                """QLabel {
                color: white;
                background-color: rgba(0,0,0,0);
                font-size: 18px;
            }"""
            )
            self.imageDepthVal.setStyleSheet(
                """QLabel {
                color: white;
                background-color: rgba(0,0,0,0);
                font-size: 18px;
            }"""
            )
            self.imageWidthVal.setStyleSheet(
                """QLabel {
                color: white;
                background-color: rgba(0,0,0,0);
                font-size: 18px;
            }"""
            )
            self.axWinSizeLabel.setStyleSheet(
                """QLabel {
                color: white;
                background-color: rgba(0,0,0,0);
                font-size: 18px;
            }"""
            )
            self.latWinSizeLabel.setStyleSheet(
                """QLabel {
                color: white;
                background-color: rgba(0,0,0,0);
                font-size: 18px;
            }"""
            )
            self.axOverlapLabel.setStyleSheet(
                """QLabel {
                color: white;
                background-color: rgba(0,0,0,0);
                font-size: 18px;
            }"""
            )
            self.latOverlapLabel.setStyleSheet(
                """QLabel {
                color: white;
                background-color: rgba(0,0,0,0);
                font-size: 18px;
            }"""
            )
            self.windowThresholdLabel.setStyleSheet(
                """QLabel {
                color: white;
                background-color: rgba(0,0,0,0);
                font-size: 18px;
            }"""
            )
            self.minFreqLabel.setStyleSheet(
                """QLabel {
                color: white;
                background-color: rgba(0,0,0,0);
                font-size: 18px;
            }"""
            )
            self.maxFreqLabel.setStyleSheet(
                """QLabel {
                color: white;
                background-color: rgba(0,0,0,0);
                font-size: 18px;
            }"""
            )
            self.lowBandFreqLabel.setStyleSheet(
                """QLabel {
                color: white;
                background-color: rgba(0,0,0,0);
                font-size: 18px;
            }"""
            )
            self.upBandFreqLabel.setStyleSheet(
                """QLabel {
                color: white;
                background-color: rgba(0,0,0,0);
                font-size: 18px;
            }"""
            )
            self.samplingFreqLabel.setStyleSheet(
                """QLabel {
                color: white;
                background-color: rgba(0,0,0,0);
                font-size: 18px;
            }"""
            )

        self.rfAnalysisGUI = RfAnalysisGUI()
        self.loadConfigGUI = LoadConfigGUI()
        self.lastGui: RoiSelectionSection.RoiSelectionGUI
        self.spectralData: SpectralData

        self.continueButton.clicked.connect(self.continueToRfAnalysis)
        self.backButton.clicked.connect(self.backToLastScreen)
        self.singleRoiWindowButton.clicked.connect(self.singleRoiWindow)
        self.loadConfigButton.clicked.connect(self.loadConfig)

    def loadConfig(self):
        self.loadConfigGUI.analysisParamsGUI = self
        self.loadConfigGUI.show()

    def initParams(self):
        self.axWinSizeVal.setMinimum(
            2 * self.spectralData.waveLength
        )  # should be at least 10 times wavelength, must be at least 2 times
        self.latWinSizeVal.setMinimum(
            2 * self.spectralData.waveLength
        )  # should be at least 10 times wavelength, must be at least 2 times

        self.axWinSizeVal.setValue(self.spectralData.axWinSize)
        self.latWinSizeVal.setValue(self.spectralData.latWinSize)
        self.axOverlapVal.setValue(int(self.spectralData.axOverlap*100))
        self.latOverlapVal.setValue(int(self.spectralData.latOverlap*100))
        self.windowThresholdVal.setValue(int(self.spectralData.roiWindowThreshold*100))
        self.minFreqVal.setValue(self.spectralData.transducerFreqBand[0]/1000000)
        self.maxFreqVal.setValue(self.spectralData.transducerFreqBand[1]/1000000)
        self.lowBandFreqVal.setValue(self.spectralData.analysisFreqBand[0]/1000000)
        self.upBandFreqVal.setValue(self.spectralData.analysisFreqBand[1]/1000000)
        self.samplingFreqVal.setValue(self.spectralData.samplingFrequency/1000000)

        self.imageDepthVal.setText(
            str(np.round(self.spectralData.depth, decimals=1))
        )
        self.imageWidthVal.setText(
            str(np.round(self.spectralData.width, decimals=1))
        )

    def singleRoiWindow(self):
        self.axOverlapVal.setValue(0)
        self.latOverlapVal.setValue(0)
        self.windowThresholdVal.setValue(50)

        mplPixWidth = max(self.spectralData.splineX) - min(
            self.spectralData.splineX
        )
        imPixWidth = mplPixWidth * self.spectralData.lateralRes
        mmWidth = self.spectralData.lateralRes * imPixWidth  # (mm/pixel)*pixels

        mplPixHeight = max(self.spectralData.splineY) - min(
            self.spectralData.splineY
        )
        imPixHeight = mplPixHeight * self.spectralData.axialRes
        mmHeight = self.spectralData.axialRes * imPixHeight  # (mm/pixel)*pixels

        self.axWinSizeVal.setValue(np.round(mmHeight, decimals=2))
        self.latWinSizeVal.setValue(np.round(mmWidth, decimals=2))

        # self.updateRoiSize()

    def updateRoiSize(self):
        if self.axWinSizeVal.value() > 0 and self.latWinSizeVal.value() > 0:
            self.axWavelengthRatioVal.setText(
                str(np.round(self.axWinSizeVal.value() / self.spectralData.waveLength, decimals=2))
            )
            self.latWavelengthRatioVal.setText(
                str(np.round(self.latWinSizeVal.value() / self.spectralData.waveLength, decimals=2))
            )

            self.maskCoverMesh.fill(0)
            axialRSize = self.axWinSizeVal.value()
            lateralRSize = self.latWinSizeVal.value()
            axialRes = self.spectralData.axialRes
            lateralRes = self.spectralData.lateralRes
            axialSize = round(axialRSize / axialRes)  # in pixels :: mm/(mm/pixel)
            lateralSize = round(lateralRSize / lateralRes)
            axialOverlap = self.axOverlapVal.value() / 100
            lateralOverlap = self.latOverlapVal.value() / 100

            xScale = self.spectralData.roiWidthScale / (self.spectralData.pixWidth)
            yScale = self.spectralData.roiDepthScale / (self.spectralData.pixDepth)
            x = self.spectralData.splineX / xScale
            y = self.spectralData.splineY / yScale

            # Some axial/lateral dims
            axialSize = round(axialRSize / axialRes)  # in pixels :: mm/(mm/pixel)
            lateralSize = round(lateralRSize / lateralRes)

            # Overlap fraction determines the incremental distance between ROIs
            axialIncrement = axialSize * (1 - axialOverlap)
            lateralIncrement = lateralSize * (1 - lateralOverlap)

            for x in np.arange(0, self.maskCoverMesh.shape[0], axialIncrement):
                ind = round(x)
                if ind < self.maskCoverMesh.shape[0]:
                    self.maskCoverMesh[ind - 2 : ind + 2, 0:] = [0, 255, 255, 255]

            for y in np.arange(0, self.maskCoverMesh.shape[1], lateralIncrement):
                ind = round(y)
                if ind < self.maskCoverMesh.shape[1]:
                    self.maskCoverMesh[0:, ind] = [0, 255, 255, 255]

            self.maskCoverMesh = np.require(self.maskCoverMesh, np.uint8, "C")
            self.bytesLineMesh, _ = self.maskCoverMesh[:, :, 0].strides
            self.qImgMesh = QImage(
                self.maskCoverMesh,
                self.maskCoverMesh.shape[1],
                self.maskCoverMesh.shape[0],
                self.bytesLineMesh,
                QImage.Format.Format_ARGB32,
            )

            self.previewFrameMesh.setPixmap(
                QPixmap.fromImage(self.qImgMesh).scaled(
                    self.widthScale, self.depthScale
                )
            )

    def plotRoiPreview(self):
        self.minX = min(self.spectralData.splineX)
        self.maxX = max(self.spectralData.splineX)
        self.minY = min(self.spectralData.splineY)
        self.maxY = max(self.spectralData.splineY)

        quotient = (self.maxX - self.minX) / (self.maxY - self.minY)
        if quotient > (341 / 231):
            self.widthScale = 341
            self.depthScale = int(self.widthScale / (
                (self.maxX - self.minX) / (self.maxY - self.minY)
            ))
        else:
            self.widthScale = int(231 * quotient)
            self.depthScale = 231

        self.xLen = round(self.maxX - self.minX)
        self.yLen = round(self.maxY - self.minY)

        self.xScale = self.spectralData.pixWidth / self.spectralData.roiWidthScale
        self.yScale = self.spectralData.pixDepth / self.spectralData.roiDepthScale
        self.xLenBmode = round(self.xLen * self.xScale)
        self.yLenBmode = round(self.yLen * self.yScale)
        self.minXBmode = round(self.minX * self.xScale)
        self.minYBmode = round(self.minY * self.yScale)
        endXBmode = min(self.minXBmode + self.xLenBmode, self.spectralData.pixWidth - 1)
        endYBmode = min(self.minYBmode + self.yLenBmode, self.spectralData.pixDepth - 1)
        self.imData = np.require(
            self.spectralData.finalBmode[self.minYBmode : endYBmode, self.minXBmode : endXBmode],
            np.uint8,
            "C",
        )
        self.arHeight = self.imData.shape[0]
        self.arWidth = self.imData.shape[1]

        self.bytesLine = self.imData.strides[0]

        self.maskCoverImg = np.zeros((self.yLen, self.xLen, 4))
        self.maskCoverMesh = np.zeros((self.yLenBmode, self.xLenBmode, 4))

        for i in range(len(self.spectralData.splineX)):
            self.maskCoverImg[
                max(round(self.spectralData.splineY[i] - self.minY - 1), 0) : max(
                    round(self.spectralData.splineY[i] - self.minY - 1), 0
                )
                + 2,
                max(round(self.spectralData.splineX[i] - self.minX - 1), 0) : max(
                    round(self.spectralData.splineX[i] - self.minX - 1), 0
                )
                + 2,
            ] = [255, 255, 0, 255]

        self.maskCoverImg = np.require(self.maskCoverImg, np.uint8, "C")
        self.bytesLineMask, _ = self.maskCoverImg[:, :, 0].strides
        self.qImgMask = QImage(
            self.maskCoverImg,
            self.maskCoverImg.shape[1],
            self.maskCoverImg.shape[0],
            self.bytesLineMask,
            QImage.Format.Format_ARGB32,
        )

        self.previewFrameMask.setPixmap(
            QPixmap.fromImage(self.qImgMask).scaled(self.widthScale, self.depthScale)
        )

        self.qIm = QImage(
            self.imData,
            self.arWidth,
            self.arHeight,
            self.bytesLine,
            QImage.Format.Format_RGB888,
        )
        self.previewFrame.setPixmap(
            QPixmap.fromImage(self.qIm).scaled(self.widthScale, self.depthScale)
        )

        self.updateRoiSize()
        self.axWinSizeVal.valueChanged.connect(self.updateRoiSize)
        self.latWinSizeVal.valueChanged.connect(self.updateRoiSize)
        self.axOverlapVal.valueChanged.connect(self.updateRoiSize)
        self.latOverlapVal.valueChanged.connect(self.updateRoiSize)

    def backToLastScreen(self):
        self.lastGui.spectralData = self.spectralData
        self.lastGui.show()
        self.hide()

    def setFilenameDisplays(self, imageName, phantomName):
        self.imagePathInput.setHidden(False)
        self.phantomPathInput.setHidden(False)
        self.imagePathInput.setText(imageName)
        self.phantomPathInput.setText(phantomName)

    def continueToRfAnalysis(self):
        self.spectralData.axWinSize = self.axWinSizeVal.value()
        self.spectralData.latWinSize = self.latWinSizeVal.value()
        self.spectralData.axOverlap = self.axOverlapVal.value() / 100
        self.spectralData.latOverlap = self.latOverlapVal.value() / 100
        self.spectralData.roiWindowThreshold = self.windowThresholdVal.value() / 100
        self.spectralData.transducerFreqBand = [self.minFreqVal.value() * 1000000, self.maxFreqVal.value() * 1000000] # Hz
        self.spectralData.samplingFrequency = self.samplingFreqVal.value() * 1000000  # Hz
        self.spectralData.analysisFreqBand = [self.lowBandFreqVal.value() * 1000000, self.upBandFreqVal.value() * 1000000] # Hz

        del self.rfAnalysisGUI
        self.rfAnalysisGUI = RfAnalysisGUI()
        self.rfAnalysisGUI.spectralData = self.spectralData
        self.rfAnalysisGUI.setFilenameDisplays(
            self.imagePathInput.text().split("/")[-1],
            self.phantomPathInput.text().split("/")[-1],
        )
        self.rfAnalysisGUI.completeSpectralAnalysis()
        self.rfAnalysisGUI.show()
        self.rfAnalysisGUI.lastGui = self
        self.hide()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    # selectWindow = QWidget()
    ui = AnalysisParamsGUI()
    # ui.selectImage.show()
    ui.show()
    sys.exit(app.exec_())
