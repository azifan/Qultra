from UtcTool2d.analysisParamsSelection_ui import *
from UtcTool2d.rfAnalysis_ui_helper import *
import os
from Utils.roiFuncs import *
from Utils.roiFuncs import roiWindowsGenerator

from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QImage, QPixmap

import platform
system = platform.system()


class AnalysisParamsGUI(Ui_analysisParams, QWidget):
    def __init__(self):
        # self.selectImage = QWidget()
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
        self.finalSplineX = None
        self.finalSplineY = None
        self.frame = None
        self.imArray = None
        self.dataFrame = None
        self.curPointsPlottedX = None
        self.curPointsPlottedY = None

        self.continueButton.clicked.connect(self.continueToRfAnalysis)
        self.backButton.clicked.connect(self.backToLastScreen)
        

    def updateRoiSize(self):

        if self.axWinSizeVal.value() > 0 and self.latWinSizeVal.value() > 0:

            self.axWavelengthRatioVal.setText(str(np.round(self.axWinSizeVal.value()/self.waveLength, decimals=2)))
            self.latWavelengthRatioVal.setText(str(np.round(self.latWinSizeVal.value()/self.waveLength, decimals=2)))

            self.maskCoverMesh.fill(0)
            axialRSize = self.axWinSizeVal.value()
            lateralRSize = self.latWinSizeVal.value()
            axialRes = self.lastGui.imgInfoStruct.axialRes
            lateralRes = self.lastGui.imgInfoStruct.lateralRes
            axialNum = self.lastGui.imgDataStruct.depthPixels
            lateralNum = self.lastGui.imgDataStruct.widthPixels
            axialSize = round(axialRSize/axialRes) # in pixels :: mm/(mm/pixel)
            lateralSize = round(lateralRSize/lateralRes)
            axialOverlap = self.axOverlapVal.value()/100
            lateralOverlap = self.latOverlapVal.value()/100

            xScale = 721/(self.lastGui.imgDataStruct.widthPixels)
            yScale = 501/(self.lastGui.imgDataStruct.depthPixels)
            x = self.finalSplineX/xScale
            y = self.finalSplineY/yScale

            # Some axial/lateral dims
            axialSize = round(axialRSize/axialRes) # in pixels :: mm/(mm/pixel)
            lateralSize = round(lateralRSize/lateralRes)

            # Overlap fraction determines the incremental distance between ROIs
            axialIncrement = axialSize * (1-axialOverlap)
            lateralIncrement = lateralSize * (1-lateralOverlap)

            for x in np.arange(self.padding/self.xScale, self.maskCoverMesh.shape[0], axialIncrement):
                ind = round(x)
                if ind < self.maskCoverMesh.shape[0]:
                    self.maskCoverMesh[ind-2:ind+2, 0:] = [0, 255, 255, 255]

            for y in np.arange(self.padding/self.yScale, self.maskCoverMesh.shape[1], lateralIncrement):
                ind = round(y)
                if ind < self.maskCoverMesh.shape[1]:
                    self.maskCoverMesh[0:, ind] = [0, 255, 255, 255]

            self.maskCoverMesh = np.require(self.maskCoverMesh, np.uint8, 'C')
            self.bytesLineMesh, _ = self.maskCoverMesh[:,:,0].strides
            self.qImgMesh = QImage(self.maskCoverMesh, self.maskCoverMesh.shape[1], self.maskCoverMesh.shape[0], self.bytesLineMesh, QImage.Format_ARGB32)

            self.previewFrameMesh.setPixmap(QPixmap.fromImage(self.qImgMesh).scaled(self.widthScale, self.depthScale))

    def plotRoiPreview(self):
        self.padding = 0 # can vary
        self.waveLength = self.axWinSizeVal.value()/10
        # 720 and 500 vals come from frame dims in ROI Selection page

        self.minX = max(min(self.finalSplineX) - self.padding, 0)
        self.maxX = min(max(self.finalSplineX) + self.padding, 720)
        self.minY = max(min(self.finalSplineY) - self.padding, 0)
        self.maxY = min(max(self.finalSplineY) + self.padding, 500)

        quotient = (self.maxX - self.minX) / (self.maxY - self.minY)
        if quotient > (341/231):
            self.widthScale = 341
            self.depthScale = self.widthScale / ((self.maxX - self.minX)/(self.maxY - self.minY))
        else:
            self.widthScale = 231 * quotient
            self.depthScale = 231

        self.xLen = round(self.maxX - self.minX)
        self.yLen = round(self.maxY - self.minY)

        if self.frame is not None:
            self.xScale = self.imArray.shape[2]/721
            self.yScale = self.imArray.shape[1]/501
            self.xLenBmode = round(self.xLen*self.xScale)
            self.yLenBmode = round(self.yLen*self.yScale)
            self.minXBmode = round(self.minX*self.xScale)
            self.minYBmode = round(self.minY*self.yScale)
            self.arHeight = min(self.minYBmode+self.yLenBmode, self.imArray.shape[1] - 1) - self.minYBmode
            self.arWidth = min(self.minXBmode+self.xLenBmode, self.imArray.shape[2] - 1) - self.minXBmode
            self.imData = np.array(self.imArray[self.frame, self.minYBmode:min(self.minYBmode+self.yLenBmode, self.imArray.shape[1] - 1), \
                                                self.minXBmode:min(self.minXBmode+self.xLenBmode, self.imArray.shape[2] - 1)]).reshape(self.arHeight, self.arWidth)
            self.imData = np.require(self.imData, np.uint8, 'C')
        else:
            self.xScale = self.imArray.shape[1]/721
            self.yScale = self.imArray.shape[0]/501
            self.xLenBmode = round(self.xLen*self.xScale)
            self.yLenBmode = round(self.yLen*self.yScale)
            self.minXBmode = round(self.minX*self.xScale)
            self.minYBmode = round(self.minY*self.yScale)
            endXBmode = min(self.minXBmode+self.xLenBmode, self.imArray.shape[1] - 1)
            endYBmode = min(self.minYBmode+self.yLenBmode, self.imArray.shape[0] - 1)
            self.imData = np.require(self.imArray[self.minYBmode:endYBmode, \
                                                  self.minXBmode:endXBmode],np.uint8,'C')
            self.arHeight = self.imData.shape[0]
            self.arWidth = self.imData.shape[1]

        self.bytesLine = self.imData.strides[0]

        self.maskCoverImg = np.zeros((self.yLen, self.xLen, 4))
        self.maskCoverMesh = np.zeros((self.yLenBmode, self.xLenBmode, 4))

        for i in range(len(self.finalSplineX)):
            self.maskCoverImg[max(round(self.finalSplineY[i] - self.minY - 1), 0):max(round(self.finalSplineY[i] - self.minY - 1), 0)+2, \
                              max(round(self.finalSplineX[i] - self.minX - 1), 0):max(round(self.finalSplineX[i] - self.minX - 1), 0)+2] = [255, 255, 0, 255]

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
        self.lastGui.dataFrame = self.dataFrame
        self.lastGui.show()
        self.hide()

    def setFilenameDisplays(self, imageName, phantomName):
        self.imagePathInput.setHidden(False)
        self.phantomPathInput.setHidden(False)
        self.imagePathInput.setText(imageName)
        self.phantomPathInput.setText(phantomName)

    def continueToRfAnalysis(self):
        del self.rfAnalysisGUI
        self.rfAnalysisGUI = RfAnalysisGUI(self.finalSplineX, self.finalSplineY)
        self.rfAnalysisGUI.imgDataStruct = self.lastGui.imgDataStruct
        self.rfAnalysisGUI.imgInfoStruct = self.lastGui.imgInfoStruct
        self.rfAnalysisGUI.refDataStruct = self.lastGui.refDataStruct
        self.rfAnalysisGUI.refInfoStruct = self.lastGui.refInfoStruct
        self.rfAnalysisGUI.curPointsPlottedX = self.curPointsPlottedX
        self.rfAnalysisGUI.curPointsPlottedY = self.curPointsPlottedY
        self.rfAnalysisGUI.dataFrame = self.dataFrame
        self.rfAnalysisGUI.frame = self.frame
        self.rfAnalysisGUI.axialWinSize = self.axWinSizeVal.value()
        self.rfAnalysisGUI.lateralWinSize = self.latWinSizeVal.value()
        self.rfAnalysisGUI.axialOverlap = self.axOverlapVal.value()/100
        self.rfAnalysisGUI.lateralOverlap = self.latOverlapVal.value()/100
        self.rfAnalysisGUI.windowThreshold = self.windowThresholdVal.value()
        self.rfAnalysisGUI.minFrequency = self.minFreqVal.value()*1000000 #Hz
        self.rfAnalysisGUI.maxFrequency = self.maxFreqVal.value()*1000000 #Hz
        self.rfAnalysisGUI.samplingFreq = self.samplingFreqVal.value()*1000000 # Hz
        self.rfAnalysisGUI.upBandFreq = self.upBandFreqVal.value()*1000000 #Hz
        self.rfAnalysisGUI.lowBandFreq = self.lowBandFreqVal.value()*1000000 #Hz
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