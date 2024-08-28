import os
import platform

import numpy as np
from PIL import Image, ImageEnhance
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import scipy.interpolate as interpolate
from matplotlib.widgets import RectangleSelector, Cursor
import matplotlib.patches as patches

from PyQt5.QtWidgets import QWidget, QHBoxLayout
from PyQt5.QtGui import QImage

from pyQus.analysisObjects import UltrasoundImage, Config
from pyQus.spectral import SpectralAnalysis

from src.DataLayer.spectral import SpectralData
from src.DataLayer.dataObjects import ScConfig
import src.Parsers.verasonicsMatParser as vera
import src.Parsers.canonBinParser as canon
import src.Parsers.terasonRfParser as tera
from src.Parsers.philipsMatParser import getImage as philipsMatParser
from src.Parsers.philipsRfParser import main_parser_stanford as philipsRfParser
from src.UtcTool2d.roiSelection_ui import Ui_constructRoi
from src.UtcTool2d.editImageDisplay_ui_helper import EditImageDisplayGUI
from src.UtcTool2d.analysisParamsSelection_ui_helper import AnalysisParamsGUI
import src.UtcTool2d.selectImage_ui_helper as SelectImageSection
from src.UtcTool2d.loadRoi_ui_helper import LoadRoiGUI
from src.Utils.roiFuncs import computeSpecWindowsIQ, computeSpecWindowsRF

system = platform.system()


