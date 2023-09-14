from UtcTool2d.roiSelection_ui import *
from UtcTool2d.editImageDisplay_ui_helper import *
from UtcTool2d.analysisParamsSelection_ui_helper import *
from UtcTool2d.loadRoi_ui_helper import *
import Parsers.philipsMatParser as matParser
import Parsers.siemensRfdParser as rfdParser
import Parsers.terasonRfParser as tera
from Parsers.philipsRfParser import main_parser_stanford

import pydicom
import os
import numpy as np
from PIL import Image, ImageEnhance
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib
import scipy.interpolate as interpolate
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPixmap, QPainter, QImage
from PyQt5.QtCore import QLine, Qt

import platform
system = platform.system()


class RoiSelectionGUI(QWidget, Ui_constructRoi):
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

        self.curPointsPlottedX = []
        self.curPointsPlottedY = []
        self.oldSpline = []
        self.multipleFrames = False
        self.imagePathInput.setHidden(True)
        self.phantomPathInput.setHidden(True)
        self.ofFramesLabel.setHidden(True)
        self.curFrameLabel.setHidden(True)
        self.totalFramesLabel.setHidden(True)
        self.curFrameSlider.setHidden(True)
        self.drawRoiButton.setHidden(True)
        self.closeRoiButton.setHidden(True)
        self.undoLastPtButton.setHidden(True)
        self.redrawRoiButton.setHidden(True)
        self.acceptRoiButton.setHidden(True)
        self.undoLoadedRoiButton.setHidden(True)
        self.acceptLoadedRoiButton.setHidden(True)
        self.acceptLoadedRoiButton.clicked.connect(self.acceptROI)
        self.undoLoadedRoiButton.clicked.connect(self.undoRoiLoad)

        self.loadRoiGUI = LoadRoiGUI()

        self.editImageDisplayButton.setHidden(True)

        self.imCoverPixmap = QPixmap(721, 501)
        self.imCoverPixmap.fill(Qt.transparent)
        self.imCoverFrame.setPixmap(self.imCoverPixmap)

        self.lastGui = None
        self.imArray = None
        self.axOverlapVal = None
        self.latOverlapVal = None
        self.minFreqVal = None
        self.maxFreqVal = None
        self.startDepthVal = None
        self.endDepthVal = None
        self.clipFactorVal = None
        self.samplingFreqVal = None
        self.analysisParamsGUI = None
        self.maskCoverImg = None
        self.dataFrame = None

        self.scatteredPoints = []
        
        self.undoLastPtButton.clicked.connect(self.undoLastPt)
        self.closeRoiButton.clicked.connect(self.closeInterpolation)
        self.redrawRoiButton.clicked.connect(self.undoLastRoi)
        self.acceptRoiButton.clicked.connect(self.acceptROI)
        self.backButton.clicked.connect(self.backToLastScreen)
        self.newRoiButton.clicked.connect(self.drawNewRoi)
        self.loadRoiButton.clicked.connect(self.openLoadRoiWindow)
    
    def undoRoiLoad(self):
        self.undoLoadedRoiButton.setHidden(True)
        self.acceptLoadedRoiButton.setHidden(True)
        self.loadRoiButton.setHidden(False)
        self.newRoiButton.setHidden(False)

        self.undoLastRoi()

    def openLoadRoiWindow(self):
        self.loadRoiGUI.chooseRoiGUI = self
        self.hide()
        self.loadRoiGUI.show()

    def drawNewRoi(self):
        self.newRoiButton.setHidden(True)
        self.loadRoiButton.setHidden(True)
        self.drawRoiButton.setHidden(False)
        self.undoLastPtButton.setHidden(False)
        self.closeRoiButton.setHidden(False)
        self.acceptRoiButton.setHidden(False)

    def backToLastScreen(self):
        self.lastGui.dataFrame = self.dataFrame
        self.lastGui.show()
        self.hide()

    def mousePressEvent(self,event):
        self.xCur = event.x()
        self.yCur = event.y()
        if self.drawRoiButton.isChecked():
            # Plot ROI points
            if self.xCur < self.xBorderMax and self.xCur > self.xBorderMin and self.yCur < self.yBorderMax and self.yCur > self.yBorderMin:
                plotX = self.xCur - 401
                plotY = self.yCur - 171
            else:
                return
            self.curPointsPlottedX.append(plotX)
            self.curPointsPlottedY.append(plotY)
            self.updateSpline()

    def updateSpline(self):
        self.maskCoverImg.fill(0)
        if len(self.curPointsPlottedX) > 0:            
            if len(self.curPointsPlottedX) > 1:
                xSpline, ySpline = calculateSpline(self.curPointsPlottedX, self.curPointsPlottedY)
                spline = [(int(xSpline[i]), int(ySpline[i])) for i in range(len(xSpline))]
                spline = np.array([*set(spline)])
                xSpline, ySpline = np.transpose(spline)
                xSpline = np.clip(xSpline, a_min=round(self.xBorderMin - 400)+1, a_max=720 + round(self.xBorderMax - 1121))
                ySpline = np.clip(ySpline, a_min=round(self.yBorderMin - 170)+1, a_max=500 + round(self.yBorderMax - 671))
                for i in range(len(xSpline)):
                    self.maskCoverImg[ySpline[i]-1:ySpline[i]+2, xSpline[i]-1:xSpline[i]+2] = [255, 255, 0, 255]

            for i in range(len(self.curPointsPlottedX)):
                self.maskCoverImg[self.curPointsPlottedY[i]-2:self.curPointsPlottedY[i]+3, \
                                    self.curPointsPlottedX[i]-2:self.curPointsPlottedX[i]+3] = [0,0,255, 255]

        self.plotOnCanvas()
        # self.updateCrosshair()

    def mouseMoveEvent(self, event):
        self.xCur = event.x()
        self.yCur = event.y()
        # self.updateCrosshair()

    # def updateCrosshair(self):
    #     if self.xCur < 1121 and self.xCur > 400 and self.yCur < 671 and self.yCur > 170:
    #         plotX = self.xCur - 401
    #     else:
    #         return
        
    #     plotY = self.yCur - 171
    #     self.imCoverFrame.pixmap().fill(Qt.transparent)
    #     painter = QPainter(self.imCoverFrame.pixmap())
    #     painter.setPen(Qt.yellow)
    #     bmodeVertLine = QLine(plotX, 0, plotX, 501)
    #     bmodeLatLine = QLine(0, plotY, 721, plotY)
    #     painter.drawLines([bmodeVertLine, bmodeLatLine])
    #     painter.end()
    #     self.update()

    def setFilenameDisplays(self, imageName, phantomName):
        self.imagePathInput.setHidden(False)
        self.phantomPathInput.setHidden(False)
        self.imagePathInput.setText(imageName)
        self.phantomPathInput.setText(phantomName)
    
    def plotOnCanvas(self): # Plot current image on GUI
        if self.multipleFrames:
            self.imData = np.array(self.imArray[self.frame]).reshape(self.arHeight, self.arWidth)
        self.imData = np.require(self.imData,np.uint8,'C')
        self.bytesLine = self.imData.strides[0]
        self.arHeight = self.imData.shape[0]
        self.arWidth = self.imData.shape[1]

        self.maskCoverImg = np.require(self.maskCoverImg, np.uint8, 'C')
        self.bytesLineMask, _ = self.maskCoverImg[:,:,0].strides
        self.qImgMask = QImage(self.maskCoverImg, self.maskCoverImg.shape[1], self.maskCoverImg.shape[0], self.bytesLineMask, QImage.Format_ARGB32)

        self.imMaskFrame.setPixmap(QPixmap.fromImage(self.qImgMask).scaled(721, 501))

        self.qIm = QImage(self.imData, self.arWidth, self.arHeight, self.bytesLine, QImage.Format_Grayscale8)
        self.imDisplayFrame.setPixmap(QPixmap.fromImage(self.qIm).scaled(self.widthScale, self.depthScale))

    def openPhilipsImage(self, imageFilePath, phantomFilePath):
        tmpLocation = imageFilePath.split("/")
        dataFileName = tmpLocation[-1]
        dataFileLocation = imageFilePath[:len(imageFilePath)-len(dataFileName)]
        tmpPhantLocation = phantomFilePath.split("/")
        phantFileName = tmpPhantLocation[-1]
        phantFileLocation = phantomFilePath[:len(phantomFilePath)-len(phantFileName)]
        if dataFileName[-3:] == ".rf":
            dataFile = open(imageFilePath, 'rb')
            datasig = list(dataFile.read(8))
            if datasig != [0,0,0,0,255,255,0,0]: # Philips signature parameters
                # self.invalidPath.setText("Data and Phantom files are both invalid.\nPlease use Philips .rf files.")
                return
            elif datasig != [0,0,0,0,255,255,0,0]:
                # self.invalidPath.setText("Invalid phantom file.\nPlease use Philips .rf files.")
                return
            else: # Display Philips image and assign relevant default analysis
                main_parser_stanford(imageFilePath) # parse image filee

                dataFileName = str(dataFileLocation[:-3]+'.mat')
        if phantFileName[-3:] == ".rf": # Check binary signatures at start of .rf files
            phantFile = open(phantomFilePath, 'rb')
            phantsig = list(phantFile.read(8))
            if phantsig != [0,0,0,0,255,255,0,0]: # Philips signature parameters
                # self.invalidPath.setText("Data and Phantom files are both invalid.\nPlease use Philips .rf files.")
                return
            elif phantsig != [0,0,0,0,255,255,0,0]:
                # self.invalidPath.setText("Invalid phantom file.\nPlease use Philips .rf files.")
                return
            else: # Display Philips image and assign relevant default analysis
                main_parser_stanford(imageFilePath) # parse image filee

                phantFileName = str(phantFileName[:-3]+'.mat')

        # Display Philips image and assign relevant default analysis params
        self.frame = None
        self.imArray, self.imgDataStruct, self.imgInfoStruct, self.refDataStruct, self.refInfoStruct = matParser.getImage(dataFileName, dataFileLocation, phantFileName, phantFileLocation, self.frame)
        self.arHeight = self.imArray.shape[0]
        self.arWidth = self.imArray.shape[1]
        self.imData = np.array(self.imArray)
        self.imData = np.require(self.imData,np.uint8,'C')
        self.maskCoverImg = np.zeros([501, 721, 4]) # Hard-coded values match size of frame on GUI
        self.bytesLine = self.imData.strides[0]

        quotient = self.imgInfoStruct.width / self.imgInfoStruct.depth
        if quotient > (721/501):
            self.widthScale = 721
            self.depthScale = self.widthScale / (self.imgInfoStruct.width/self.imgInfoStruct.depth)
        else:
            self.widthScale = 501 * quotient
            self.depthScale = 501
        self.yBorderMin = 170 + ((501 - self.depthScale)/2)
        self.yBorderMax = 671 - ((501 - self.depthScale)/2)
        self.xBorderMin = 400 + ((721 - self.widthScale)/2)
        self.xBorderMax = 1121 - ((721 - self.widthScale)/2)

        self.qIm = QImage(self.imData, self.arWidth, self.arHeight, self.bytesLine, QImage.Format_Grayscale8).scaled(self.widthScale, self.depthScale)

        self.imDisplayFrame.setPixmap(QPixmap.fromImage(self.qIm).scaled(self.widthScale, self.depthScale))

        self.pixSizeAx = self.imgDataStruct.bMode.shape[0] #were both scBmode
        self.pixSizeLat = self.imgDataStruct.bMode.shape[1]

        self.axOverlapVal = 50
        self.latOverlapVal = 50
        self.minFreqVal = 3
        self.maxFreqVal = 4.5
        self.startDepthVal = 0.04
        self.endDepthVal = 0.16
        self.clipFactorVal = 95
        self.samplingFreqVal = 20

        self.plotOnCanvas()

    def openSiemensImage(self, imageFilePath, phantomFilePath):
        tmpLocation = imageFilePath.split("/")
        dataFileName = tmpLocation[-1]
        dataFileLocation = imageFilePath[:len(imageFilePath)-len(dataFileName)]
        tmpPhantLocation = phantomFilePath.split("/")
        phantFileName = tmpPhantLocation[-1]
        phantFileLocation = phantomFilePath[:len(phantomFilePath)-len(phantFileName)]

        self.imArray, self.imgDataStruct, self.imgInfoStruct, self.refDataStruct, self.refInfoStruct = rfdParser.getImage(dataFileName, dataFileLocation, phantFileName, phantFileLocation)
        self.frame = 0
        self.imData = np.array(self.imArray[self.frame]).reshape(self.imArray.shape[1], self.imArray.shape[2])
        self.imData = np.require(self.imData,np.uint8,'C')
        self.maskCoverImg = np.zeros([501, 721, 4]) # Hard-coded values match size of frame on GUI
        self.bytesLine = self.imData.strides[0]
        self.arHeight = self.imData.shape[0]
        self.arWidth = self.imData.shape[1]
        self.qIm = QImage(self.imData, self.arWidth, self.arHeight, self.bytesLine, QImage.Format_Grayscale8)

        quotient = self.imgInfoStruct.width / self.imgInfoStruct.depth
        if quotient > (721/501):
            self.widthScale = 721
            self.depthScale = self.widthScale / (self.imgInfoStruct.width/self.imgInfoStruct.depth)
        else:
            self.widthScale = 501 * quotient
            self.depthScale = 501
        self.yBorderMin = 170 + ((501 - self.depthScale)/2)
        self.yBorderMax = 671 - ((501 - self.depthScale)/2)
        self.xBorderMin = 400 + ((721 - self.widthScale)/2)
        self.xBorderMax = 1121 - ((721 - self.widthScale)/2)

        self.imDisplayFrame.setPixmap(QPixmap.fromImage(self.qIm).scaled(self.widthScale, self.depthScale))

        self.pixSizeAx = self.imgDataStruct.bMode.shape[1] #were both scBmode
        self.pixSizeLat = self.imgDataStruct.bMode.shape[2]

        self.ofFramesLabel.setHidden(False)
        self.curFrameLabel.setHidden(False)
        self.totalFramesLabel.setHidden(False)
        self.curFrameSlider.setHidden(False)
        self.curFrameSlider.setMaximum(self.imArray.shape[0]-1)
        self.totalFramesLabel.setText(str(self.imArray.shape[0]-1))
        self.curFrameSlider.valueChanged.connect(self.curFrameChanged)

        self.axOverlapVal = 50
        self.latOverlapVal = 50
        self.startDepthVal = 0.04
        self.endDepthVal = 0.16
        self.clipFactorVal = 95
        self.minFreqVal = 7
        self.maxFreqVal = 17
        self.samplingFreqVal = 40
        self.multipleFrames = True

        self.plotOnCanvas()

    def openTerasonImage(self, imageFilePath, phantomFilePath):
        self.imArray, self.imgDataStruct, self.imgInfoStruct, self.refDataStruct, self.refInfoStruct = tera.getImage(imageFilePath, phantomFilePath)

        quotient = self.imgInfoStruct.width / self.imgInfoStruct.depth
        if quotient > (721/501):
            self.widthScale = 721
            self.depthScale = self.widthScale / (self.imgInfoStruct.width/self.imgInfoStruct.depth)
        else:
            self.widthScale = 501 * quotient
            self.depthScale = 501
        self.maskCoverImg = np.zeros([501, 721, 4]) # Hard-coded values match size of frame on GUI
        self.yBorderMin = 170 + ((501 - self.depthScale)/2)
        self.yBorderMax = 671 - ((501 - self.depthScale)/2)
        self.xBorderMin = 400 + ((721 - self.widthScale)/2)
        self.xBorderMax = 1121 - ((721 - self.widthScale)/2)
            

        self.arHeight = self.imArray.shape[0]
        self.arWidth = self.imArray.shape[1]
        self.imData = np.array(self.imArray)
        self.imData = np.require(self.imData,np.uint8,'C')
        self.bytesLine = self.imData.strides[0]
        self.qIm = QImage(self.imData, self.arWidth, self.arHeight, self.bytesLine, QImage.Format_Grayscale8).scaled(self.widthScale, self.depthScale)

        self.imDisplayFrame.setPixmap(QPixmap.fromImage(self.qIm).scaled(self.widthScale, self.depthScale))

        self.pixSizeAx = self.imArray.shape[0]
        self.pixSizeLat = self.imArray.shape[1]
        self.axOverlapVal = 50
        self.latOverlapVal = 50
        self.minFreqVal = 3
        self.maxFreqVal = 4.5
        self.startDepthVal = 0.04
        self.endDepthVal = 0.16
        self.clipFactorVal = 95
        self.samplingFreqVal = 20
        self.frame = None

        self.plotOnCanvas()
        

    def curFrameChanged(self):
        self.frame = self.curFrameSlider.value()
        self.curFrameLabel.setText(str(self.frame))
        self.plotOnCanvas()

    def closeInterpolation(self): # Finish drawing ROI
        if len(self.curPointsPlottedX) > 2:
            self.drawRoiButton.setChecked(False)

            # remove duplicate points
            points = np.transpose(np.array([self.curPointsPlottedX, self.curPointsPlottedY]))
            points = removeDuplicates(points)
            [self.curPointsPlottedX, self.curPointsPlottedY] = np.transpose(points)
            self.curPointsPlottedX = list(self.curPointsPlottedX)
            self.curPointsPlottedY = list(self.curPointsPlottedY)
            self.curPointsPlottedX.append(self.curPointsPlottedX[0])
            self.curPointsPlottedY.append(self.curPointsPlottedY[0])
            self.maskCoverImg.fill(0)

            xSpline, ySpline = calculateSpline(self.curPointsPlottedX, self.curPointsPlottedY)
            xSpline = np.clip(xSpline, a_min=round(self.xBorderMin - 400)+1, a_max=720 + round(self.xBorderMax - 1121))
            ySpline = np.clip(ySpline, a_min=round(self.yBorderMin - 170)+1, a_max=500 + round(self.yBorderMax - 671))
            self.xSpline = xSpline
            self.ySpline = ySpline
            spline = [(int(xSpline[i]), int(ySpline[i])) for i in range(len(xSpline))]
            spline = np.array([*set(spline)])
            xSpline, ySpline = np.transpose(spline)
            for i in range(len(xSpline)):
                self.maskCoverImg[ySpline[i]-1:ySpline[i]+2, xSpline[i]-1:xSpline[i]+2] = [0, 0, 255, 255]
            self.drawRoiButton.setChecked(False)
            self.drawRoiButton.setCheckable(False)
            self.redrawRoiButton.setHidden(False)
            self.closeRoiButton.setHidden(True)
            self.plotOnCanvas()

    def undoLastPt(self):
        if len(self.curPointsPlottedX):
            self.maskCoverImg[self.curPointsPlottedX[-1]-2:self.curPointsPlottedX[-1]+3, \
                            self.curPointsPlottedY[-1]-2:self.curPointsPlottedY[-1]+3] = [0,0,0,0]
            self.curPointsPlottedX.pop()
            self.curPointsPlottedY.pop()
            self.updateSpline()

    def undoLastRoi(self):
        if not self.drawRoiButton.isCheckable() or self.drawRoiButton.isHidden():
            self.curPointsPlottedX = []
            self.curPointsPlottedY = []
            self.drawRoiButton.setCheckable(True)
            self.redrawRoiButton.setHidden(True)
            self.closeRoiButton.setHidden(False)
            self.maskCoverImg.fill(0)
            self.plotOnCanvas()
            self.update()

    def acceptROI(self):
        if len(self.curPointsPlottedX) > 1 and self.curPointsPlottedX[-1] == self.curPointsPlottedX[0]:
            del self.analysisParamsGUI

            if self.multipleFrames:
                imData = np.array(self.imArray[self.frame]).reshape(self.arHeight, self.arWidth)
            else:
                imData = self.imArray
            imData = np.flipud(imData)
            imData = np.require(imData, np.uint8, 'C')
            bytesLine = imData.strides[0]
            arHeight = imData.shape[0]
            arWidth = imData.shape[1]
            savedIm = QImage(imData, arWidth, arHeight, bytesLine, QImage.Format_Grayscale8).scaled(self.widthScale, self.depthScale)

            savedIm.mirrored().save(os.path.join("Junk", "bModeImRaw.png"))
            savedIm.mirrored().save(os.path.join("Junk", "bModeIm.png"))
            self.analysisParamsGUI = AnalysisParamsGUI()
            self.analysisParamsGUI.finalSplineX = self.xSpline - ((721 - self.widthScale)/2)
            self.analysisParamsGUI.finalSplineY = self.ySpline - ((501 - self.depthScale)/2)
            self.analysisParamsGUI.curPointsPlottedX = self.curPointsPlottedX
            self.analysisParamsGUI.curPointsPlottedY = self.curPointsPlottedY
            self.analysisParamsGUI.frame = self.frame
            self.analysisParamsGUI.imArray = self.imArray
            self.analysisParamsGUI.dataFrame = self.dataFrame
            self.analysisParamsGUI.imageDepthVal.setText(str(np.round(self.imgInfoStruct.depth, decimals=1)))
            self.analysisParamsGUI.imageWidthVal.setText(str(np.round(self.imgInfoStruct.width, decimals=1)))

            speedOfSoundInTissue = 1540 #m/s
            self.waveLength = (speedOfSoundInTissue/self.imgInfoStruct.centerFrequency)*1000 #mm
            self.analysisParamsGUI.axWinSizeVal.setValue(self.waveLength*10)
            self.analysisParamsGUI.latWinSizeVal.setValue(self.waveLength*10)
            # self.analysisParamsGUI.yBorderMin = (721 - self.widthScale)/2
            # self.analysisParamsGUI.xBorderMin = (501 - self.depthScale)/2
            self.analysisParamsGUI.imWidthScale = self.widthScale
            self.analysisParamsGUI.imDepthScale = self.depthScale

            self.analysisParamsGUI.axOverlapVal.setValue(self.axOverlapVal)
            self.analysisParamsGUI.latOverlapVal.setValue(self.latOverlapVal)
            self.analysisParamsGUI.windowThresholdVal.setValue(95)
            self.analysisParamsGUI.minFreqVal.setValue(np.round(self.imgInfoStruct.minFrequency/1000000, decimals=2))
            self.analysisParamsGUI.maxFreqVal.setValue(np.round(self.imgInfoStruct.maxFrequency/1000000, decimals=2))
            self.analysisParamsGUI.lowBandFreqVal.setValue(np.round(self.imgInfoStruct.lowBandFreq/1000000, decimals=2))
            self.analysisParamsGUI.upBandFreqVal.setValue(np.round(self.imgInfoStruct.upBandFreq/1000000, decimals=2))
            self.analysisParamsGUI.samplingFreqVal.setValue(np.round(self.imgInfoStruct.samplingFrequency/1000000, decimals=2))
            self.analysisParamsGUI.setFilenameDisplays(self.imagePathInput.text().split('/')[-1], self.phantomPathInput.text().split('/')[-1])
            self.analysisParamsGUI.lastGui = self
            self.analysisParamsGUI.plotRoiPreview()
            self.analysisParamsGUI.show()
            self.hide()

def calculateSpline(xpts, ypts): # 2D spline interpolation
    cv = []
    for i in range(len(xpts)):
        cv.append([xpts[i], ypts[i]])
    cv = np.array(cv)
    if len(xpts) == 2:
        tck, u_ = interpolate.splprep(cv.T, s=0.0, k=1)
    elif len(xpts) == 3:
        tck, u_ = interpolate.splprep(cv.T, s=0.0, k=2)
    else:
        tck, u_ = interpolate.splprep(cv.T, s=0.0, k=3)
    x,y = np.array(interpolate.splev(np.linspace(0, 1, 1000), tck))
    return x, y

def removeDuplicates(ar):
        # Credit: https://stackoverflow.com/questions/480214/how-do-i-remove-duplicates-from-a-list-while-preserving-order
        seen = set()
        seen_add = seen.add
        return [x for x in ar if not (tuple(x) in seen or seen_add(tuple(x)))]