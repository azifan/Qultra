from CeusTool3d.voiSelection_ui import Ui_constructVoi
from CeusTool3d.ticAnalysis_ui_helper import TicAnalysisGUI
from CeusTool3d.saveVoi_ui_helper import SaveVoiGUI

import nibabel as nib
import numpy as np
from scipy.ndimage import binary_fill_holes
import os

from itertools import chain
import scipy.interpolate as interpolate
from scipy.spatial import ConvexHull
import pyvista as pv
import Utils.utils as ut

from PyQt5.QtWidgets import QWidget, QApplication, QFileDialog
from PyQt5.QtGui import QPixmap, QPainter, QImage
from PyQt5.QtCore import QLine, Qt

import platform

system = platform.system()


class VoiSelectionGUI(Ui_constructVoi, QWidget):
    def __init__(self):
        # self.selectImage = QWidget()
        super().__init__()
        self.setupUi(self)

        if system == "Windows":
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
            self.imagePathInput.setStyleSheet(
                """QLabel {
                font-size: 11px;
                color: rgb(255, 255, 255);
                background-color: rgba(255, 255, 255, 0);
                border: 0px;
            }"""
            )
            self.roiSidebarLabel.setStyleSheet(
                """QLabel {
                font-size: 18px;
                color: rgb(255, 255, 255);
                background-color: rgba(255, 255, 255, 0);
                border: 0px;
                font-weight: bold;
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
            self.ticAnalysisLabel.setStyleSheet(
                """QLabel {
                font-size: 18px;
                color: rgb(255, 255, 255);
                background-color: rgba(255, 255, 255, 0);
                border: 0px;
                font-weight: bold;
            }"""
            )
            self.rfAnalysisLabel.setStyleSheet(
                """QLabel {
                font-size: 18px;
                color: rgb(255, 255, 255);
                background-color: rgba(255, 255, 255, 0);
                border: 0px;
                font-weight: bold;
            }"""
            )
            self.voiAlphaSpinBox.setStyleSheet(
                """QSpinBox{
                background-color: white;
                font-size: 13px;
            }"""
            )

        self.redrawRoiButton.setHidden(True)
        self.continueButton.setHidden(True)
        self.continueButton.clicked.connect(self.moveToTic)

        self.voiAlphaLabel.setHidden(True)
        self.voiAlphaOfLabel.setHidden(True)
        self.voiAlphaSpinBox.setHidden(True)
        self.voiAlphaStatus.setHidden(True)
        self.voiAlphaTotal.setHidden(True)
        self.restartVoiButton.setHidden(True)
        self.exportDataButton.setHidden(True)
        self.saveDataButton.setHidden(True)
        self.saveVoiButton.setHidden(True)
        self.drawRoiButton.setHidden(True)
        self.undoLastPtButton.setHidden(True)
        self.interpolateVoiButton.setHidden(True)
        self.closeRoiButton.setHidden(True)
        self.newVoiBackButton.setHidden(True)
        self.voiAdviceLabel.setHidden(True)
        self.toggleButton.setHidden(True)

        self.sliceSpinBoxChanged = False
        self.sliceSliderChanged = False
        self.newData = None
        self.auc = None
        self.pe = None
        self.tp = None
        self.mtt = None
        self.tmppv = None
        self.dataFrame = None
        self.fullPath = None
        self.bmode4dIm = None

        self.voiAlphaSpinBox.setMinimum(0)
        self.voiAlphaSpinBox.setMaximum(255)
        self.voiAlphaStatus.setMinimum(0)
        self.voiAlphaStatus.setMaximum(255)
        self.voiAlphaStatus.setValue(255)
        self.voiAlphaSpinBox.setValue(255)

        self.curSliceIndex = 0
        self.curAlpha = 255
        self.curPointsPlottedX = []
        self.curPointsPlottedY = []
        self.pointsPlotted = []
        self.xCur = 0
        self.yCur = 0
        self.planesDrawn = []
        self.painted = "none"
        self.lastGui = None
        self.exportDataGUI = None
        self.saveVoiGUI = None
        self.timeconst = None

        self.setMouseTracking(True)

        self.ticAnalysisGui = TicAnalysisGUI()

        self.axCoverPixmap = QPixmap(321, 301)
        self.axCoverPixmap.fill(Qt.transparent)
        self.axCoverLabel.setPixmap(self.axCoverPixmap)

        self.sagCoverPixmap = QPixmap(321, 301)
        self.sagCoverPixmap.fill(Qt.transparent)
        self.sagCoverLabel.setPixmap(self.sagCoverPixmap)

        self.corCoverPixmap = QPixmap(321, 301)
        self.corCoverPixmap.fill(Qt.transparent)
        self.corCoverLabel.setPixmap(self.corCoverPixmap)
        self.backButton.clicked.connect(self.backToLastScreen)
        self.newVoiBackButton.clicked.connect(self.backFromNewVoi)
        self.drawNewVoiButton.clicked.connect(self.drawNewVoi)
        self.saveVoiButton.clicked.connect(self.startSaveVoi)
        self.loadVoiButton.clicked.connect(self.loadVoi)

    def startSaveVoi(self):
        del self.saveVoiGUI
        self.saveVoiGUI = SaveVoiGUI()
        self.saveVoiGUI.voiSelectionGUI = self
        pathPieces = self.fullPath.split("/")
        fileName = pathPieces[-1]
        pathPieces[-1] = "nifti_segmentation_QUANTUS"
        pathPieces.append(fileName)

        path = pathPieces[0]
        for i in range(len(pathPieces) - 2):
            path = str(path + "/" + pathPieces[i + 1])
        if not os.path.exists(path):
            os.mkdir(path)

        self.saveVoiGUI.newFolderPathInput.setText(path)
        self.saveVoiGUI.newFileNameInput.setText(
            str(pathPieces[-1][:-7] + "_segmentation.nii.gz")
        )
        self.saveVoiGUI.show()

    def saveVoi(self, fileDestination, name, frame):
        segMask = np.zeros([self.x + 1, self.y + 1, self.z + 1, self.numSlices])
        self.pointsPlotted = [*set(self.pointsPlotted)]
        for point in self.pointsPlotted:
            segMask[point[0], point[1], point[2], frame] = 1

        affine = np.eye(4)
        niiarray = nib.Nifti1Image(segMask.astype("uint8"), affine)
        niiarray.header["descrip"] = self.imagePathInput.text()
        outputPath = os.path.join(fileDestination, name)
        if os.path.exists(outputPath):
            os.remove(outputPath)
        nib.save(niiarray, outputPath)

    def loadVoi(self):
        fileName, _ = QFileDialog.getOpenFileName(None, "Open File", filter="*.nii.gz")
        if fileName != "":
            nibIm = nib.load(fileName)
            if (
                self.imagePathInput.text().replace("'", '"')
                == str(nibIm.header["descrip"])[2:-1]
            ):
                mask = nibIm.get_fdata().astype(np.uint8)
            else:
                print("Mask is not compatible with this image")
                return
        else:
            return
        maskPoints = np.where(mask > 0)
        maskPoints = np.transpose(maskPoints)
        for point in maskPoints:
            self.maskCoverImg[point[0], point[1], point[2]] = [
                0,
                0,
                255,
                int(self.curAlpha),
            ]
            self.pointsPlotted.append((point[0], point[1], point[2]))
        self.curFrameIndex = maskPoints[0, 0]

        self.drawNewVoiButton.setHidden(True)
        self.loadVoiButton.setHidden(True)

        self.restartVoiButton.setHidden(False)
        self.continueButton.setHidden(False)
        self.saveVoiButton.setHidden(False)
        self.voiAlphaLabel.setHidden(False)
        self.voiAlphaOfLabel.setHidden(False)
        self.voiAlphaSpinBox.setHidden(False)
        self.voiAlphaStatus.setHidden(False)
        self.voiAlphaTotal.setHidden(False)
        self.restartVoiButton.clicked.connect(self.restartVoi)

        self.changeAxialSlices()
        self.changeSagSlices()
        self.changeCorSlices()
        self.update()

    def backFromNewVoi(self):
        self.drawRoiButton.setHidden(True)
        self.closeRoiButton.setHidden(True)
        self.redrawRoiButton.setHidden(True)
        self.interpolateVoiButton.setHidden(True)
        self.newVoiBackButton.setHidden(True)
        self.loadVoiButton.setHidden(False)
        self.drawNewVoiButton.setHidden(False)
        self.voiAdviceLabel.setHidden(True)
        self.undoLastPtButton.setHidden(True)

        self.pointsPlotted = []
        self.planesDrawn = []
        self.maskCoverImg.fill(0)
        self.changeAxialSlices()
        self.changeSagSlices()
        self.changeCorSlices()
        self.update()

    def drawNewVoi(self):
        self.drawRoiButton.setHidden(False)
        self.closeRoiButton.setHidden(False)
        self.undoLastPtButton.setHidden(False)
        self.interpolateVoiButton.setHidden(False)
        self.drawNewVoiButton.setHidden(True)
        self.loadVoiButton.setHidden(True)
        self.newVoiBackButton.setHidden(True)
        self.voiAdviceLabel.setHidden(False)
        self.newVoiBackButton.setHidden(False)

    def backToLastScreen(self):
        self.lastGui.dataFrame = self.dataFrame
        self.lastGui.timeconst = None
        self.lastGui.show()
        self.hide()

    def restartVoi(self):
        self.pointsPlotted = []
        self.planesDrawn = []
        self.maskCoverImg.fill(0)

        self.voiAlphaLabel.setHidden(True)
        self.voiAlphaOfLabel.setHidden(True)
        self.voiAlphaSpinBox.setHidden(True)
        self.voiAlphaStatus.setHidden(True)
        self.voiAlphaTotal.setHidden(True)
        self.restartVoiButton.setHidden(True)
        self.continueButton.setHidden(True)
        self.saveVoiButton.setHidden(True)

        self.drawRoiButton.setHidden(False)
        self.undoLastPtButton.setHidden(False)
        self.redrawRoiButton.setHidden(False)
        self.interpolateVoiButton.setHidden(False)
        self.voiAdviceLabel.setHidden(False)
        self.newVoiBackButton.setHidden(False)

        self.changeAxialSlices()
        self.changeSagSlices()
        self.changeCorSlices()
        self.backFromNewVoi()
        self.update()

    def computeTic(self):
        times = [i * self.timeconst for i in range(1, self.OGData4dImg.shape[3] + 1)]
        self.voxelScale = (
            self.header[1] * self.header[2] * self.header[3]
        )  # /1000/1000/1000 # mm^3
        self.pointsPlotted = [*set(self.pointsPlotted)]
        print("Voxel volume:", self.voxelScale)
        self.voxelScale *= len(self.pointsPlotted)
        print("Num voxels:", len(self.pointsPlotted))
        simplifiedMask = self.maskCoverImg[:, :, :, 2]
        TIC = ut.generate_TIC(
            self.OGData4dImg, simplifiedMask, times, 24.09, self.voxelScale
        )  # hard-coded for now

        # Bunch of checks
        if np.isnan(np.sum(TIC[:, 1])):
            print("STOPPED:NaNs in the VOI")
            return
        if np.isinf(np.sum(TIC[:, 1])):
            print("STOPPED:InFs in the VOI")
            return

        self.ticX = np.array([[TIC[i, 0], i] for i in range(len(TIC[:, 0]))])
        self.ticY = TIC[:, 1]
        self.ticAnalysisGui.ax.clear()
        self.ticAnalysisGui.ticX = []
        self.ticAnalysisGui.ticY = []
        self.ticAnalysisGui.removedPointsX = []
        self.ticAnalysisGui.removedPointsY = []
        self.ticAnalysisGui.selectedPoints = []
        self.ticAnalysisGui.t0Index = -2
        self.ticAnalysisGui.graph(self.ticX, self.ticY)

    def setFilenameDisplays(self, imageName):
        self.imagePathInput.setHidden(False)

        imFile = imageName.split("/")[-1]
        self.fullPath = imageName

        self.imagePathInput.setText(imFile)
        self.inputTextPath = imageName

    def curSliceSpinBoxValueChanged(self):
        if not self.sliceSliderChanged:
            self.sliceSpinBoxChanged = True
            self.sliceValueChanged()

    def curSliceSliderValueChanged(self):
        if not self.sliceSpinBoxChanged:
            self.sliceSliderChanged = True
            self.sliceValueChanged()

    def findSliceFromTime(self, inputtedTime):
        i = 0
        while i < len(self.sliceArray):
            if inputtedTime < self.sliceArray[i]:
                break
            i += 1
        if i == len(self.sliceArray):
            i -= 1
        elif i > 0:
            if (self.sliceArray[i] - inputtedTime) > (
                self.sliceArray[i - 1] - inputtedTime
            ):
                i -= 1
        if i < 0:
            i = 0
        return i

    def sliceValueChanged(self):
        if self.sliceSpinBoxChanged and self.sliceSliderChanged:
            self.sliceSpinBoxChanged = False
            self.sliceSliderChanged = False
            print("Error tracking slices")
            return
        if self.sliceSpinBoxChanged:
            self.curSliceIndex = self.findSliceFromTime(self.curSliceSpinBox.value())
            self.curSliceSlider.setValue(self.curSliceIndex)
            self.sliceSpinBoxChanged = False
        if self.sliceSliderChanged:
            self.curSliceIndex = int(self.curSliceSlider.value())
            self.curSliceSpinBox.setValue(self.sliceArray[self.curSliceIndex])
            self.sliceSliderChanged = False
        self.changeAxialSlices()
        self.changeSagSlices()
        self.changeCorSlices()

    def alphaValueChanged(self):
        self.curAlpha = int(self.voiAlphaSpinBox.value())
        self.voiAlphaSpinBoxChanged = False
        self.voiAlphaStatus.setValue(self.curAlpha)
        for i in range(len(self.pointsPlotted)):
            self.maskCoverImg[
                self.pointsPlotted[i][0],
                self.pointsPlotted[i][1],
                self.pointsPlotted[i][2],
                3,
            ] = self.curAlpha
        self.changeAxialSlices()
        self.changeSagSlices()
        self.changeCorSlices()

    def toggleIms(self):
        if self.toggleButton.isChecked():
            self.data4dImg = self.bmode4dIm
        else:
            self.data4dImg = self.OGData4dImg
        self.changeAxialSlices()
        self.changeSagSlices()
        self.changeCorSlices()
        self.updateCrosshair()

    def openImage(self, bmodePath):
        self.nibImg = nib.load(self.inputTextPath, mmap=False)
        self.dataNibImg = self.nibImg.get_fdata()
        self.dataNibImg = self.dataNibImg.astype(np.uint8)

        self.OGData4dImg = self.dataNibImg.copy()

        self.data4dImg = self.dataNibImg
        self.x, self.y, self.z, self.numSlices = self.data4dImg.shape
        self.maskCoverImg = np.zeros([self.x, self.y, self.z, 4])
        self.curSliceSlider.setMaximum(self.numSlices - 1)

        if bmodePath is not None:
            self.bmode4dIm = (
                nib.load(bmodePath, mmap=False).get_fdata().astype(np.uint8)
            )
            self.toggleButton.setHidden(False)
            self.toggleButton.setCheckable(True)
            self.toggleButton.clicked.connect(self.toggleIms)

        self.header = self.nibImg.header[
            "pixdim"
        ]  # [dims, voxel dims (3 vals), timeconst, 0, 0, 0], assume mm/pix
        self.sliceArray = np.round(
            [i * self.timeconst for i in range(1, self.OGData4dImg.shape[3] + 1)],
            decimals=2,
        )
        self.curSliceSpinBox.setMaximum(self.sliceArray[-1])
        self.curSliceTotal.setText(str(self.sliceArray[-1]))

        self.curSliceSpinBox.setValue(self.sliceArray[self.curSliceIndex])
        self.curSliceSlider.setValue(self.curSliceIndex)
        self.curSliceSlider.valueChanged.connect(self.curSliceSliderValueChanged)
        self.curSliceSpinBox.valueChanged.connect(self.curSliceSpinBoxValueChanged)

        self.x -= 1
        self.y -= 1
        self.z -= 1

        self.axialTotalFrames.setText(str(self.z + 1))
        self.sagittalTotalFrames.setText(str(self.x + 1))
        self.coronalTotalFrames.setText(str(self.y + 1))

        self.axialFrameNum.setText("1")
        self.sagittalFrameNum.setText("1")
        self.coronalFrameNum.setText("1")

        tempAx = self.maskCoverImg[:, :, 0, :]  # 2D data for axial
        tempAx = np.flipud(tempAx)  # flipud
        tempAx = np.rot90(tempAx, 3)  # rotate ccw 270
        tempAx = np.require(tempAx, np.uint8, "C")

        tempSag = self.maskCoverImg[0, :, :, :]  # 2D data for sagittal
        tempSag = np.flipud(tempSag)  # flipud
        tempSag = np.rot90(tempSag, 2)  # rotate ccw 180
        tempSag = np.fliplr(tempSag)
        tempSag = np.require(tempSag, np.uint8, "C")

        tempCor = self.maskCoverImg[:, 0, :, :]  # 2D data for coronal
        tempCor = np.rot90(tempCor, 1)  # rotate ccw 90
        tempCor = np.flipud(tempCor)  # flipud
        tempCor = np.require(tempCor, np.uint8, "C")

        self.maskAxH, self.maskAxW = tempAx[
            :, :, 0
        ].shape  # getting height and width for each plane
        self.maskSagH, self.maskSagW = tempSag[:, :, 0].shape
        self.maskCorH, self.maskCorW = tempCor[:, :, 0].shape

        self.maskBytesLineAx, _ = tempAx[
            :, :, 0
        ].strides  # in order to create proper QImage, need to know bytes/line
        self.maskBytesLineSag, _ = tempSag[:, :, 0].strides
        self.maskBytesLineCor, _ = tempCor[:, :, 0].strides

        self.curMaskAxIm = QImage(
            tempAx,
            self.maskAxW,
            self.maskAxH,
            self.maskBytesLineAx,
            QImage.Format_ARGB32,
        )  # creating QImage
        self.curMaskSagIm = QImage(
            tempSag,
            self.maskSagW,
            self.maskSagH,
            self.maskBytesLineSag,
            QImage.Format_ARGB32,
        )
        self.curMaskCorIm = QImage(
            tempCor,
            self.maskCorW,
            self.maskCorH,
            self.maskBytesLineCor,
            QImage.Format_ARGB32,
        )

        self.maskLayerAx.setPixmap(
            QPixmap.fromImage(self.curMaskAxIm).scaled(321, 301)
        )  # displaying QPixmap in the QLabels
        self.maskLayerSag.setPixmap(
            QPixmap.fromImage(self.curMaskSagIm).scaled(321, 301)
        )
        self.maskLayerCor.setPixmap(
            QPixmap.fromImage(self.curMaskCorIm).scaled(321, 301)
        )
        # self.axCoverLabel.setMouseTracking(True)
        # self.corCoverLabel.setMouseTracking(True)
        # self.sagCoverLabel.setMouseTracking(True)

        self.drawRoiButton.setCheckable(True)

        # getting initial image data for axial, sag, coronal slices
        self.data2dAx = self.data4dImg[:, :, 0, self.curSliceIndex]  # 2D data for axial
        self.data2dAx = np.flipud(self.data2dAx)  # flipud
        self.data2dAx = np.rot90(self.data2dAx, 3)  # rotate ccw 270
        self.data2dAx = np.require(self.data2dAx, np.uint8, "C")

        self.data2dSag = self.data4dImg[
            0, :, :, self.curSliceIndex
        ]  # 2D data for sagittal
        self.data2dSag = np.flipud(self.data2dSag)  # flipud
        self.data2dSag = np.rot90(self.data2dSag, 2)  # rotate ccw 180
        self.data2dSag = np.fliplr(self.data2dSag)
        self.data2dSag = np.require(self.data2dSag, np.uint8, "C")

        self.data2dCor = self.data4dImg[
            :, 0, :, self.curSliceIndex
        ]  # 2D data for coronal
        self.data2dCor = np.rot90(self.data2dCor, 1)  # rotate ccw 90
        self.data2dCor = np.flipud(self.data2dCor)  # flipud
        self.data2dCor = np.require(self.data2dCor, np.uint8, "C")

        (
            self.heightAx,
            self.widthAx,
        ) = self.data2dAx.shape  # getting height and width for each plane
        self.heightSag, self.widthSag = self.data2dSag.shape
        self.heightCor, self.widthCor = self.data2dCor.shape

        (
            self.bytesLineAx,
            _,
        ) = (
            self.data2dAx.strides
        )  # in order to create proper QImage, need to know bytes/line
        self.bytesLineSag, _ = self.data2dSag.strides
        self.bytesLineCor, _ = self.data2dCor.strides

        self.qImgAx = QImage(
            self.data2dAx,
            self.widthAx,
            self.heightAx,
            self.bytesLineAx,
            QImage.Format_Grayscale8,
        )  # creating QImage
        self.qImgSag = QImage(
            self.data2dSag,
            self.widthSag,
            self.heightSag,
            self.bytesLineSag,
            QImage.Format_Grayscale8,
        )
        self.qImgCor = QImage(
            self.data2dCor,
            self.widthCor,
            self.heightCor,
            self.bytesLineCor,
            QImage.Format_Grayscale8,
        )

        self.pixmapAx = QPixmap.fromImage(self.qImgAx).scaled(
            321, 301
        )  # creating QPixmap from QImage
        self.pixmapSag = QPixmap.fromImage(self.qImgSag).scaled(321, 301)
        self.pixmapCor = QPixmap.fromImage(self.qImgCor).scaled(321, 301)

        self.axialPlane.setPixmap(self.pixmapAx)  # displaying QPixmap in the QLabels
        self.sagPlane.setPixmap(self.pixmapSag)
        self.corPlane.setPixmap(self.pixmapCor)

        # self.scrolling = True
        # self.axCoverLabel.setCursor(Qt.BlankCursor)
        # self.sagCoverLabel.setCursor(Qt.BlankCursor)
        # self.corCoverLabel.setCursor(Qt.BlankCursor)
        self.newXVal = 0
        self.newYVal = 0
        self.newZVal = 0

        self.voiAlphaSpinBox.valueChanged.connect(self.alphaValueChanged)

        self.closeRoiButton.clicked.connect(
            self.acceptPolygon
        )  # called to exit the paint function
        self.undoLastPtButton.clicked.connect(
            self.undoLastPoint
        )  # deletes last drawn rectangle if on sag or cor slices

        self.redrawRoiButton.clicked.connect(self.undoLastRoi)
        self.drawRoiButton.clicked.connect(self.startRoiDraw)

    def changeAxialSlices(self):
        self.axialFrameNum.setText(str(self.newZVal + 1))

        self.data2dAx = self.data4dImg[
            :, :, self.newZVal, self.curSliceIndex
        ]  # , self.curSliceIndex #defining 2D data for axial
        self.data2dAx = np.flipud(self.data2dAx)  # flipud
        self.data2dAx = np.rot90(self.data2dAx, 3)  # rotate
        self.data2dAx = np.require(self.data2dAx, np.uint8, "C")

        self.bytesLineAx, _ = self.data2dAx.strides
        self.qImgAx = QImage(
            self.data2dAx,
            self.widthAx,
            self.heightAx,
            self.bytesLineAx,
            QImage.Format_Grayscale8,
        )

        tempAx = self.maskCoverImg[:, :, self.newZVal, :]  # 2D data for axial
        tempAx = np.flipud(tempAx)  # flipud
        tempAx = np.rot90(tempAx, 3)  # rotate ccw 270
        tempAx = np.require(tempAx, np.uint8, "C")

        self.curMaskAxIm = QImage(
            tempAx,
            self.maskAxW,
            self.maskAxH,
            self.maskBytesLineAx,
            QImage.Format_ARGB32,
        )  # creating QImage

        self.maskLayerAx.setPixmap(
            QPixmap.fromImage(self.curMaskAxIm).scaled(321, 301)
        )  # displaying QPixmap in the QLabels
        self.axialPlane.setPixmap(
            QPixmap.fromImage(self.qImgAx).scaled(321, 301)
        )  # otherwise, would just display the normal unmodified q_img

    def changeSagSlices(self):
        self.sagittalFrameNum.setText(str(self.newXVal + 1))

        self.data2dSag = self.data4dImg[
            self.newXVal, :, :, self.curSliceIndex
        ]  # , self.curSliceIndex
        self.data2dSag = np.flipud(self.data2dSag)  # flipud
        self.data2dSag = np.rot90(self.data2dSag, 2)  # rotate
        self.data2dSag = np.fliplr(self.data2dSag)
        self.data2dSag = np.require(self.data2dSag, np.uint8, "C")

        self.bytesLineSag, _ = self.data2dSag.strides
        self.qImgSag = QImage(
            self.data2dSag,
            self.widthSag,
            self.heightSag,
            self.bytesLineSag,
            QImage.Format_Grayscale8,
        )

        tempSag = self.maskCoverImg[self.newXVal, :, :, :]  # 2D data for sagittal
        tempSag = np.flipud(tempSag)  # flipud
        tempSag = np.rot90(tempSag, 2)  # rotate ccw 180
        tempSag = np.fliplr(tempSag)
        tempSag = np.require(tempSag, np.uint8, "C")

        self.curMaskSagIm = QImage(
            tempSag,
            self.maskSagW,
            self.maskSagH,
            self.maskBytesLineSag,
            QImage.Format_ARGB32,
        )

        self.maskLayerSag.setPixmap(
            QPixmap.fromImage(self.curMaskSagIm).scaled(321, 301)
        )
        self.sagPlane.setPixmap(QPixmap.fromImage(self.qImgSag).scaled(321, 301))

    def changeCorSlices(self):
        self.coronalFrameNum.setText(str(self.newYVal + 1))

        self.data2dCor = self.data4dImg[
            :, self.newYVal, :, self.curSliceIndex
        ]  # , self.curSliceIndex
        self.data2dCor = np.rot90(self.data2dCor, 1)  # rotate
        self.data2dCor = np.flipud(self.data2dCor)  # flipud
        self.data2dCor = np.require(self.data2dCor, np.uint8, "C")

        self.bytesLineCor, _ = self.data2dCor.strides
        self.qImgCor = QImage(
            self.data2dCor,
            self.widthCor,
            self.heightCor,
            self.bytesLineCor,
            QImage.Format_Grayscale8,
        )

        tempCor = self.maskCoverImg[:, self.newYVal, :, :]  # 2D data for coronal
        tempCor = np.rot90(tempCor, 1)  # rotate ccw 90
        tempCor = np.flipud(tempCor)  # flipud
        tempCor = np.require(tempCor, np.uint8, "C")

        self.curMaskCorIm = QImage(
            tempCor,
            self.maskCorW,
            self.maskCorH,
            self.maskBytesLineCor,
            QImage.Format_ARGB32,
        )

        self.maskLayerCor.setPixmap(
            QPixmap.fromImage(self.curMaskCorIm).scaled(321, 301)
        )
        self.corPlane.setPixmap(QPixmap.fromImage(self.qImgCor).scaled(321, 301))

    def updateCrosshair(self):
        scrolling = "none"
        # if self.scrolling:
        if (
            self.xCur < 721
            and self.xCur > 400
            and self.yCur < 341
            and self.yCur > 40
            and (self.painted == "none" or self.painted == "ax")
        ):
            self.actualX = int((self.xCur - 401) * (self.widthAx - 1) / 321)
            self.actualY = int((self.yCur - 41) * (self.heightAx - 1) / 301)
            scrolling = "ax"
            self.axCoverLabel.pixmap().fill(Qt.transparent)
            painter = QPainter(self.axCoverLabel.pixmap())
            painter.setPen(Qt.yellow)
            axVertLine = QLine(self.xCur - 401, 0, self.xCur - 401, 301)
            axLatLine = QLine(0, self.yCur - 41, 321, self.yCur - 41)
            painter.drawLines([axVertLine, axLatLine])
            painter.end()
        elif (
            self.xCur < 1131
            and self.xCur > 810
            and self.yCur < 341
            and self.yCur > 40
            and (self.painted == "none" or self.painted == "sag")
        ):
            self.actualX = int((self.xCur - 811) * (self.widthSag - 1) / 321)
            self.actualY = int((self.yCur - 41) * (self.heightSag - 1) / 301)
            scrolling = "sag"
            self.sagCoverLabel.pixmap().fill(Qt.transparent)
            painter = QPainter(self.sagCoverLabel.pixmap())
            painter.setPen(Qt.yellow)
            sagVertLine = QLine(self.xCur - 811, 0, self.xCur - 811, 301)
            sagLatLine = QLine(0, self.yCur - 41, 321, self.yCur - 41)
            painter.drawLines([sagVertLine, sagLatLine])
            painter.end()
        elif (
            self.xCur < 1131
            and self.xCur > 810
            and self.yCur < 711
            and self.yCur > 410
            and (self.painted == "none" or self.painted == "cor")
        ):
            self.actualX = int((self.xCur - 811) * (self.widthCor - 1) / 321)
            self.actualY = int((self.yCur - 411) * (self.heightCor - 1) / 301)
            scrolling = "cor"
            self.corCoverLabel.pixmap().fill(Qt.transparent)
            painter = QPainter(self.corCoverLabel.pixmap())
            painter.setPen(Qt.yellow)
            corVertLine = QLine(self.xCur - 811, 0, self.xCur - 811, 301)
            corLatLine = QLine(0, self.yCur - 411, 321, self.yCur - 411)
            painter.drawLines([corVertLine, corLatLine])
            painter.end()

        if scrolling == "ax":
            self.newXVal = self.actualX
            self.newYVal = self.actualY
            self.changeSagSlices()
            self.changeCorSlices()
            self.sagCoverLabel.pixmap().fill(Qt.transparent)
            painter = QPainter(self.sagCoverLabel.pixmap())
            painter.setPen(Qt.yellow)
            sagVertLine = QLine(
                int(self.newZVal / self.z * 321),
                0,
                int(self.newZVal / self.z * 321),
                301,
            )
            sagLatLine = QLine(
                0,
                int(self.newYVal / self.y * 301),
                321,
                int(self.newYVal / self.y * 301),
            )
            painter.drawLines([sagVertLine, sagLatLine])
            painter.end()

            self.corCoverLabel.pixmap().fill(Qt.transparent)
            painter = QPainter(self.corCoverLabel.pixmap())
            painter.setPen(Qt.yellow)
            corVertLine = QLine(
                int(self.newXVal / self.x * 321),
                0,
                int(self.newXVal / self.x * 321),
                301,
            )
            corLatLine = QLine(
                0,
                int(self.newZVal / self.z * 301),
                321,
                int(self.newZVal / self.z * 301),
            )
            painter.drawLines([corVertLine, corLatLine])
            painter.end()
            self.update()

        elif scrolling == "sag":
            self.newZVal = self.actualX
            self.newYVal = self.actualY
            self.changeAxialSlices()
            self.changeCorSlices()
            self.axCoverLabel.pixmap().fill(Qt.transparent)
            painter = QPainter(self.axCoverLabel.pixmap())
            painter.setPen(Qt.yellow)
            axVertLine = QLine(
                int(self.newXVal / self.x * 321),
                0,
                int(self.newXVal / self.x * 321),
                301,
            )
            axLatLine = QLine(
                0,
                int(self.newYVal / self.y * 301),
                321,
                int(self.newYVal / self.y * 301),
            )
            painter.drawLines([axVertLine, axLatLine])
            painter.end()

            self.corCoverLabel.pixmap().fill(Qt.transparent)
            painter = QPainter(self.corCoverLabel.pixmap())
            painter.setPen(Qt.yellow)
            corVertLine = QLine(
                int(self.newXVal / self.x * 321),
                0,
                int(self.newXVal / self.x * 321),
                301,
            )
            corLatLine = QLine(
                0,
                int(self.newZVal / self.z * 301),
                321,
                int(self.newZVal / self.z * 301),
            )
            painter.drawLines([corVertLine, corLatLine])
            painter.end()
            self.update()

        elif scrolling == "cor":
            self.newXVal = self.actualX
            self.newZVal = self.actualY
            self.changeAxialSlices()
            self.changeSagSlices()
            self.axCoverLabel.pixmap().fill(Qt.transparent)
            painter = QPainter(self.axCoverLabel.pixmap())
            painter.setPen(Qt.yellow)
            axVertLine = QLine(
                int(self.newXVal / self.x * 321),
                0,
                int(self.newXVal / self.x * 321),
                301,
            )
            axLatLine = QLine(
                0,
                int(self.newYVal / self.y * 301),
                321,
                int(self.newYVal / self.y * 301),
            )
            painter.drawLines([axVertLine, axLatLine])
            painter.end()

            self.sagCoverLabel.pixmap().fill(Qt.transparent)
            painter = QPainter(self.sagCoverLabel.pixmap())
            painter.setPen(Qt.yellow)
            sagVertLine = QLine(
                int(self.newZVal / self.z * 321),
                0,
                int(self.newZVal / self.z * 321),
                301,
            )
            sagLatLine = QLine(
                0,
                int(self.newYVal / self.y * 301),
                321,
                int(self.newYVal / self.y * 301),
            )
            painter.drawLines([sagVertLine, sagLatLine])
            painter.end()
            self.update()

    def mousePressEvent(self, event):
        self.xCur = event.x()
        self.yCur = event.y()
        self.newPointPlotted = False
        if self.drawRoiButton.isChecked():
            # Plot ROI points
            if (
                self.xCur < 721
                and self.xCur > 400
                and self.yCur < 341
                and self.yCur > 40
            ) and (self.painted == "none" or self.painted == "ax"):
                self.actualX = int((self.xCur - 401) * (self.widthAx - 1) / 321)
                self.actualY = int((self.yCur - 41) * (self.heightAx - 1) / 301)
                self.maskCoverImg[self.actualX, self.actualY, self.newZVal] = [
                    0,
                    0,
                    255,
                    int(self.curAlpha),
                ]
                self.curPointsPlottedX.append(self.actualX)
                self.curPointsPlottedY.append(self.actualY)
                self.newPointPlotted = True
                self.painted = "ax"
                self.curROIDrawn = False
            elif (
                event.x() < 1131
                and event.x() > 810
                and event.y() < 341
                and event.y() > 40
            ) and (self.painted == "none" or self.painted == "sag"):
                self.actualX = int((self.xCur - 811) * (self.widthSag - 1) / 321)
                self.actualY = int((self.yCur - 41) * (self.heightSag - 1) / 301)
                self.maskCoverImg[self.newXVal, self.actualY, self.actualX] = [
                    0,
                    0,
                    255,
                    int(self.curAlpha),
                ]
                self.curPointsPlottedX.append(self.actualX)
                self.curPointsPlottedY.append(self.actualY)
                self.newPointPlotted = True
                self.painted = "sag"
                self.curROIDrawn = False
            elif (
                event.x() < 1131
                and event.x() > 810
                and event.y() < 711
                and event.y() > 410
            ) and (self.painted == "none" or self.painted == "cor"):
                self.actualX = int((self.xCur - 811) * (self.widthCor - 1) / 321)
                self.actualY = int((self.yCur - 411) * (self.heightCor - 1) / 301)
                self.maskCoverImg[self.actualX, self.newYVal, self.actualY] = [
                    0,
                    0,
                    255,
                    int(self.curAlpha),
                ]
                self.curPointsPlottedX.append(self.actualX)
                self.curPointsPlottedY.append(self.actualY)
                self.newPointPlotted = True
                self.painted = "cor"
                self.curROIDrawn = False
            self.changeSagSlices()
            self.changeCorSlices()
            self.changeAxialSlices()
            self.updateCrosshair()

    def mouseMoveEvent(self, event):
        self.xCur = event.x()
        self.yCur = event.y()
        self.updateCrosshair()

    def acceptPolygon(self):
        # 2d interpolation
        if len(self.curPointsPlottedX):
            self.drawRoiButton.setChecked(False)

            # remove duplicate points
            points = np.transpose(
                np.array([self.curPointsPlottedX, self.curPointsPlottedY])
            )
            points = removeDuplicates(points)
            [self.curPointsPlottedX, self.curPointsPlottedY] = np.transpose(points)
            self.curPointsPlottedX = list(self.curPointsPlottedX)
            self.curPointsPlottedY = list(self.curPointsPlottedY)

            self.curPointsPlottedX.append(self.curPointsPlottedX[0])
            self.curPointsPlottedY.append(self.curPointsPlottedY[0])
            self.maskCoverImg.fill(0)
            x, y = calculateSpline(self.curPointsPlottedX, self.curPointsPlottedY)
            newROI = []
            for i in range(len(x)):
                if self.painted == "ax":
                    if len(newROI) == 0 or newROI[-1] != (
                        int(x[i]),
                        int(y[i]),
                        self.newZVal,
                    ):
                        newROI.append((int(x[i]), int(y[i]), self.newZVal))
                elif self.painted == "sag":
                    if len(newROI) == 0 or newROI[-1] != (
                        self.newXVal,
                        int(y[i]),
                        int(x[i]),
                    ):
                        newROI.append((self.newXVal, int(y[i]), int(x[i])))
                elif self.painted == "cor":
                    if len(newROI) == 0 or newROI[-1] != (
                        int(x[i]),
                        self.newYVal,
                        int(y[i]),
                    ):
                        newROI.append((int(x[i]), self.newYVal, int(y[i])))
            self.pointsPlotted.append(newROI)
            for i in range(len(self.pointsPlotted)):
                for j in range(len(self.pointsPlotted[i])):
                    self.maskCoverImg[
                        self.pointsPlotted[i][j][0],
                        self.pointsPlotted[i][j][1],
                        self.pointsPlotted[i][j][2],
                    ] = [0, 0, 255, int(self.curAlpha)]
            self.changeAxialSlices()
            self.changeSagSlices()
            self.changeCorSlices()
            self.curPointsPlottedX = []
            self.curPointsPlottedY = []
            self.planesDrawn.append(self.painted)
            self.painted = "none"
            self.curROIDrawn = True
            self.redrawRoiButton.setHidden(False)
            self.closeRoiButton.setHidden(True)
            # if (len(self.planesDrawn) == 1) or (len(self.planesDrawn) >= 3 and ((self.planesDrawn[0]!=self.planesDrawn[1]) and (self.planesDrawn[1]!=self.planesDrawn[2]) and (self.planesDrawn[2]!=self.planesDrawn[0]))):
            if len(self.planesDrawn):
                self.interpolateVoiButton.clicked.connect(self.voi3dInterpolation)

    def undoLastPoint(self):
        if len(self.curPointsPlottedX) != 0:
            self.maskCoverImg[self.curPointsPlottedX[-1]]
            self.curPointsPlottedX.pop()
            self.curPointsPlottedY.pop()
            self.maskCoverImg.fill(0)
            for i in range(len(self.pointsPlotted)):
                for j in range(len(self.pointsPlotted[i])):
                    self.maskCoverImg[
                        self.pointsPlotted[i][j][0],
                        self.pointsPlotted[i][j][1],
                        self.pointsPlotted[i][j][2],
                    ] = [0, 0, 255, int(self.curAlpha)]
            for i in range(len(self.curPointsPlottedX)):
                if self.painted == "ax":
                    self.maskCoverImg[
                        int(self.curPointsPlottedX[i]),
                        int(self.curPointsPlottedY[i]),
                        self.newZVal,
                    ] = [0, 0, 255, int(self.curAlpha)]
                elif self.painted == "sag":
                    self.maskCoverImg[
                        self.newXVal,
                        int(self.curPointsPlottedY[i]),
                        int(self.curPointsPlottedX[i]),
                    ] = [0, 0, 255, int(self.curAlpha)]
                elif self.painted == "cor":
                    self.maskCoverImg[
                        int(self.curPointsPlottedX[i]),
                        self.newYVal,
                        int(self.curPointsPlottedY[i]),
                    ] = [0, 0, 255, int(self.curAlpha)]

            self.changeAxialSlices()
            self.changeSagSlices()
            self.changeCorSlices()
        if len(self.curPointsPlottedX) == 0:
            self.painted == "none"

    def moveToTic(self):
        self.ticAnalysisGui.timeLine = None
        self.computeTic()
        self.ticAnalysisGui.pointsPlotted = self.pointsPlotted
        self.ticAnalysisGui.voxelScale = self.voxelScale
        self.ticAnalysisGui.dataFrame = self.dataFrame
        self.ticAnalysisGui.data4dImg = self.data4dImg
        self.ticAnalysisGui.curSliceIndex = self.curSliceIndex
        self.ticAnalysisGui.newXVal = self.newXVal
        self.ticAnalysisGui.newYVal = self.newYVal
        self.ticAnalysisGui.newZVal = self.newZVal
        self.ticAnalysisGui.x = self.x
        self.ticAnalysisGui.y = self.y
        self.ticAnalysisGui.z = self.z
        self.ticAnalysisGui.maskCoverImg = self.maskCoverImg
        self.ticAnalysisGui.widthAx = self.widthAx
        self.ticAnalysisGui.heightAx = self.heightAx
        self.ticAnalysisGui.bytesLineAx = self.bytesLineAx
        self.ticAnalysisGui.maskAxW = self.maskAxW
        self.ticAnalysisGui.maskAxH = self.maskAxH
        self.ticAnalysisGui.maskBytesLineAx = self.maskBytesLineAx
        self.ticAnalysisGui.widthSag = self.widthSag
        self.ticAnalysisGui.heightSag = self.heightSag
        self.ticAnalysisGui.bytesLineSag = self.bytesLineSag
        self.ticAnalysisGui.maskSagW = self.maskSagW
        self.ticAnalysisGui.maskSagH = self.maskSagH
        self.ticAnalysisGui.maskBytesLineSag = self.maskBytesLineSag
        self.ticAnalysisGui.widthCor = self.widthCor
        self.ticAnalysisGui.heightCor = self.heightCor
        self.ticAnalysisGui.bytesLineCor = self.bytesLineCor
        self.ticAnalysisGui.maskCorW = self.maskCorW
        self.ticAnalysisGui.maskCorH = self.maskCorH
        self.ticAnalysisGui.maskBytesLineCor = self.maskBytesLineCor
        self.ticAnalysisGui.sliceArray = self.sliceArray
        self.voiAlphaSpinBox.setValue(100)
        self.alphaValueChanged()
        self.ticAnalysisGui.changeAxialSlices()
        self.ticAnalysisGui.changeSagSlices()
        self.ticAnalysisGui.changeCorSlices()
        self.ticAnalysisGui.deSelectLastPointButton.setHidden(True)
        self.ticAnalysisGui.removeSelectedPointsButton.setHidden(True)
        self.ticAnalysisGui.restoreLastPointsButton.setHidden(True)
        self.ticAnalysisGui.acceptTicButton.setHidden(True)
        self.ticAnalysisGui.acceptT0Button.setHidden(True)
        self.ticAnalysisGui.t0Slider.setHidden(True)
        self.ticAnalysisGui.selectT0Button.setHidden(False)
        self.ticAnalysisGui.automaticallySelectT0Button.setHidden(False)
        self.ticAnalysisGui.show()
        self.ticAnalysisGui.lastGui = self
        self.ticAnalysisGui.imagePathInput.setText(self.imagePathInput.text())
        self.hide()

    def startRoiDraw(self):
        if self.drawRoiButton.isChecked():
            self.closeRoiButton.setHidden(False)
            self.redrawRoiButton.setHidden(True)
        elif not len(self.curPointsPlottedX):
            self.closeRoiButton.setHidden(True)
            self.redrawRoiButton.setHidden(False)

    def undoLastRoi(self):
        if len(self.planesDrawn):
            if len(self.pointsPlotted) > 0:
                self.pointsPlotted.pop()
                self.planesDrawn.pop()
                self.maskCoverImg.fill(0)
                for i in range(len(self.pointsPlotted)):
                    for j in range(len(self.pointsPlotted[i])):
                        self.maskCoverImg[
                            self.pointsPlotted[i][j][0],
                            self.pointsPlotted[i][j][1],
                            self.pointsPlotted[i][j][2],
                        ] = [0, 0, 255, int(self.curAlpha)]
                self.changeAxialSlices()
                self.changeSagSlices()
                self.changeCorSlices()
            self.update()

    def voi3dInterpolation(self):
        if len(self.pointsPlotted) == len(self.planesDrawn):
            if len(self.planesDrawn):
                if len(self.planesDrawn) >= 3:
                    points = calculateSpline3D(
                        list(chain.from_iterable(self.pointsPlotted))
                    )
                elif len(self.planesDrawn) == 2:
                    return
                else:
                    points = set()
                    for group in np.array(self.pointsPlotted):
                        for point in group:
                            points.add(tuple(point))

                self.pointsPlotted = []
                self.maskCoverImg.fill(0)

                for point in points:
                    if max(self.data4dImg[tuple(point)]) != 0:
                        self.maskCoverImg[tuple(point)] = [
                            0,
                            0,
                            255,
                            int(self.curAlpha),
                        ]
                        self.pointsPlotted.append(tuple(point))
                if len(self.pointsPlotted) == 0:
                    print("VOI not in US image.\nDraw new VOI over US image")
                    self.maskCoverImg.fill(0)
                    self.changeAxialSlices()
                    self.changeSagSlices()
                    self.changeCorSlices()
                    return

            mask = np.zeros(
                (
                    self.maskCoverImg.shape[0],
                    self.maskCoverImg.shape[1],
                    self.maskCoverImg.shape[2],
                )
            )

            for point in self.pointsPlotted:
                mask[point] = 1
            for i in range(mask.shape[2]):
                border = np.where(mask[:, :, i] == 1)
                if (
                    (not len(border[0]))
                    or (max(border[0]) == min(border[0]))
                    or (max(border[1]) == min(border[1]))
                ):
                    continue
                border = np.array(border).T
                hull = ConvexHull(border)
                vertices = border[hull.vertices]
                shape = vertices.shape
                vertices = np.reshape(
                    np.append(vertices, vertices[0]), (shape[0] + 1, shape[1])
                )

                # Linear interpolation of 2d convex hull
                tck, _ = interpolate.splprep(vertices.T, s=0.0, k=1)
                splineX, splineY = np.array(
                    interpolate.splev(np.linspace(0, 1, 1000), tck)
                )

                mask[:, :, i] = np.zeros((mask.shape[0], mask.shape[1]))
                for j in range(len(splineX)):
                    mask[int(splineX[j]), int(splineY[j]), i] = 1
                filledMask = binary_fill_holes(mask[:, :, i])
                mask[:, :, i] = binary_fill_holes(mask[:, :, i])
                maskPoints = np.array(np.where(filledMask > 0))
                for j in range(len(maskPoints[0])):
                    self.maskCoverImg[maskPoints[0][j], maskPoints[1][j], i] = [
                        0,
                        0,
                        255,
                        int(self.curAlpha),
                    ]
                    self.pointsPlotted.append((maskPoints[0][j], maskPoints[1][j], i))

            self.changeAxialSlices()
            self.changeSagSlices()
            self.changeCorSlices()
            self.interpolateVoiButton.setHidden(True)
            self.continueButton.setHidden(False)

            self.drawRoiButton.setHidden(True)
            self.undoLastPtButton.setHidden(True)
            self.redrawRoiButton.setHidden(True)
            self.voiAdviceLabel.setHidden(True)
            self.newVoiBackButton.setHidden(True)

            self.voiAlphaLabel.setHidden(False)
            self.voiAlphaOfLabel.setHidden(False)
            self.voiAlphaSpinBox.setHidden(False)
            self.voiAlphaStatus.setHidden(False)
            self.voiAlphaTotal.setHidden(False)
            self.restartVoiButton.setHidden(False)
            self.saveVoiButton.setHidden(False)
            self.restartVoiButton.clicked.connect(self.restartVoi)


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


def ellipsoidFitLS(pos):
    # centre coordinates on origin
    pos = pos - np.mean(pos, axis=0)

    # build our regression matrix
    A = pos**2

    # vector of ones
    Ones = np.ones(len(A))

    # least squares solver
    B, _, _, _ = np.linalg.lstsq(A, Ones, rcond=None)

    # solving for a, b, c
    a_ls = np.sqrt(1.0 / B[0])
    b_ls = np.sqrt(1.0 / B[1])
    c_ls = np.sqrt(1.0 / B[2])

    return (a_ls, b_ls, c_ls)


def calculateSpline3D(points):
    # Calculate ellipsoid of best fit
    # points = np.array(points)
    # a,b,c = ellipsoidFitLS(points)
    # output = set()

    # u = np.linspace(0., np.pi*2., 1000)
    # v = np.linspace(0., np.pi, 1000)
    # u, v = np.meshgrid(u,v)

    # x = a*np.cos(u)*np.sin(v)
    # y = b*np.sin(u)*np.sin(v)
    # z = c*np.cos(v)

    # # turn this data into 1d arrays
    # x = x.flatten()
    # y = y.flatten()
    # z = z.flatten()
    # x += np.mean(points, axis=0)[0]
    # y += np.mean(points, axis=0)[1]
    # z += np.mean(points, axis=0)[2]

    # for i in range(len(x)):
    #     output.add((int(x[i]), int(y[i]), int(z[i])))
    # return output

    cloud = pv.PolyData(points, force_float=False)
    volume = cloud.delaunay_3d(alpha=100.0)
    shell = volume.extract_geometry()
    final = shell.triangulate()
    final.smooth(n_iter=1000)
    faces = final.faces.reshape((-1, 4))
    faces = faces[:, 1:]
    arr = final.points[faces]

    arr = np.array(arr)

    output = set()
    for tri in arr:
        slope_2 = tri[2] - tri[1]
        start_2 = tri[1]
        slope_3 = tri[0] - tri[1]
        start_3 = tri[1]
        for i in range(100, -1, -1):
            bound_one = start_2 + ((i / 100) * slope_2)
            bound_two = start_3 + ((i / 100) * slope_3)
            cur_slope = bound_one - bound_two
            cur_start = bound_two
            for j in range(100, -1, -1):
                cur_pos = cur_start + ((j / 100) * cur_slope)
                output.add((int(cur_pos[0]), int(cur_pos[1]), int(cur_pos[2])))

    return output


def removeDuplicates(ar):
    # Credit: https://stackoverflow.com/questions/480214/how-do-i-remove-duplicates-from-a-list-while-preserving-order
    seen = set()
    seen_add = seen.add
    return [x for x in ar if not (tuple(x) in seen or seen_add(tuple(x)))]


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    # selectWindow = QWidget()
    ui = VoiSelectionGUI()
    # ui.selectImage.show()
    ui.show()
    sys.exit(app.exec_())
