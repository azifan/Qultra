from UtcTool2dIQ.analysisParamsSelection_ui import *
from UtcTool2dIQ.rfAnalysis_ui_helper import *
import os
from Utils.roiFuncs import *

from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QImage, QPixmap

import platform

system = platform.system()

class AnalysisParamsGUI(Ui_analysisParams, QWidget):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        if system == 'Windows':
            self.roiSidebarLabel.setStyleSheet("""QLabel { 
                font-size: 18px; 
                color: rgb(255, 255, 255); 
                background-color: rgba(255, 255, 255, 0); 
                border: 0px; 
                font-weight: bold; 
            }""")
            self.imageSelectionLabelSidebar.setStyleSheet("""QLabel {
                font-size: 18px;
                color: rgb(255, 255, 255);
                background-color: rgba(255, 255, 255, 0);
                border: 0px;
                font-weight: bold;
            }""")
            self.imageLabel.setStyleSheet("""QLabel {
                font-size: 13px;
                color: rgb(255, 255, 255);
                background-color: rgba(255, 255, 255, 0);
                border: 0px;
                font-weight: bold;
            }""")
            self.phantomLabel.setStyleSheet("""QLabel {
                font-size: 13px;
                color: rgb(255, 255, 255);
                background-color: rgba(255, 255, 255, 0);
                border: 0px;
                font-weight: bold;
            }""")
            self.imagePathInput.setStyleSheet("""QLabel {
                font-size: 11px;
                color: rgb(255, 255, 255);
                background-color: rgba(255, 255, 255, 0);
                border: 0px;
            }""")
            self.phantomPathInput.setStyleSheet("""QLabel {
                font-size: 11px;
                color: rgb(255, 255, 255);
                background-color: rgba(255, 255, 255, 0);
                border: 0px;
            }""")
            self.analysisParamsLabel.setStyleSheet("""QLabel {
                font-size: 18px;
                color: rgb(255, 255, 255);
                background-color: rgba(255, 255, 255, 0);
                border: 0px;
                font-weight:bold;
            }""")
            self.rfAnalysisLabel.setStyleSheet("""QLabel {
                font-size: 18px;
                color: rgb(255, 255, 255);
                background-color: rgba(255, 255, 255, 0);
                border: 0px;
                font-weight:bold;
            }""")
            self.exportResultsLabel.setStyleSheet("""QLabel {
                font-size: 18px;
                color: rgb(255, 255, 255);
                background-color: rgba(255, 255, 255, 0);
                border: 0px;
                font-weight:bold;
            }""")
            self.imageDepthLabel.setStyleSheet("""QLabel {
                color: white;
                background-color: rgba(0,0,0,0);
                font-size: 18px;
            }""")
            self.imageWidthLabel.setStyleSheet("""QLabel {
                color: white;
                background-color: rgba(0,0,0,0);
                font-size: 18px;
            }""")
            self.imageDepthVal.setStyleSheet("""QLabel {
                color: white;
                background-color: rgba(0,0,0,0);
                font-size: 18px;
            }""")
            self.imageWidthVal.setStyleSheet("""QLabel {
                color: white;
                background-color: rgba(0,0,0,0);
                font-size: 18px;
            }""")
            self.axWinSizeLabel.setStyleSheet("""QLabel {
                color: white;
                background-color: rgba(0,0,0,0);
                font-size: 18px;
            }""")
            self.latWinSizeLabel.setStyleSheet("""QLabel {
                color: white;
                background-color: rgba(0,0,0,0);
                font-size: 18px;
            }""")
            self.axOverlapLabel.setStyleSheet("""QLabel {
                color: white;
                background-color: rgba(0,0,0,0);
                font-size: 18px;
            }""")
            self.latOverlapLabel.setStyleSheet("""QLabel {
                color: white;
                background-color: rgba(0,0,0,0);
                font-size: 18px;
            }""")
            self.windowThresholdLabel.setStyleSheet("""QLabel {
                color: white;
                background-color: rgba(0,0,0,0);
                font-size: 18px;
            }""")
            self.minFreqLabel.setStyleSheet("""QLabel {
                color: white;
                background-color: rgba(0,0,0,0);
                font-size: 18px;
            }""")
            self.maxFreqLabel.setStyleSheet("""QLabel {
                color: white;
                background-color: rgba(0,0,0,0);
                font-size: 18px;
            }""")
            self.lowBandFreqLabel.setStyleSheet("""QLabel {
                color: white;
                background-color: rgba(0,0,0,0);
                font-size: 18px;
            }""")
            self.upBandFreqLabel.setStyleSheet("""QLabel {
                color: white;
                background-color: rgba(0,0,0,0);
                font-size: 18px;
            }""")
            self.samplingFreqLabel.setStyleSheet("""QLabel {
                color: white;
                background-color: rgba(0,0,0,0);
                font-size: 18px;
            }""")

        self.rfAnalysisGUI = None
        self.lastGui = None
        self.AnalysisInfo = None

        self.continueButton.clicked.connect(self.continueToRfAnalysis)
        self.backButton.clicked.connect(self.backToLastScreen)
        self.singleRoiWindowButton.clicked.connect(self.singleRoiWindow)

    def singleRoiWindow(self):
        self.axOverlapVal.setValue(0)
        self.latOverlapVal.setValue(0)
        self.windowThresholdVal.setValue(50)

        xScale = self.AnalysisInfo.roiWidthScale/(self.AnalysisInfo.pixWidth)
        mplPixWidth = max(self.AnalysisInfo.finalSplineX) - min(self.AnalysisInfo.finalSplineX)
        imPixWidth = mplPixWidth / xScale
        mmWidth = self.AnalysisInfo.lateralRes * imPixWidth # (mm/pixel)*pixels

        yScale = self.AnalysisInfo.roiDepthScale/(self.AnalysisInfo.pixDepth)
        mplPixHeight = max(self.AnalysisInfo.finalSplineY) - min(self.AnalysisInfo.finalSplineY)
        imPixHeight = mplPixHeight / yScale
        mmHeight = self.AnalysisInfo.axialRes * imPixHeight # (mm/pixel)*pixels

        self.axWinSizeVal.setValue(np.round(mmHeight, decimals=2))
        self.latWinSizeVal.setValue(np.round(mmWidth, decimals=2))

        self.updateRoiSize()


    def updateRoiSize(self):

        if self.axWinSizeVal.value() > 0 and self.latWinSizeVal.value() > 0:

            self.axWavelengthRatioVal.setText(str(np.round(self.axWinSizeVal.value()/self.waveLength, decimals=2)))
            self.latWavelengthRatioVal.setText(str(np.round(self.latWinSizeVal.value()/self.waveLength, decimals=2)))

            self.maskCoverMesh.fill(0)
            axialRSize = self.axWinSizeVal.value()
            lateralRSize = self.latWinSizeVal.value()
            axialRes = self.AnalysisInfo.axialRes
            lateralRes = self.AnalysisInfo.lateralRes
            axialSize = round(axialRSize/axialRes) # in pixels :: mm/(mm/pixel)
            lateralSize = round(lateralRSize/lateralRes)
            axialOverlap = self.axOverlapVal.value()/100
            lateralOverlap = self.latOverlapVal.value()/100

            xScale = self.AnalysisInfo.roiWidthScale/(self.AnalysisInfo.pixWidth)
            yScale = self.AnalysisInfo.roiDepthScale/(self.AnalysisInfo.pixDepth)
            x = self.AnalysisInfo.finalSplineX/xScale
            y = self.AnalysisInfo.finalSplineY/yScale

            # Some axial/lateral dims
            axialSize = round(axialRSize/axialRes) # in pixels :: mm/(mm/pixel)
            lateralSize = round(lateralRSize/lateralRes)

            # Overlap fraction determines the incremental distance between ROIs
            axialIncrement = axialSize * (1-axialOverlap)
            lateralIncrement = lateralSize * (1-lateralOverlap)

            for x in np.arange(0, self.maskCoverMesh.shape[0], axialIncrement):
                ind = round(x)
                if ind < self.maskCoverMesh.shape[0]:
                    self.maskCoverMesh[ind-2:ind+2, 0:] = [0, 255, 255, 255]

            for y in np.arange(0, self.maskCoverMesh.shape[1], lateralIncrement):
                ind = round(y)
                if ind < self.maskCoverMesh.shape[1]:
                    self.maskCoverMesh[0:, ind] = [0, 255, 255, 255]

            self.maskCoverMesh = np.require(self.maskCoverMesh, np.uint8, 'C')
            self.bytesLineMesh, _ = self.maskCoverMesh[:,:,0].strides
            self.qImgMesh = QImage(self.maskCoverMesh, self.maskCoverMesh.shape[1], self.maskCoverMesh.shape[0], self.bytesLineMesh, QImage.Format_ARGB32)

            self.previewFrameMesh.setPixmap(QPixmap.fromImage(self.qImgMesh).scaled(self.widthScale, self.depthScale))

    def plotRoiPreview(self):
        self.waveLength = self.axWinSizeVal.value()/10

        self.minX = min(self.AnalysisInfo.finalSplineX)
        self.maxX = max(self.AnalysisInfo.finalSplineX)
        self.minY = min(self.AnalysisInfo.finalSplineY)
        self.maxY = max(self.AnalysisInfo.finalSplineY)

        quotient = (self.maxX - self.minX) / (self.maxY - self.minY)
        if quotient > (341/231):
            self.widthScale = 341
            self.depthScale = self.widthScale / ((self.maxX - self.minX)/(self.maxY - self.minY))
        else:
            self.widthScale = 231 * quotient
            self.depthScale = 231

        self.xLen = round(self.maxX - self.minX)
        self.yLen = round(self.maxY - self.minY)

        self.xScale = self.AnalysisInfo.pixWidth/self.AnalysisInfo.roiWidthScale
        self.yScale = self.AnalysisInfo.pixDepth/self.AnalysisInfo.roiDepthScale
        self.xLenBmode = round(self.xLen*self.xScale)
        self.yLenBmode = round(self.yLen*self.yScale)
        self.minXBmode = round(self.minX*self.xScale) 
        self.minYBmode = round(self.minY*self.yScale) 
        endXBmode = min(self.minXBmode+self.xLenBmode, self.AnalysisInfo.pixWidth - 1)
        endYBmode = min(self.minYBmode+self.yLenBmode, self.AnalysisInfo.pixDepth - 1)
        flippedArray = np.flipud(self.AnalysisInfo.imArray)
        self.imData = np.require(flippedArray[self.minYBmode:endYBmode, \
                                                self.minXBmode:endXBmode],np.uint8,'C')
        self.arHeight = self.imData.shape[0]
        self.arWidth = self.imData.shape[1]

        self.bytesLine = self.imData.strides[0]

        self.maskCoverImg = np.zeros((self.yLen, self.xLen, 4))
        self.maskCoverMesh = np.zeros((self.yLenBmode, self.xLenBmode, 4))

        for i in range(len(self.AnalysisInfo.finalSplineX)):
            self.maskCoverImg[max(round(self.AnalysisInfo.finalSplineY[i] - self.minY - 1), 0):max(round(self.AnalysisInfo.finalSplineY[i] - self.minY - 1), 0)+2, \
                              max(round(self.AnalysisInfo.finalSplineX[i] - self.minX - 1), 0):max(round(self.AnalysisInfo.finalSplineX[i] - self.minX - 1), 0)+2] = [255, 255, 0, 255]

        self.maskCoverImg = np.require(self.maskCoverImg, np.uint8, 'C')
        self.bytesLineMask, _ = self.maskCoverImg[:,:,0].strides
        self.qImgMask = QImage(self.maskCoverImg, self.maskCoverImg.shape[1], self.maskCoverImg.shape[0], self.bytesLineMask, QImage.Format_ARGB32)

        self.previewFrameMask.setPixmap(QPixmap.fromImage(self.qImgMask).scaled(self.widthScale, self.depthScale))

        self.qIm = QImage(self.imData, self.arWidth, self.arHeight, self.bytesLine, QImage.Format_Grayscale8)
        self.previewFrame.setPixmap(QPixmap.fromImage(self.qIm).scaled(self.widthScale, self.depthScale))

        self.updateRoiSize()
        self.axWinSizeVal.valueChanged.connect(self.updateRoiSize)
        self.latWinSizeVal.valueChanged.connect(self.updateRoiSize)
        self.axOverlapVal.valueChanged.connect(self.updateRoiSize)
        self.latOverlapVal.valueChanged.connect(self.updateRoiSize)

    def backToLastScreen(self):
        self.lastGui.AnalysisInfo.dataFrame = self.AnalysisInfo.dataFrame
        self.lastGui.show()
        self.hide()

    def setFilenameDisplays(self, imageName, phantomName):
        self.imagePathInput.setHidden(False)
        self.phantomPathInput.setHidden(False)
        self.imagePathInput.setText(imageName)
        self.phantomPathInput.setText(phantomName)

    def continueToRfAnalysis(self):
        self.AnalysisInfo.axialWinSize = self.axWinSizeVal.value()
        self.AnalysisInfo.lateralWinSize = self.latWinSizeVal.value()
        self.AnalysisInfo.axialOverlap = self.axOverlapVal.value()/100
        self.AnalysisInfo.lateralOverlap = self.latOverlapVal.value()/100
        self.AnalysisInfo.threshold = self.windowThresholdVal.value()
        self.AnalysisInfo.minFrequency = self.minFreqVal.value()*1000000 #Hz
        self.AnalysisInfo.maxFrequency = self.maxFreqVal.value()*1000000 #Hz
        self.AnalysisInfo.samplingFreq = self.samplingFreqVal.value()*1000000 #Hz
        self.AnalysisInfo.lowBandFreq = self.lowBandFreqVal.value()*1000000 #Hz
        self.AnalysisInfo.upBandFreq = self.upBandFreqVal.value()*1000000 #Hz

        del self.rfAnalysisGUI
        self.rfAnalysisGUI = RfAnalysisGUI()
        self.rfAnalysisGUI.AnalysisInfo = self.AnalysisInfo
        self.rfAnalysisGUI.editImageDisplayGUI.contrastVal.setValue(self.lastGui.editImageDisplayGUI.contrastVal.value())
        self.rfAnalysisGUI.editImageDisplayGUI.brightnessVal.setValue(self.lastGui.editImageDisplayGUI.brightnessVal.value())
        self.rfAnalysisGUI.editImageDisplayGUI.sharpnessVal.setValue(self.lastGui.editImageDisplayGUI.sharpnessVal.value())
        self.rfAnalysisGUI.editImageDisplayGUI.contrastVal.valueChanged.connect(self.lastGui.analysisParamsGUI.rfAnalysisGUI.changeContrast)
        self.rfAnalysisGUI.editImageDisplayGUI.brightnessVal.valueChanged.connect(self.rfAnalysisGUI.changeBrightness)    
        self.rfAnalysisGUI.editImageDisplayGUI.sharpnessVal.valueChanged.connect(self.rfAnalysisGUI.changeSharpness)
        self.rfAnalysisGUI.setFilenameDisplays(self.imagePathInput.text().split('/')[-1], self.phantomPathInput.text().split('/')[-1])
        self.rfAnalysisGUI.displayROIWindows()
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