class RoiSelectionGUI(QWidget, Ui_constructRoi):
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

        self.imagePathInput.setHidden(True)
        self.phantomPathInput.setHidden(True)
        self.drawRoiButton.setHidden(True)
        self.closeRoiButton.setHidden(True)
        self.undoLastPtButton.setHidden(True)
        self.redrawRoiButton.setHidden(True)
        self.acceptRoiButton.setHidden(True)
        self.undoLoadedRoiButton.setHidden(True)
        self.acceptLoadedRoiButton.setHidden(True)
        self.userDrawRectangleButton.setHidden(True)
        self.drawFreehandButton.setHidden(True)
        self.backFromFreehandButton.setHidden(True)
        self.backFromRectangleButton.setHidden(True)
        self.acceptRectangleButton.setHidden(True)
        self.physicalRectDimsLabel.setHidden(True)
        self.physicalRectHeightLabel.setHidden(True)
        self.physicalRectWidthLabel.setHidden(True)
        self.physicalRectHeightVal.setHidden(True)
        self.physicalRectWidthVal.setHidden(True)
        self.acceptLoadedRoiButton.clicked.connect(self.acceptROI)
        self.acceptRectangleButton.clicked.connect(self.acceptRect)
        self.undoLoadedRoiButton.clicked.connect(self.undoRoiLoad)

        self.loadRoiGUI = LoadRoiGUI()
        self.pointsPlottedX = []
        self.pointsPlottedY = []

        # Prepare B-Mode display plot
        self.horizontalLayout = QHBoxLayout(self.imDisplayFrame)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.horizontalLayout.addWidget(self.canvas)

        self.editImageDisplayGUI = EditImageDisplayGUI()
        self.editImageDisplayGUI.contrastVal.valueChanged.connect(self.changeContrast)
        self.editImageDisplayGUI.brightnessVal.valueChanged.connect(
            self.changeBrightness
        )
        self.editImageDisplayGUI.sharpnessVal.valueChanged.connect(self.changeSharpness)

        self.analysisParamsGUI = AnalysisParamsGUI()

        self.scatteredPoints = []
        self.spectralData: SpectralData
        self.ultrasoundImage: UltrasoundImage
        self.lastGui: SelectImageSection.SelectImageGUI_UtcTool2dIQ

        self.crosshairCursor = Cursor(
            self.ax, color="gold", linewidth=0.4, useblit=True
        )
        self.selector = RectangleSelector(
            self.ax,
            self.drawRect,
            useblit=True,
            props=dict(linestyle="-", color="cyan", fill=False),
        )
        self.selector.set_active(False)
        self.cid = None

        self.redrawRoiButton.setHidden(True)

        # self.editImageDisplayButton.clicked.connect(self.openImageEditor)
        self.editImageDisplayButton.setHidden(True)  # done for now for simplicity
        self.drawRoiButton.clicked.connect(self.recordDrawRoiClicked)
        self.userDrawRectangleButton.clicked.connect(self.recordDrawRectClicked)
        self.undoLastPtButton.clicked.connect(self.undoLastPt)
        self.closeRoiButton.clicked.connect(self.closeInterpolation)
        self.redrawRoiButton.clicked.connect(self.undoLastRoi)
        self.acceptRoiButton.clicked.connect(self.acceptROI)
        self.backButton.clicked.connect(self.backToWelcomeScreen)
        self.newRoiButton.clicked.connect(self.drawNewRoi)
        self.drawRectangleButton.clicked.connect(self.startDrawRectRoi)
        self.loadRoiButton.clicked.connect(self.openLoadRoiWindow)
        self.backFromFreehandButton.clicked.connect(self.backFromFreehand)
        self.backFromRectangleButton.clicked.connect(self.backFromRect)

    def undoRoiLoad(self):
        self.undoLoadedRoiButton.setHidden(True)
        self.acceptLoadedRoiButton.setHidden(True)
        self.loadRoiButton.setHidden(False)
        self.newRoiButton.setHidden(False)
        self.drawRectangleButton.setHidden(False)

        self.spectralData.rectCoords = []
        self.undoLastRoi()

    def openLoadRoiWindow(self):
        self.loadRoiGUI.chooseRoiGUI = self
        self.loadRoiGUI.show()

    def backFromFreehand(self):
        self.newRoiButton.setHidden(False)
        self.loadRoiButton.setHidden(False)
        self.drawRectangleButton.setHidden(False)
        self.drawRoiButton.setHidden(True)
        self.undoLastPtButton.setHidden(True)
        self.closeRoiButton.setHidden(True)
        self.acceptRoiButton.setHidden(True)
        self.backFromFreehandButton.setHidden(True)
        self.undoLastRoi()
        self.drawRoiButton.setChecked(False)
        self.crosshairCursor.set_active(False)
        if self.cid is not None:
            self.cid = self.figure.canvas.mpl_disconnect(self.cid)

    def backFromRect(self):
        self.newRoiButton.setHidden(False)
        self.drawRectangleButton.setHidden(False)
        self.loadRoiButton.setHidden(False)
        self.userDrawRectangleButton.setHidden(True)
        self.backFromRectangleButton.setHidden(True)
        self.acceptRectangleButton.setHidden(True)
        self.physicalRectDimsLabel.setHidden(True)
        self.physicalRectHeightLabel.setHidden(True)
        self.physicalRectWidthLabel.setHidden(True)
        self.physicalRectHeightVal.setHidden(True)
        self.physicalRectWidthVal.setHidden(True)
        self.physicalRectHeightVal.setText("0")
        self.physicalRectWidthVal.setText("0")
        self.userDrawRectangleButton.setChecked(False)
        self.undoLastRoi()
        self.spectralData.rectCoords = []
        self.selector.set_active(False)
        if len(self.ax.patches) > 0:
            self.ax.patches.pop()
        self.canvas.draw()

    def drawNewRoi(self):
        self.newRoiButton.setHidden(True)
        self.loadRoiButton.setHidden(True)
        self.drawRectangleButton.setHidden(True)
        self.drawRoiButton.setHidden(False)
        self.undoLastPtButton.setHidden(False)
        self.closeRoiButton.setHidden(False)
        self.acceptRoiButton.setHidden(False)
        self.backFromFreehandButton.setHidden(False)

    def startDrawRectRoi(self):
        self.newRoiButton.setHidden(True)
        self.drawRectangleButton.setHidden(True)
        self.loadRoiButton.setHidden(True)
        self.userDrawRectangleButton.setHidden(False)
        self.backFromRectangleButton.setHidden(False)
        self.acceptRectangleButton.setHidden(False)
        self.physicalRectDimsLabel.setHidden(False)
        self.physicalRectHeightLabel.setHidden(False)
        self.physicalRectWidthLabel.setHidden(False)
        self.physicalRectHeightVal.setHidden(False)
        self.physicalRectWidthVal.setHidden(False)

    def backToWelcomeScreen(self):
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
        self.ax.imshow(self.spectralData.finalBmode, cmap="Greys_r")
        plt.gcf().set_facecolor((0, 0, 0, 0))

        try:
            if self.spectralData.numSamplesDrOut == 1400:
                # Preset 1 boundaries for 20220831121844_IQ.bin
                self.ax.plot([148.76, 154.22], [0, 500], c="purple")  # left boundary
                self.ax.plot([0, 716], [358.38, 386.78], c="purple")  # bottom boundary
                self.ax.plot([572.47, 509.967], [0, 500], c="purple")  # right boundary

            elif self.spectralData.numSamplesDrOut == 1496:
                # Preset 2 boundaries for 20220831121752_IQ.bin
                self.ax.plot([146.9, 120.79], [0, 500], c="purple")  # left boundary
                self.ax.plot([0, 644.76], [462.41, 500], c="purple")  # bottom boundary
                self.ax.plot([614.48, 595.84], [0, 500], c="purple")  # right boundary

            # elif self.ImDisplayInfo.numSamplesDrOut != -1:
            #     print("No preset found!")
        except (AttributeError, UnboundLocalError):
            pass

        if len(self.spectralData.splineX):
            self.spline = self.ax.plot(self.spectralData.splineX, self.spectralData.splineY, 
                                       color="cyan", zorder=1, linewidth=0.75)
        elif len(self.pointsPlottedX) > 0:
            self.scatteredPoints.append(
                self.ax.scatter(
                    self.pointsPlottedX[-1],
                    self.pointsPlottedY[-1],
                    marker="o",
                    s=0.5,
                    c="red",
                    zorder=500,
                )
            )
            if len(self.pointsPlottedX) > 1:
                xSpline, ySpline = calculateSpline(
                    self.pointsPlottedX, self.pointsPlottedY
                )
                self.spline = self.ax.plot(
                    xSpline, ySpline, color="cyan", zorder=1, linewidth=0.75
                )

        self.figure.subplots_adjust(
            left=0, right=1, bottom=0, top=1, hspace=0.2, wspace=0.2
        )
        self.crosshairCursor.set_active(False)
        plt.tick_params(bottom=False, left=False, labelbottom=False, labelleft=False)
        self.canvas.draw()  # Refresh canvas

    def openImageVerasonics(
        self, imageFilePath, phantomFilePath
    ):  # Open initial image given data and phantom files previously inputted
        raise NotImplementedError("Not updated with refactor")
        tmpLocation = imageFilePath.split("/")
        dataFileName = tmpLocation[-1]
        dataFileLocation = imageFilePath[: len(imageFilePath) - len(dataFileName)]
        tmpPhantLocation = phantomFilePath.split("/")
        phantFileName = tmpPhantLocation[-1]
        phantFileLocation = phantomFilePath[: len(phantomFilePath) - len(phantFileName)]

        (imArray, imgDataStruct, imgInfoStruct, refDataStruct, refInfoStruct,) = vera.getImage(
            dataFileName, dataFileLocation, phantFileName, phantFileLocation
        )
        self.AnalysisInfo.verasonics = True

        self.AnalysisInfo.computeSpecWindows = computeSpecWindowsIQ

        self.processImage(
            imArray, imgDataStruct, refDataStruct, imgInfoStruct, refInfoStruct
        )

        self.editImageDisplayGUI.brightnessVal.setValue(1)
        self.editImageDisplayGUI.sharpnessVal.setValue(1)

    def openImageCanon(
        self, imageFilePath, phantomFilePath
    ):  # Open initial image given data and phantom files previously inputted
        # Find image and phantom paths
        tmpLocation = imageFilePath.split("/")
        dataFileName = tmpLocation[-1]
        dataFileLocation = imageFilePath[: len(imageFilePath) - len(dataFileName)]
        tmpPhantLocation = phantomFilePath.split("/")
        phantFileName = tmpPhantLocation[-1]
        phantFileLocation = phantomFilePath[: len(phantomFilePath) - len(phantFileName)]

        # Open both images and record relevant data
        imgDataStruct, imgInfoStruct, refDataStruct, refInfoStruct = canon.getImage(
            dataFileName, dataFileLocation, phantFileName, phantFileLocation
        )

        scConfig = ScConfig()
        scConfig.width = imgInfoStruct.width1
        scConfig.tilt = imgInfoStruct.tilt1
        scConfig.startDepth = imgInfoStruct.startDepth1
        scConfig.endDepth = imgInfoStruct.endDepth1
        scConfig.numSamplesDrOut = imgInfoStruct.numSamplesDrOut
        self.spectralData.scConfig = scConfig

        self.ultrasoundImage = UltrasoundImage()
        self.ultrasoundImage.bmode = np.flipud(imgDataStruct.scBmodeStruct.preScArr)
        self.ultrasoundImage.scBmode = np.flipud(imgDataStruct.scBmodeStruct.scArr)
        self.ultrasoundImage.xmap = np.flipud(imgDataStruct.scBmodeStruct.xmap)
        self.ultrasoundImage.ymap = np.flipud(imgDataStruct.scBmodeStruct.ymap)

        self.processImage(
            imgDataStruct, refDataStruct, imgInfoStruct, refInfoStruct
        )

    def openPhilipsImage(self, imageFilePath, phantomFilePath):
        raise NotImplementedError("Not updated with refactor")
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
                philipsRfParser(imageFilePath) # parse image filee
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
                philipsRfParser(imageFilePath) # parse image filee

                phantFileName = str(phantFileName[:-3]+'.mat')

        # Display Philips image and assign relevant default analysis params
        self.frame = None
        imArray, imgDataStruct, imgInfoStruct, refDataStruct, refInfoStruct = philipsMatParser(dataFileName, dataFileLocation, phantFileName, phantFileLocation, self.frame)

        self.processImage(
            imArray, imgDataStruct, refDataStruct, imgInfoStruct, refInfoStruct
        )    

    def openImageTerason(self, imageFilePath, phantomFilePath):
        raise NotImplementedError("Not updated with refactor")
        imgDataStruct, imgInfoStruct, refDataStruct, refInfoStruct = tera.getImage(
            imageFilePath, phantomFilePath
        )

        # Assumes no scan conversion
        imArray = imgDataStruct.bMode
        self.AnalysisInfo.computeSpecWindows = computeSpecWindowsRF
        self.processImage(
            imArray, imgDataStruct, refDataStruct, imgInfoStruct, refInfoStruct
        )

    def processImage(
        self, imgDataStruct, refDataStruct, imgInfoStruct, refInfoStruct
    ):
        self.ultrasoundImage.axialResRf = imgInfoStruct.depth / imgDataStruct.rf.shape[0]
        self.ultrasoundImage.lateralResRf = self.ultrasoundImage.axialResRf * (
            imgDataStruct.rf.shape[0]/imgDataStruct.rf.shape[1]
        ) # placeholder
        self.ultrasoundImage.rf = imgDataStruct.rf
        self.ultrasoundImage.phantomRf = refDataStruct.rf

        analysisConfig = Config()
        analysisConfig.analysisFreqBand = [imgInfoStruct.lowBandFreq, imgInfoStruct.upBandFreq]
        analysisConfig.transducerFreqBand = [imgInfoStruct.minFrequency, imgInfoStruct.maxFrequency]
        analysisConfig.samplingFrequency = imgInfoStruct.samplingFrequency
        analysisConfig.centerFrequency = imgInfoStruct.centerFrequency

        spectralAnalysis = SpectralAnalysis()
        spectralAnalysis.ultrasoundImage = self.ultrasoundImage
        spectralAnalysis.config = analysisConfig

        self.spectralData.spectralAnalysis = spectralAnalysis
        self.spectralData.depth = imgInfoStruct.depth
        self.spectralData.width = imgInfoStruct.width
        
        self.spectralData.convertImagesToRGB()

        self.displayInitialImage()

    def displayInitialImage(self):
        # Display images correctly
        quotient = self.spectralData.width / self.spectralData.depth
        if quotient > (721 / 501):
            self.spectralData.roiWidthScale = 721
            self.spectralData.roiDepthScale = int(self.spectralData.roiWidthScale / (
                self.spectralData.width / self.spectralData.depth
            ))
        else:
            self.spectralData.roiWidthScale = int(501 * quotient)
            self.spectralData.roiDepthScale = 501
        self.maskCoverImg = np.zeros(
            [501, 721, 4]
        )  # Hard-coded values match size of frame on GUI
        self.yBorderMin = 190 + ((501 - self.spectralData.roiDepthScale) / 2)
        self.yBorderMax = 671 - ((501 - self.spectralData.roiDepthScale) / 2)
        self.xBorderMin = 400 + ((721 - self.spectralData.roiWidthScale) / 2)
        self.xBorderMax = 1121 - ((721 - self.spectralData.roiWidthScale) / 2)

        self.qIm = QImage(
            self.spectralData.finalBmode,
            self.spectralData.finalBmode.shape[1],
            self.spectralData.finalBmode.shape[0],
            self.spectralData.finalBmode.strides[0],
            QImage.Format_RGB888,
        ).scaled(self.spectralData.roiWidthScale, self.spectralData.roiDepthScale)

        self.qIm.mirrored().save(
            os.path.join("Junk", "bModeImRaw.png")
        )  # Save as .png file

        self.editImageDisplayGUI.contrastVal.setValue(1)
        self.editImageDisplayGUI.brightnessVal.setValue(0.75)
        self.editImageDisplayGUI.sharpnessVal.setValue(3)

        self.spectralData.spectralAnalysis.initAnalysisConfig()

        self.physicalDepthVal.setText(
            str(np.round(self.spectralData.depth, decimals=2))
        )
        self.physicalWidthVal.setText(
            str(np.round(self.spectralData.width, decimals=2))
        )
        self.pixelWidthVal.setText(str(self.spectralData.finalBmode.shape[1]))
        self.pixelDepthVal.setText(str(self.spectralData.finalBmode.shape[0]))

        self.cvIm = Image.open(os.path.join("Junk", "bModeImRaw.png"))
        enhancer = ImageEnhance.Contrast(self.cvIm)

        imOutput = enhancer.enhance(self.editImageDisplayGUI.contrastVal.value())
        bright = ImageEnhance.Brightness(imOutput)
        imOutput = bright.enhance(self.editImageDisplayGUI.brightnessVal.value())
        sharp = ImageEnhance.Sharpness(imOutput)
        imOutput = sharp.enhance(self.editImageDisplayGUI.sharpnessVal.value())
        self.spectralData.finalBmode = np.array(imOutput)

        self.plotOnCanvas()

    def recordDrawRoiClicked(self):
        if self.drawRoiButton.isChecked():  # Set up b-mode to be drawn on
            # image, =self.ax.plot([], [], marker="o",markersize=3, markerfacecolor="red")
            # self.cid = image.figure.canvas.mpl_connect('button_press_event', self.interpolatePoints)
            self.cid = self.figure.canvas.mpl_connect(
                "button_press_event", self.interpolatePoints
            )
            self.crosshairCursor.set_active(True)
        else:  # No longer let b-mode be drawn on
            self.cid = self.figure.canvas.mpl_disconnect(self.cid)
            self.crosshairCursor.set_active(False)
        self.canvas.draw()

    def recordDrawRectClicked(self):
        if self.userDrawRectangleButton.isChecked():  # Set up b-mode to be drawn on
            self.selector.set_active(True)
            self.cid = self.figure.canvas.mpl_connect(
                "button_press_event", self.clearRect
            )
        else:  # No longer let b-mode be drawn on
            self.cid = self.figure.canvas.mpl_disconnect(self.cid)
            self.selector.set_active(False)
        self.canvas.draw()

    def undoLastPt(self):  # When drawing ROI, undo last point plotted
        if len(self.pointsPlottedX) > 0:
            self.scatteredPoints[-1].remove()
            self.scatteredPoints.pop()
            self.pointsPlottedX.pop()
            self.pointsPlottedY.pop()
            if len(self.pointsPlottedX) > 0:
                oldSpline = self.spline.pop(0)
                oldSpline.remove()
                if len(self.pointsPlottedX) > 1:
                    self.spectralData.splineX, self.spectralData.splineY = calculateSpline(
                        self.pointsPlottedX, self.pointsPlottedY
                    )
                    self.spline = self.ax.plot(
                        self.spectralData.splineX,
                        self.spectralData.splineY,
                        color="cyan",
                        linewidth=0.75,
                    )
            self.canvas.draw()
            self.drawRoiButton.setChecked(True)
            self.recordDrawRoiClicked()

    def closeInterpolation(self):  # Finish drawing ROI
        if len(self.pointsPlottedX) > 2:
            self.ax.clear()
            self.ax.imshow(self.spectralData.finalBmode, cmap="Greys_r")
            if self.pointsPlottedX[0] != self.pointsPlottedX[-1] and self.pointsPlottedY[0] != self.pointsPlottedY[-1]:
                self.pointsPlottedX.append(self.pointsPlottedX[0])
                self.pointsPlottedY.append(self.pointsPlottedY[0])
            self.spectralData.splineX, self.spectralData.splineY = calculateSpline(
                self.pointsPlottedX, self.pointsPlottedY
            )
            self.spectralData.splineX = np.clip(self.spectralData.splineX, a_min=0, a_max=self.spectralData.pixDepth-1)
            self.spectralData.splineY = np.clip(self.spectralData.splineY, a_min=0, a_max=self.spectralData.pixDepth-1)

            try:
                if self.spectralData.numSamplesDrOut == 1400:
                    self.spectralData.splineX = np.clip(self.spectralData.splineX, a_min=148, a_max=573)
                    self.spectralData.splineY = np.clip(self.spectralData.splineY, a_min=0.5, a_max=387)
                elif self.spectralData.numSamplesDrOut == 1496:
                    self.spectralData.splineX = np.clip(self.spectralData.splineX, a_min=120, a_max=615)
                    self.spectralData.splineY = np.clip(self.spectralData.splineY, a_min=0.5, a_max=645)
                # elif self.ImDisplayInfo.numSamplesDrOut != -1:
                #     print("Preset not found!")
                #     return
            except (AttributeError, UnboundLocalError):
                pass

            self.ax.plot(
                self.spectralData.splineX, self.spectralData.splineY, color="cyan", linewidth=0.75
            )
            try:
                (image,) = self.ax.plot(
                    [], [], marker="o", markersize=3, markerfacecolor="red"
                )
                image.figure.canvas.mpl_disconnect(self.cid)
            except AttributeError:
                image = 0  # do nothing. Means we're loading ROI

            try:
                if self.spectralData.numSamplesDrOut == 1400:
                    # Preset 1 boundaries for 20220831121844_IQ.bin
                    self.ax.plot(
                        [148.76, 154.22], [0, 500], c="purple"
                    )  # left boundary
                    self.ax.plot(
                        [0, 716], [358.38, 386.78], c="purple"
                    )  # bottom boundary
                    self.ax.plot(
                        [572.47, 509.967], [0, 500], c="purple"
                    )  # right boundary

                elif self.spectralData.numSamplesDrOut == 1496:
                    # Preset 2 boundaries for 20220831121752_IQ.bin
                    self.ax.plot([146.9, 120.79], [0, 500], c="purple")  # left boundary
                    self.ax.plot(
                        [0, 644.76], [462.41, 500], c="purple"
                    )  # bottom boundary
                    self.ax.plot(
                        [614.48, 595.84], [0, 500], c="purple"
                    )  # right boundary

                # elif self.ImDisplayInfo.numSamplesDrOut != -1:
                #     print("No preset found!")
            except (AttributeError, UnboundLocalError):
                pass

            self.figure.subplots_adjust(
                left=0, right=1, bottom=0, top=1, hspace=0.2, wspace=0.2
            )
            self.ax.tick_params(bottom=False, left=False)
            self.canvas.draw()
            self.ROIDrawn = True
            self.drawRoiButton.setChecked(False)
            self.drawRoiButton.setCheckable(False)
            self.redrawRoiButton.setHidden(False)
            self.closeRoiButton.setHidden(True)
            self.crosshairCursor.set_active(False)
            self.undoLastPtButton.clicked.disconnect()
            self.canvas.draw()

    def undoLastRoi(
        self,
    ):  # Remove previously drawn roi and prepare user to draw a new one
        self.spectralData.splineX = []
        self.spectralData.splineY = []
        self.pointsPlottedX = []
        self.pointsPlottedY = []
        self.drawRoiButton.setChecked(False)
        self.drawRoiButton.setCheckable(True)
        self.closeRoiButton.setHidden(False)
        self.redrawRoiButton.setHidden(True)
        self.undoLastPtButton.clicked.connect(self.undoLastPt)
        self.plotOnCanvas()

    def updateBModeSettings(
        self,
    ):  # Updates background photo when image settings are modified
        self.cvIm = Image.open(os.path.join("Junk", "bModeImRaw.png"))
        contrast = ImageEnhance.Contrast(self.cvIm)
        imOutput = contrast.enhance(self.editImageDisplayGUI.contrastVal.value())
        brightness = ImageEnhance.Brightness(imOutput)
        imOutput = brightness.enhance(self.editImageDisplayGUI.brightnessVal.value())
        sharpness = ImageEnhance.Sharpness(imOutput)
        imOutput = sharpness.enhance(self.editImageDisplayGUI.sharpnessVal.value())
        self.spectralData.finalBmode = np.array(imOutput)
        self.plotOnCanvas()

    def clearRect(self, event):
        if len(self.ax.patches) > 0:
            self.ax.patches.pop()
            self.canvas.draw()

    def interpolatePoints(
        self, event
    ):  # Update ROI being drawn using spline using 2D interpolation
        try:
            if self.spectralData.numSamplesDrOut == 1400:
                # Preset 1 boundaries for 20220831121844_IQ.bin
                leftSlope = (500 - 0) / (154.22 - 148.76)
                pointSlopeLeft = (event.ydata - 0) / (event.xdata - 148.76)
                if pointSlopeLeft <= 0 or leftSlope < pointSlopeLeft:
                    return

                bottomSlope = (386.78 - 358.38) / (716 - 0)
                pointSlopeBottom = (event.ydata - 358.38) / (event.xdata - 0)
                rightSlope = (500 - 0) / (509.967 - 572.47)
                pointSlopeRight = (event.ydata - 0) / (event.xdata - 572.47)

            elif self.spectralData.numSamplesDrOut == 1496:
                # Preset 2 boundaries for 20220831121752_IQ.bin
                leftSlope = (500 - 0) / (120.79 - 146.9)
                pointSlopeLeft = (event.ydata - 0) / (event.xdata - 146.9)
                if pointSlopeLeft > leftSlope and pointSlopeLeft <= 0:
                    return

                bottomSlope = (500 - 462.41) / (644.76 - 0)
                pointSlopeBottom = (event.ydata - 462.41) / (event.xdata - 0)
                rightSlope = (500 - 0) / (595.84 - 614.48)
                pointSlopeRight = (event.ydata - 0) / (event.xdata - 614.48)

            # elif self.ImDisplayInfo.numSamplesDrOut != -1:
            #     print("Preset not found!")
            #     return

            if pointSlopeBottom > bottomSlope:
                return
            if pointSlopeRight >= 0 or pointSlopeRight < rightSlope:
                return
        except (AttributeError, UnboundLocalError):
            pass

        if len(self.pointsPlottedX) > 0 and self.pointsPlottedX[-1] == int(event.xdata) and self.pointsPlottedY[-1] == int(event.ydata):
            return

        self.pointsPlottedX.append(int(event.xdata))
        self.pointsPlottedY.append(int(event.ydata))
        plottedPoints = len(self.pointsPlottedX)

        if plottedPoints > 1:
            if plottedPoints > 2:
                oldSpline = self.spline.pop(0)
                oldSpline.remove()

            xSpline, ySpline = calculateSpline(self.pointsPlottedX, self.pointsPlottedY)
            xSpline = np.clip(xSpline, a_min=0, a_max=self.spectralData.pixWidth-1)
            ySpline = np.clip(ySpline, a_min=0, a_max=self.spectralData.pixDepth-1)
            self.spline = self.ax.plot(
                xSpline, ySpline, color="cyan", zorder=1, linewidth=0.75
            )
            self.figure.subplots_adjust(
                left=0, right=1, bottom=0, top=1, hspace=0.2, wspace=0.2
            )
            self.ax.tick_params(bottom=False, left=False)
        self.scatteredPoints.append(
            self.ax.scatter(
                self.pointsPlottedX[-1],
                self.pointsPlottedY[-1],
                marker="o",
                s=0.5,
                c="red",
                zorder=500,
            )
        )
        self.canvas.draw()

    def drawRect(self, event1, event2):
        try:
            if self.spectralData.numSamplesDrOut == 1400:
                # Preset 1 boundaries for 20220831121844_IQ.bin
                leftSlope = (500 - 0) / (154.22 - 148.76)
                pointSlopeLeft = (event1.ydata - 0) / (event1.xdata - 148.76)
                if pointSlopeLeft <= 0 or leftSlope < pointSlopeLeft:
                    return
                pointSlopeLeft = (event2.ydata - 0) / (event2.xdata - 148.76)
                if pointSlopeLeft <= 0 or leftSlope < pointSlopeLeft:
                    return

                bottomSlope = (386.78 - 358.38) / (716 - 0)
                pointSlopeBottom = (event1.ydata - 358.38) / (event1.xdata - 0)
                if pointSlopeBottom > bottomSlope:
                    return
                pointSlopeBottom = (event2.ydata - 358.38) / (event2.xdata - 0)
                if pointSlopeBottom > bottomSlope:
                    return
                rightSlope = (500 - 0) / (509.967 - 572.47)
                pointSlopeRight = (event1.ydata - 0) / (event1.xdata - 572.47)
                if pointSlopeRight >= 0 or pointSlopeRight < rightSlope:
                    return
                pointSlopeRight = (event2.ydata - 0) / (event2.xdata - 572.47)
                if pointSlopeRight >= 0 or pointSlopeRight < rightSlope:
                    return

            elif self.spectralData.numSamplesDrOut == 1496:
                # Preset 2 boundaries for 20220831121752_IQ.bin
                leftSlope = (500 - 0) / (120.79 - 146.9)
                pointSlopeLeft = (event1.ydata - 0) / (event1.xdata - 146.9)
                if pointSlopeLeft > leftSlope and pointSlopeLeft <= 0:
                    return
                pointSlopeLeft = (event2.ydata - 0) / (event2.xdata - 146.9)
                if pointSlopeLeft > leftSlope and pointSlopeLeft <= 0:
                    return

                bottomSlope = (500 - 462.41) / (644.76 - 0)
                pointSlopeBottom = (event1.ydata - 462.41) / (event1.xdata - 0)
                if pointSlopeBottom > bottomSlope:
                    return
                pointSlopeBottom = (event2.ydata - 462.41) / (event2.xdata - 0)
                if pointSlopeBottom > bottomSlope:
                    return
                rightSlope = (500 - 0) / (595.84 - 614.48)
                pointSlopeRight = (event1.ydata - 0) / (event1.xdata - 614.48)
                if pointSlopeRight >= 0 or pointSlopeRight < rightSlope:
                    return
                pointSlopeRight = (event2.ydata - 0) / (event2.xdata - 614.48)
                if pointSlopeRight >= 0 or pointSlopeRight < rightSlope:
                    return

            # elif self.ImDisplayInfo.numSamplesDrOut != -1:
            #     print("Preset not found!")
            #     return

        except (AttributeError, UnboundLocalError):
            pass

        self.spectralData.rectCoords = [
            int(event1.xdata),
            int(event1.ydata),
            int(event2.xdata),
            int(event2.ydata),
        ]
        self.plotPatch()

    def plotPatch(self):
        if len(self.spectralData.rectCoords) > 0:
            left, bottom, right, top = self.spectralData.rectCoords
            rect = patches.Rectangle(
                (left, bottom),
                (right - left),
                (top - bottom),
                linewidth=1,
                edgecolor="cyan",
                facecolor="none",
            )
            if len(self.ax.patches) > 0:
                self.ax.patches.pop()

            self.ax.add_patch(rect)

            xScale = self.spectralData.roiWidthScale / (self.spectralData.finalBmode.shape[1])
            mplPixWidth = abs(right - left)
            imPixWidth = mplPixWidth / xScale
            mmWidth = self.spectralData.lateralRes * imPixWidth  # (mm/pixel)*pixels
            self.physicalRectWidthVal.setText(str(np.round(mmWidth, decimals=2)))

            yScale = self.spectralData.roiDepthScale / (self.spectralData.finalBmode.shape[0])
            mplPixHeight = abs(top - bottom)
            imPixHeight = mplPixHeight / yScale
            mmHeight = self.spectralData.axialRes * imPixHeight  # (mm/pixel)*pixels
            self.physicalRectHeightVal.setText(str(np.round(mmHeight, decimals=2)))

            self.figure.subplots_adjust(
                left=0, right=1, bottom=0, top=1, hspace=0.2, wspace=0.2
            )
            self.ax.tick_params(bottom=False, left=False)
            self.canvas.draw()

    def acceptRect(self):
        if len(self.ax.patches) == 1:
            left, bottom = self.ax.patches[0].get_xy()
            left = int(left)
            bottom = int(bottom)
            width = int(self.ax.patches[0].get_width())
            height = int(self.ax.patches[0].get_height())
            self.pointsPlottedX = (
                list(range(left, left + width))
                + list(np.ones(height).astype(int) * (left + width - 1))
                + list(range(left + width - 1, left - 1, -1))
                + list(np.ones(height).astype(int) * left)
            )
            self.pointsPlottedY = (
                list(np.ones(width).astype(int) * bottom)
                + list(range(bottom, bottom + height))
                + list(np.ones(width).astype(int) * (bottom + height - 1))
                + list(range(bottom + height - 1, bottom - 1, -1))
            )
            self.spectralData.splineX = np.array(
                self.pointsPlottedX
            )  # Image boundaries already addressed at plotting phase
            self.spectralData.splineY = np.array(
                self.pointsPlottedY
            )  # Image boundaries already addressed at plotting phase
            self.acceptROI()

    def acceptROI(self):
        if (
            len(self.pointsPlottedX) > 1
            and self.pointsPlottedX[0] == self.pointsPlottedX[-1]
        ):
            self.analysisParamsGUI.spectralData = self.spectralData
            self.analysisParamsGUI.initParams()
            self.analysisParamsGUI.lastGui = self
            self.analysisParamsGUI.setFilenameDisplays(
                self.imagePathInput.text(),
                self.phantomPathInput.text(),
            )
            self.analysisParamsGUI.plotRoiPreview()
            self.analysisParamsGUI.show()
            self.editImageDisplayGUI.hide()
            self.hide()


def calculateSpline(xpts, ypts):  # 2D spline interpolation
    cv = []
    for i in range(len(xpts)):
        cv.append([xpts[i], ypts[i]])
    cv = np.array(cv)
    if len(xpts) == 2:
        tck, _ = interpolate.splprep(cv.T, s=0.0, k=1)
    elif len(xpts) == 3:
        tck, _ = interpolate.splprep(cv.T, s=0.0, k=2)
    else:
        tck, _ = interpolate.splprep(cv.T, s=0.0, k=3)
    x, y = np.array(interpolate.splev(np.linspace(0, 1, 1000), tck))
    return x, y
