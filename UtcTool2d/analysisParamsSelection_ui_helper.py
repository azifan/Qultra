from UtcTool2d.analysisParamsSelection_ui import *
from UtcTool2d.rfAnalysis_ui_helper import *
import os
from Utils.roiFuncs import *

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

    def plotRoiPreview(self):
        padding = 10 # can vary
        # 720 and 500 vals come from frame dims in ROI Selection page

        minX = max(min(self.finalSplineX) - padding, 0)
        maxX = min(max(self.finalSplineX) + padding, 720)
        minY = max(min(self.finalSplineY) - padding, 0)
        maxY = min(max(self.finalSplineY) + padding, 500)

        xLen = round(maxX - minX)
        yLen = round(maxY - minY)

        if self.frame is not None:
            xLenBmode = round(xLen/721*self.imArray.shape[2])
            yLenBmode = round(yLen/501*self.imArray.shape[1])
            minXBmode = round(minX/721*self.imArray.shape[2])
            minYBmode = round(minY/501*self.imArray.shape[1])
            self.imData = np.array(self.imArray[self.frame, minYBmode:min(minYBmode+yLenBmode, self.imArray.shape[1] - 1), \
                                                minXBmode:min(minXBmode+xLenBmode, self.imArray.shape[2] - 1)]).reshape(self.arHeight, self.arWidth)
            self.imData = np.require(self.imData, np.uint8, 'C')
        else:
            xLenBmode = round(xLen/721*self.imArray.shape[1])
            yLenBmode = round(yLen/501*self.imArray.shape[0])
            minXBmode = round(minX/721*self.imArray.shape[1])
            minYBmode = round(minY/501*self.imArray.shape[0])
            endXBmode = min(minXBmode+xLenBmode, self.imArray.shape[1] - 1)
            endYBmode = min(minYBmode+yLenBmode, self.imArray.shape[0] - 1)
            self.imData = np.require(self.imArray[minYBmode:endYBmode, \
                                                  minXBmode:endXBmode],np.uint8,'C')

        self.bytesLine = self.imData.strides[0]
        self.arHeight = self.imData.shape[0]
        self.arWidth = self.imData.shape[1]

        self.maskCoverImg = np.zeros((yLen, xLen, 4))
        for i in range(len(self.finalSplineX)):
            self.maskCoverImg[max(round(self.finalSplineY[i] - minY - 1), 0):max(round(self.finalSplineY[i] - minY - 1), 0)+2, \
                              max(round(self.finalSplineX[i] - minX - 1), 0):max(round(self.finalSplineX[i] - minX - 1), 0)+2] = [255, 255, 0, 255]

        self.maskCoverImg = np.require(self.maskCoverImg, np.uint8, 'C')
        self.bytesLineMask, _ = self.maskCoverImg[:,:,0].strides
        self.qImgMask = QImage(self.maskCoverImg, self.maskCoverImg.shape[1], self.maskCoverImg.shape[0], self.bytesLineMask, QImage.Format_ARGB32)

        self.previewFrameMask.setPixmap(QPixmap.fromImage(self.qImgMask).scaled(341, 231))

        self.qIm = QImage(self.imData, self.arWidth, self.arHeight, self.bytesLine, QImage.Format_Grayscale8)
        self.previewFrame.setPixmap(QPixmap.fromImage(self.qIm).scaled(341, 231))


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