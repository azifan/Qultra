import platform

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import nibabel as nib
from PIL.ImageQt import ImageQt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QWidget, QFileDialog, QHBoxLayout
from PyQt5.QtGui import QImage, QPixmap, QPainter, QCursor, QResizeEvent
from PyQt5.QtCore import QLine, Qt, QPoint, pyqtSlot

import src.Utils.lognormalFunctions as lf
from src.CeusTool3d.ceusAnalysis_ui import Ui_ceusAnalysis
from src.CeusTool3d.exportData_ui_helper import ExportDataGUI
from src.CeusTool3d.legend_ui_helper import LegendDisplay
from src.DataLayer.qtSupport import MouseTracker, qImToPIL


system = platform.system()


class CeusAnalysisGUI(Ui_ceusAnalysis, QWidget):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setLayout(self.fullScreenLayout)

        self.lastGui = None; self.pointsPlotted = None
        self.data4dImg = None; self.curSliceIndex = None
        self.newXVal = None; self.newYVal = None; self.newZVal = None
        self.x = None; self.y = None; self.z = None
        self.maskCoverImg = None; self.sliceArray = None
        self.voxelScale = None; self.sliceSpinBoxChanged = False
        self.sliceSliderChanged = False; self.masterParamap = None
        self.paramapPoints = None; self.curParamap = None; self.cmap = None
        self.newData = None; self.exportDataGUI = None
        self.bmode4dImg = None; self.ceus4dImg = None

        self.hideParamapDisplayLayout(); self.hideTicDisplayLayout()
        self.showResultsViewLayout(); self.navigatingLabel.hide()

        self.horizLayout = QHBoxLayout(self.ticDisplay)
        self.fig = plt.figure()
        self.canvas = FigureCanvas(self.fig)
        self.horizLayout.addWidget(self.canvas)
        self.canvas.draw()
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel("Time (s)", fontsize=4, labelpad=0.5)
        self.ax.set_ylabel("Signal Amplitude", fontsize=4, labelpad=0.5)
        self.ax.set_title("Time Intensity Curve (TIC)", fontsize=5, pad=1.5)
        self.ax.tick_params("both", pad=0.3, labelsize=3.6)
        plt.xticks(fontsize=3)
        plt.yticks(fontsize=3)

        self.voiAlphaSpinBox.setValue(100)
        self.aucParamapButton.setCheckable(True)
        self.peParamapButton.setCheckable(True)
        self.mttParamapButton.setCheckable(True)
        self.tpParamapButton.setCheckable(True)
        self.showLegendButton.setCheckable(True)
        self.showHideCrossButton.setCheckable(True)
        
        self.backButton.clicked.connect(self.backToLastScreen)
        self.exportDataButton.clicked.connect(self.moveToExport)
        self.curSliceSlider.valueChanged.connect(self.curSliceSliderValueChanged)
        self.curSliceSpinBox.valueChanged.connect(self.curSliceSpinBoxValueChanged)
        self.voiAlphaSpinBox.valueChanged.connect(self.alphaValueChanged)
        self.showTicButton.clicked.connect(self.showTic)
        self.ticBackButton.clicked.connect(self.backFromTic)
        self.loadParamapsButton.clicked.connect(self.loadParamaps)
        self.aucParamapButton.clicked.connect(self.displayAuc)
        self.peParamapButton.clicked.connect(self.displayPe)
        self.tpParamapButton.clicked.connect(self.displayTp)
        self.mttParamapButton.clicked.connect(self.displayMtt)
        self.paramapBackButton.clicked.connect(self.backFromParamap)
        self.showLegendButton.clicked.connect(self.displayLegend)
        self.showHideCrossButton.clicked.connect(self.showHideCross)
        self.toggleButton.clicked.connect(self.toggleIms)

        trackerAx = MouseTracker(self.axialPlane)
        trackerAx.positionChanged.connect(self.axCoordChanged)
        trackerSag = MouseTracker(self.sagPlane)
        trackerSag.positionChanged.connect(self.sagCoordChanged)
        trackerCor = MouseTracker(self.corPlane)
        trackerCor.positionChanged.connect(self.corCoordChanged) 

    def toggleIms(self):
        if self.toggleButton.isChecked():
            self.data4dImg = self.bmode4dImg
        else:
            self.data4dImg = self.ceus4dImg
        self.updateCrosshairs() 

    def hideTicDisplayLayout(self):
        self.ticBackButton.hide()
        self.ticDisplay.hide()
    
    def showTicDisplayLayout(self):
        self.ticBackButton.show()
        self.ticDisplay.show()

    def hideResultsViewLayout(self):
        self.loadParamapsButton.hide()
        self.showTicButton.hide()

    def showResultsViewLayout(self):
        self.loadParamapsButton.show()
        self.showTicButton.show()
    
    def hideParamapDisplayLayout(self):
        self.aucParamapButton.hide()
        self.mttParamapButton.hide()
        self.paramapBackButton.hide()
        self.peParamapButton.hide()
        self.showLegendButton.hide()
        self.tpParamapButton.hide()
        self.chooseParamapLabel.hide()

    def showParamapDisplayLayout(self):
        self.aucParamapButton.show()
        self.mttParamapButton.show()
        self.paramapBackButton.show()
        self.peParamapButton.show()
        self.showLegendButton.show()
        self.tpParamapButton.show()
        self.chooseParamapLabel.show()

    @pyqtSlot(QPoint)
    def axCoordChanged(self, pos):
        if self.observingLabel.isHidden():
            xdiff = self.axialPlane.width() - self.axialPlane.pixmap().width()
            ydiff = self.axialPlane.height() - self.axialPlane.pixmap().height()
            xCoord = pos.x() - xdiff/2; yCoord = pos.y() - ydiff/2

            if xCoord < 0 or yCoord < 0 or xCoord >= self.axialPlane.pixmap().width() or yCoord >= self.axialPlane.pixmap().height():
                return
            self.newXVal = int((xCoord/self.axialPlane.pixmap().width()) * self.x)
            self.newYVal = int((yCoord/self.axialPlane.pixmap().height()) * self.y)
            self.updateCrosshairs()

    @pyqtSlot(QPoint)
    def sagCoordChanged(self, pos):
        if self.observingLabel.isHidden():
            xdiff = self.sagPlane.width() - self.sagPlane.pixmap().width()
            ydiff = self.sagPlane.height() - self.sagPlane.pixmap().height()
            xCoord = pos.x() - xdiff/2; yCoord = pos.y() - ydiff/2

            if xCoord < 0 or yCoord < 0 or xCoord >= self.sagPlane.pixmap().width() or yCoord >= self.sagPlane.pixmap().height():
                return
            self.newZVal = int((xCoord/self.sagPlane.pixmap().width()) * self.z)
            self.newYVal = int((yCoord/self.sagPlane.pixmap().height()) * self.y)
            self.updateCrosshairs()
        
    @pyqtSlot(QPoint)
    def corCoordChanged(self, pos):
        if self.observingLabel.isHidden():
            xdiff = self.corPlane.width() - self.corPlane.pixmap().width()
            ydiff = self.corPlane.height() - self.corPlane.pixmap().height()
            xCoord = pos.x() - xdiff/2; yCoord = pos.y() - ydiff/2

            if xCoord < 0 or yCoord < 0 or xCoord >= self.corPlane.pixmap().width() or yCoord >= self.corPlane.pixmap().height():
                return
            self.newXVal = int((xCoord/self.corPlane.pixmap().width()) * self.x)
            self.newZVal = int((yCoord/self.corPlane.pixmap().height()) * self.z)
            self.updateCrosshairs()

    def showHideCross(self):
        if self.showHideCrossButton.isChecked():
            pilIms = [self.imAxPIL, self.imSagPIL, self.imCorPIL]
            pixmaps = [self.pixmapAx, self.pixmapSag, self.pixmapCor]
            for i, pilIm in enumerate(pilIms):
                pixmaps[i] = QPixmap.fromImage(ImageQt(pilIm))
            self.changeAxialSlices(); self.changeSagSlices(); self.changeCorSlices()
            self.axialPlane.setCursor(QCursor(Qt.ArrowCursor))
            self.sagPlane.setCursor(QCursor(Qt.ArrowCursor))
            self.corPlane.setCursor(QCursor(Qt.ArrowCursor))
        else:
            if self.observingLabel.isHidden():
                self.axialPlane.setCursor(QCursor(Qt.BlankCursor))
                self.sagPlane.setCursor(QCursor(Qt.BlankCursor))
                self.corPlane.setCursor(QCursor(Qt.BlankCursor))
            self.updateCrosshairs()

    def backFromParamap(self):
        self.hideParamapDisplayLayout(); self.showResultsViewLayout()

        self.aucParamapButton.setChecked(False); self.peParamapButton.setChecked(False)
        self.tpParamapButton.setChecked(False); self.mttParamapButton.setChecked(False)
        self.showLegendButton.setChecked(False); self.legendDisplay.hide()

        self.masterParamap = None
        self.clearParamap()

    def clearParamap(self):
        self.cmap = None
        self.legendDisplay.legendFrame.hide()
        self.updateCrosshairs()

    def displayLegend(self):
        if not self.showLegendButton.isChecked():
            self.legendDisplay.hide()
        else:
            self.legendDisplay.show()

    def displayAuc(self):
        if not self.aucParamapButton.isChecked():
            self.clearParamap()
        else:
            if self.peParamapButton.isChecked():
                self.peParamapButton.setChecked(False)
            if self.mttParamapButton.isChecked():
                self.mttParamapButton.setChecked(False)
            if self.tpParamapButton.isChecked():
                self.tpParamapButton.setChecked(False)

            self.cmap = plt.get_cmap("viridis").colors

            arr = np.linspace(0, 100, 1000).reshape((1000, 1))
            self.legendDisplay.ax.clear()
            new_cmap1 = self.legendDisplay.truncate_colormap(plt.get_cmap("viridis"))
            self.legendDisplay.ax.imshow(
                arr, aspect="auto", cmap=new_cmap1, origin="lower"
            )
            self.legendDisplay.ax.tick_params(axis="y", labelsize=7, pad=0.5)
            self.legendDisplay.ax.set_xticks([])
            self.legendDisplay.ax.set_yticks([0, 250, 500, 750, 1000])
            self.legendDisplay.ax.set_yticklabels(
                [
                    np.round(self.minAuc, decimals=1),
                    np.round(
                        self.minAuc + ((self.maxAuc - self.minAuc) / 4), decimals=1
                    ),
                    np.round(
                        self.minAuc + ((self.maxAuc - self.minAuc) / 4), decimals=1
                    ),
                    np.round(
                        self.minAuc + (3 * (self.maxAuc - self.minAuc) / 4), decimals=1
                    ),
                    np.round(self.maxAuc, decimals=1),
                ]
            )
            self.legendDisplay.figure.subplots_adjust(
                left=0.4, right=0.95, bottom=0.05, top=0.96
            )
            self.legendDisplay.canvas.draw()
            self.legendDisplay.legendFrame.setHidden(False)

            for point in self.pointsPlotted:
                if self.maxAuc == self.minAuc:
                    color = self.cmap[125]
                else:
                    aucVal = self.masterParamap[point[0], point[1], point[2], 0]
                    if not self.masterParamap[point[0], point[1], point[2], 3]:
                        color = [0, 0, 0]  # window not able to be fit
                    elif self.maxAuc == self.minAuc:
                        color = self.cmap[125]
                    else:
                        color = self.cmap[
                            int(
                                (255 / (self.maxAuc - self.minAuc))
                                * (aucVal - self.minAuc)
                            )
                        ]
                self.paramap[point[0], point[1], point[2]] = [
                    int(color[2] * 255),
                    int(color[1] * 255),
                    int(color[0] * 255),
                    int(self.curAlpha),
                ]

            self.updateCrosshairs()

    def displayPe(self):
        if not self.peParamapButton.isChecked():
            self.clearParamap()
        else:
            if self.aucParamapButton.isChecked():
                self.aucParamapButton.setChecked(False)
            if self.mttParamapButton.isChecked():
                self.mttParamapButton.setChecked(False)
            if self.tpParamapButton.isChecked():
                self.tpParamapButton.setChecked(False)

            arr = np.linspace(0, 100, 1000).reshape((1000, 1))
            self.legendDisplay.ax.clear()
            new_cmap1 = self.legendDisplay.truncate_colormap(plt.get_cmap("magma"))
            self.legendDisplay.ax.imshow(
                arr, aspect="auto", cmap=new_cmap1, origin="lower"
            )
            self.legendDisplay.ax.tick_params(axis="y", labelsize=7, pad=0.5)
            self.legendDisplay.ax.set_xticks([])
            self.legendDisplay.ax.set_yticks([0, 250, 500, 750, 1000])
            self.legendDisplay.ax.set_yticklabels(
                [
                    np.round(self.minPe, decimals=2),
                    np.round(self.minPe + ((self.maxPe - self.minPe) / 4), decimals=2),
                    np.round(self.minPe + ((self.maxPe - self.minPe) / 4), decimals=2),
                    np.round(
                        self.minPe + (3 * (self.maxPe - self.minPe) / 4), decimals=2
                    ),
                    np.round(self.maxPe, decimals=2),
                ]
            )
            self.legendDisplay.figure.subplots_adjust(
                left=0.4, right=0.95, bottom=0.05, top=0.96
            )
            self.legendDisplay.canvas.draw()
            self.legendDisplay.legendFrame.setHidden(False)

            self.cmap = plt.get_cmap("magma").colors

            for point in self.pointsPlotted:
                if self.maxPe == self.minPe:
                    color = self.cmap[125]
                else:
                    peVal = self.masterParamap[point[0], point[1], point[2], 1]
                    if not self.masterParamap[point[0], point[1], point[2], 3]:
                        color = [0, 0, 0]  # window not able to be fit
                    elif self.maxPe == self.minPe:
                        color = self.cmap[125]
                    else:
                        color = self.cmap[
                            int(
                                (255 / (self.maxPe - self.minPe)) * (peVal - self.minPe)
                            )
                        ]
                self.paramap[point[0], point[1], point[2]] = [
                    int(color[2] * 255),
                    int(color[1] * 255),
                    int(color[0] * 255),
                    int(self.curAlpha),
                ]

            self.updateCrosshairs()

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self.axialPlane.setAlignment(Qt.AlignCenter)
        self.sagPlane.setAlignment(Qt.AlignCenter)
        self.corPlane.setAlignment(Qt.AlignCenter)
        self.updateCrosshairs()

    def displayTp(self):
        if not self.tpParamapButton.isChecked():
            self.clearParamap()
        else:
            if self.aucParamapButton.isChecked():
                self.aucParamapButton.setChecked(False)
            if self.mttParamapButton.isChecked():
                self.mttParamapButton.setChecked(False)
            if self.peParamapButton.isChecked():
                self.peParamapButton.setChecked(False)

            self.cmap = plt.get_cmap("plasma").colors

            arr = np.linspace(0, 100, 1000).reshape((1000, 1))
            self.legendDisplay.ax.clear()
            new_cmap1 = self.legendDisplay.truncate_colormap(plt.get_cmap("plasma"))
            self.legendDisplay.ax.imshow(
                arr, aspect="auto", cmap=new_cmap1, origin="lower"
            )
            self.legendDisplay.ax.tick_params(axis="y", labelsize=7, pad=0.5)
            self.legendDisplay.ax.set_xticks([])
            self.legendDisplay.ax.set_yticks([0, 250, 500, 750, 1000])
            self.legendDisplay.ax.set_yticklabels(
                [
                    np.round(self.minTp, decimals=1),
                    np.round(self.minTp + ((self.maxTp - self.minTp) / 4), decimals=1),
                    np.round(self.minTp + ((self.maxTp - self.minTp) / 4), decimals=1),
                    np.round(
                        self.minTp + (3 * (self.maxTp - self.minTp) / 4), decimals=1
                    ),
                    np.round(self.maxTp, decimals=1),
                ]
            )
            self.legendDisplay.figure.subplots_adjust(
                left=0.4, right=0.95, bottom=0.05, top=0.96
            )
            self.legendDisplay.canvas.draw()
            self.legendDisplay.legendFrame.setHidden(False)

            for point in self.pointsPlotted:
                if self.maxTp == self.minTp:
                    color = self.cmap[125]
                else:
                    tpVal = self.masterParamap[point[0], point[1], point[2], 2]
                    if not self.masterParamap[point[0], point[1], point[2], 3]:
                        color = [0, 0, 0]  # window not able to be fit
                    elif self.maxTp == self.minTp:
                        color = self.cmap = 125
                    else:
                        color = self.cmap[
                            int(
                                (255 / (self.maxTp - self.minTp)) * (tpVal - self.minTp)
                            )
                        ]
                self.paramap[point[0], point[1], point[2]] = [
                    int(color[2] * 255),
                    int(color[1] * 255),
                    int(color[0] * 255),
                    int(self.curAlpha),
                ]

            self.updateCrosshairs()

    def displayMtt(self):
        if not self.mttParamapButton.isChecked():
            self.clearParamap()
        else:
            if self.aucParamapButton.isChecked():
                self.aucParamapButton.setChecked(False)
            if self.tpParamapButton.isChecked():
                self.tpParamapButton.setChecked(False)
            if self.peParamapButton.isChecked():
                self.peParamapButton.setChecked(False)

            self.cmap = plt.get_cmap("cividis").colors

            arr = np.linspace(0, 100, 1000).reshape((1000, 1))
            self.legendDisplay.ax.clear()
            new_cmap1 = self.legendDisplay.truncate_colormap(plt.get_cmap("cividis"))
            self.legendDisplay.ax.imshow(
                arr, aspect="auto", cmap=new_cmap1, origin="lower"
            )
            self.legendDisplay.ax.tick_params(axis="y", labelsize=7, pad=0.5)
            self.legendDisplay.ax.set_xticks([])
            self.legendDisplay.ax.set_yticks([0, 250, 500, 750, 1000])
            self.legendDisplay.ax.set_yticklabels(
                [
                    np.round(self.minMtt, decimals=1),
                    np.round(
                        self.minMtt + ((self.maxMtt - self.minMtt) / 4), decimals=1
                    ),
                    np.round(
                        self.minMtt + ((self.maxMtt - self.minMtt) / 4), decimals=1
                    ),
                    np.round(
                        self.minMtt + (3 * (self.maxMtt - self.minMtt) / 4), decimals=1
                    ),
                    np.round(self.maxMtt, decimals=1),
                ]
            )
            self.legendDisplay.figure.subplots_adjust(
                left=0.4, right=0.95, bottom=0.05, top=0.96
            )
            self.legendDisplay.canvas.draw()
            self.legendDisplay.legendFrame.setHidden(False)

            for point in self.pointsPlotted:
                if self.maxMtt == self.minMtt:
                    color = self.cmap[125]
                else:
                    mttVal = self.masterParamap[point[0], point[1], point[2], 2]
                    if not self.masterParamap[point[0], point[1], point[2], 3]:
                        color = [0, 0, 0]  # window not able to be fit
                    elif self.maxMtt == self.minMtt:
                        color = self.cmap[125]
                    else:
                        color = self.cmap[
                            int(
                                (255 / (self.maxMtt - self.minMtt))
                                * (mttVal - self.minMtt)
                            )
                        ]
                self.paramap[point[0], point[1], point[2]] = [
                    int(color[2] * 255),
                    int(color[1] * 255),
                    int(color[0] * 255),
                    int(self.curAlpha),
                ]

            self.updateCrosshairs()

    def loadParamaps(self):
        fileName, _ = QFileDialog.getOpenFileName(
            None, "Open File", filter="*.nii.gz *.nii"
        )
        if fileName != "":
            nibIm = nib.load(fileName)
            self.masterParamap = nibIm.get_fdata().astype(np.double)
        else:
            return
        self.paramap = np.zeros(
            (
                self.data4dImg.shape[0],
                self.data4dImg.shape[1],
                self.data4dImg.shape[2],
                4,
            )
        )

        self.maxAuc = 0
        self.minAuc = 99999999
        self.maxPe = 0
        self.minPe = 99999999
        self.maxTp = 0
        self.minTp = 99999999
        self.maxMtt = 0
        self.minMtt = 99999999
        for i in range(len(self.pointsPlotted)):
            if (
                self.masterParamap[
                    self.pointsPlotted[i][0],
                    self.pointsPlotted[i][1],
                    self.pointsPlotted[i][2],
                ][3]
                != 0
            ):
                if (
                    self.masterParamap[
                        self.pointsPlotted[i][0],
                        self.pointsPlotted[i][1],
                        self.pointsPlotted[i][2],
                    ][0]
                    > self.maxAuc
                ):
                    self.maxAuc = self.masterParamap[
                        self.pointsPlotted[i][0],
                        self.pointsPlotted[i][1],
                        self.pointsPlotted[i][2],
                    ][0]
                if (
                    self.masterParamap[
                        self.pointsPlotted[i][0],
                        self.pointsPlotted[i][1],
                        self.pointsPlotted[i][2],
                    ][0]
                    < self.minAuc
                ):
                    self.minAuc = self.masterParamap[
                        self.pointsPlotted[i][0],
                        self.pointsPlotted[i][1],
                        self.pointsPlotted[i][2],
                    ][0]
                if (
                    self.masterParamap[
                        self.pointsPlotted[i][0],
                        self.pointsPlotted[i][1],
                        self.pointsPlotted[i][2],
                    ][1]
                    > self.maxPe
                ):
                    self.maxPe = self.masterParamap[
                        self.pointsPlotted[i][0],
                        self.pointsPlotted[i][1],
                        self.pointsPlotted[i][2],
                    ][1]
                if (
                    self.masterParamap[
                        self.pointsPlotted[i][0],
                        self.pointsPlotted[i][1],
                        self.pointsPlotted[i][2],
                    ][1]
                    < self.minPe
                ):
                    self.minPe = self.masterParamap[
                        self.pointsPlotted[i][0],
                        self.pointsPlotted[i][1],
                        self.pointsPlotted[i][2],
                    ][1]
                if (
                    self.masterParamap[
                        self.pointsPlotted[i][0],
                        self.pointsPlotted[i][1],
                        self.pointsPlotted[i][2],
                    ][2]
                    > self.maxTp
                ):
                    self.maxTp = self.masterParamap[
                        self.pointsPlotted[i][0],
                        self.pointsPlotted[i][1],
                        self.pointsPlotted[i][2],
                    ][2]
                if (
                    self.masterParamap[
                        self.pointsPlotted[i][0],
                        self.pointsPlotted[i][1],
                        self.pointsPlotted[i][2],
                    ][2]
                    < self.minTp
                ):
                    self.minTp = self.masterParamap[
                        self.pointsPlotted[i][0],
                        self.pointsPlotted[i][1],
                        self.pointsPlotted[i][2],
                    ][2]
                if (
                    self.masterParamap[
                        self.pointsPlotted[i][0],
                        self.pointsPlotted[i][1],
                        self.pointsPlotted[i][2],
                    ][3]
                    > self.maxMtt
                ):
                    self.maxMtt = self.masterParamap[
                        self.pointsPlotted[i][0],
                        self.pointsPlotted[i][1],
                        self.pointsPlotted[i][2],
                    ][3]
                if (
                    self.masterParamap[
                        self.pointsPlotted[i][0],
                        self.pointsPlotted[i][1],
                        self.pointsPlotted[i][2],
                    ][3]
                    < self.minMtt
                ):
                    self.minMtt = self.masterParamap[
                        self.pointsPlotted[i][0],
                        self.pointsPlotted[i][1],
                        self.pointsPlotted[i][2],
                    ][3]

        self.hideResultsViewLayout(); self.showParamapDisplayLayout()

    def backFromTic(self):
        self.hideTicDisplayLayout(); self.showResultsViewLayout()

    def showTic(self):
        self.hideResultsViewLayout(); self.showTicDisplayLayout()

    def mousePressEvent(self, event):
        if self.navigatingLabel.isHidden():
            self.navigatingLabel.show(); self.observingLabel.hide()
            if not self.showHideCrossButton.isChecked():
                self.axialPlane.setCursor(QCursor(Qt.BlankCursor))
                self.sagPlane.setCursor(QCursor(Qt.BlankCursor))
                self.corPlane.setCursor(QCursor(Qt.BlankCursor))
        else:
            self.navigatingLabel.hide(); self.observingLabel.show()
            self.axialPlane.setCursor(QCursor(Qt.ArrowCursor))
            self.sagPlane.setCursor(QCursor(Qt.ArrowCursor))
            self.corPlane.setCursor(QCursor(Qt.ArrowCursor))

    def updateCrosshairs(self):
        self.changeAxialSlices(); self.changeSagSlices(); self.changeCorSlices()
        xCoordAx = int((self.newXVal/self.x) * self.axialPlane.pixmap().width())
        yCoordAx = int((self.newYVal/self.y) * self.axialPlane.pixmap().height())
        xCoordSag = int((self.newZVal/self.z) * self.sagPlane.pixmap().width())
        yCoordSag = int((self.newYVal/self.y) * self.sagPlane.pixmap().height())
        xCoordCor = int((self.newXVal/self.x) * self.corPlane.pixmap().width())
        yCoordCor = int((self.newZVal/self.z) * self.corPlane.pixmap().height())

        if not self.showHideCrossButton.isChecked():
            pixmaps = [self.axialPlane.pixmap(), self.sagPlane.pixmap(), self.corPlane.pixmap()]
            points = [(xCoordAx, yCoordAx), (xCoordSag, yCoordSag), (xCoordCor, yCoordCor)]
            for i, pixmap in enumerate(pixmaps):
                painter = QPainter(pixmap); painter.setPen(Qt.yellow)
                coord = points[i]
                vertLine = QLine(coord[0], 0, coord[0], pixmap.height())
                latLine = QLine(0, coord[1], pixmap.width(), coord[1])
                painter.drawLines([vertLine, latLine])
                painter.end()

    def moveToExport(self):
        del self.exportDataGUI
        self.exportDataGUI = ExportDataGUI()
        dataFrame = pd.DataFrame(
            columns=[
                "Patient",
                "Area Under Curve (AUC)",
                "Peak Enhancement (PE)",
                "Time to Peak (TP)",
                "Mean Transit Time (MTT)",
                "TMPPV",
                "VOI Volume (mm^3)",
            ]
        )
        curData = {
                "Patient": self.imagePathInput.text().split("_")[0],
                "Area Under Curve (AUC)": self.auc,
                "Peak Enhancement (PE)": self.pe,
                "Time to Peak (TP)": self.tp,
                "Mean Transit Time (MTT)": self.mtt,
                "TMPPV": self.normFact,
                "VOI Volume (mm^3)": self.voxelScale,
            }
        self.exportDataGUI.dataFrame = dataFrame.append(curData, ignore_index=True)
        self.exportDataGUI.lastGui = self
        self.exportDataGUI.setFilenameDisplays(self.imagePathInput.text())
        self.exportDataGUI.show()
        self.hide()

    def backToLastScreen(self):
        self.lastGui.show()
        self.hide()

    def acceptTICt0(self):
        self.acceptTIC(1)

    def acceptTIC(self, autoT0=0):
        self.imagePathInput.setText(self.lastGui.imagePathInput.text())
        self.newData = None
        self.pointsPlotted = self.lastGui.pointsPlotted
        self.ceus4dImg = self.lastGui.ceus4dImg
        self.bmode4dImg = self.lastGui.bmode4dImg
        self.curSliceIndex = self.lastGui.curSliceIndex
        self.newXVal = self.lastGui.newXVal
        self.newYVal = self.lastGui.newYVal
        self.newZVal = self.lastGui.newZVal
        self.x = self.lastGui.x
        self.y = self.lastGui.y
        self.z = self.lastGui.z
        self.maskCoverImg = self.lastGui.maskCoverImg
        self.sliceArray = self.lastGui.sliceArray
        self.voxelScale = self.lastGui.voxelScale
        self.curSliceTotal.setText(str(self.sliceArray[-1]))
        self.data4dImg = self.lastGui.data4dImg
        
        if self.bmode4dImg is None:
            self.toggleButton.hide()
        elif self.lastGui.toggleButton.isChecked():
            self.toggleButton.setChecked(True)

        self.axialTotalFrames.setText(str(self.z + 1))
        self.sagittalTotalFrames.setText(str(self.x + 1))
        self.coronalTotalFrames.setText(str(self.y + 1))

        self.ax.clear()
        self.ax.plot(self.lastGui.ticX[:, 0], self.lastGui.ticY)

        # self.sliceArray = self.ticEditor.ticX[:,1]
        # if self.curSliceIndex>= len(self.sliceArray):
        #     self.curSliceSlider.setValue(len(self.sliceArray)-1)
        #     self.curSliceSliderValueChanged()
        # self.curSliceSlider.setMaximum(len(self.sliceArray)-1)
        # self.curSliceSpinBox.setMaximum(len(self.sliceArray)-1)

        normFact = np.max(self.lastGui.ticY)
        self.lastGui.ticY = self.lastGui.ticY / normFact
        x = self.lastGui.ticX[:, 0] - np.min(self.lastGui.ticX[:, 0])

        # Bunch of checks
        if np.isnan(np.sum(self.lastGui.ticY)):
            print("STOPPED:NaNs in the VOI")
            return
        if np.isinf(np.sum(self.lastGui.ticY)):
            print("STOPPED:InFs in the VOI")
            return

        # Do the fitting
        try:
            params, _, wholecurve = lf.data_fit(
                [x, self.lastGui.ticY], normFact, autoT0
            )
            self.ax.plot(self.lastGui.ticX[:, 0], wholecurve)
            range = max(self.lastGui.ticX[:, 0]) - min(self.lastGui.ticX[:, 0])
            self.ax.set_xlim(
                xmin=min(self.lastGui.ticX[:, 0]) - (0.05 * range),
                xmax=max(self.lastGui.ticX[:, 0]) + (0.05 * range),
            )
        except RuntimeError:
            print("RunTimeError in Lognormal Fitting")
            params = np.array(
                [
                    np.max(self.lastGui.ticY) * normFact,
                    np.trapz(self.lastGui.ticY * normFact, x=self.lastGui.ticX[:, 0]),
                    self.lastGui.ticX[-1, 0],
                    np.argmax(self.lastGui.ticY),
                    np.max(self.lastGui.ticX[:, 0]) * 2,
                    0,
                ]
            )
        self.fig.subplots_adjust(left=0.1, right=0.97, top=0.85, bottom=0.25)
        self.canvas.draw()
        self.lastGui.ticY *= normFact

        self.aucVal.setText(str(np.around(params[1], decimals=3)))
        self.peVal.setText(str(np.around(params[0], decimals=3)))
        self.tpVal.setText(str(np.around(params[2], decimals=2)))
        self.mttVal.setText(str(np.around(params[3], decimals=2)))
        self.tmppvVal.setText(str(np.around(normFact, decimals=1)))
        if params[4] != 0:
            self.t0Val.setText(str(np.around(params[4], decimals=2)))
        else:
            self.t0Val.setText(str(np.around(self.lastGui.ticX[0, 0], decimals=2)))
        self.voiVolumeVal.setText(str(np.around(self.voxelScale, decimals=1)))
        self.auc = params[1]
        self.pe = params[0]
        self.tp = params[2]
        self.mtt = params[3]
        self.normFact = normFact

        self.lastGui.hide()
        self.curSliceSlider.setValue(self.lastGui.curSliceIndex)
        self.curSliceSlider.setMinimum(0)
        self.curSliceSlider.setMaximum(len(self.sliceArray) - 1)
        self.curSliceSpinBox.setMinimum(0)
        self.curSliceSpinBox.setMaximum(self.sliceArray[-1])
        self.curSliceSliderValueChanged()
        self.alphaValueChanged()
        self.show()
        self.resize(self.lastGui.size())

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
        self.updateCrosshairs()

    def curSliceSpinBoxValueChanged(self):
        if not self.sliceSliderChanged:
            self.sliceSpinBoxChanged = True
            self.sliceValueChanged()

    def curSliceSliderValueChanged(self):
        if not self.sliceSpinBoxChanged:
            self.sliceSliderChanged = True
            self.sliceValueChanged()

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
        self.updateCrosshairs()

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

    def changeAxialSlices(self):
        self.axialFrameNum.setText(str(self.newZVal + 1))

        data2dAx = self.data4dImg[:, :, self.newZVal, self.curSliceIndex]
        data2dAx = np.rot90(np.flipud(data2dAx), 3)
        data2dAx = np.require(data2dAx, np.uint8, "C")
        heightAx, widthAx = data2dAx.shape  # getting height and width for each plane
        bytesLineAx, _ = data2dAx.strides

        qImgAx = QImage(data2dAx, widthAx, heightAx, bytesLineAx, QImage.Format_Grayscale8)
        qImgAx = qImgAx.convertToFormat(QImage.Format_ARGB32)
        self.imAxPIL = qImToPIL(qImgAx)

        if self.masterParamap is not None and self.cmap is not None:
            paramapAx = self.paramap[:, :, self.newZVal, :]
            paramapAx = np.rot90(np.flipud(paramapAx), 3)
            paramapAx = np.require(paramapAx, np.uint8, "C")

            bytesLineAxParamap, _ = paramapAx[:, :, 0].strides
            paramapAxIm = QImage(paramapAx, paramapAx.shape[1], paramapAx.shape[0], bytesLineAxParamap, QImage.Format_ARGB32)

            pmapAxPIL = qImToPIL(paramapAxIm)
            self.imAxPIL.paste(pmapAxPIL, mask=pmapAxPIL)
        else:
            tempAx = self.maskCoverImg[:, :, self.newZVal, :]  # 2D data for axial
            tempAx = np.rot90(np.flipud(tempAx), 3)
            tempAx = np.require(tempAx, np.uint8, "C")
            maskAxH, maskAxW = tempAx[:, :, 0].shape
            maskBytesLineAx, _ = tempAx[:, :, 0].strides

            curMaskAxIm = QImage(tempAx, maskAxW, maskAxH, maskBytesLineAx, QImage.Format_ARGB32)

            maskAx = qImToPIL(curMaskAxIm)
            self.imAxPIL.paste(maskAx, mask=maskAx)

        self.pixmapAx = QPixmap.fromImage(ImageQt(self.imAxPIL))
        self.axialPlane.setPixmap(self.pixmapAx.scaled(
            self.axialPlane.width(), self.axialPlane.height(), Qt.KeepAspectRatio))

    def changeSagSlices(self):
        self.sagittalFrameNum.setText(str(self.newXVal + 1))

        data2dSag = self.data4dImg[self.newXVal, :, :, self.curSliceIndex]
        data2dSag = np.require(data2dSag, np.uint8, "C")
        heightSag, widthSag = data2dSag.shape  # getting height and width for each plane
        bytesLineSag, _ = data2dSag.strides

        qImgSag = QImage(data2dSag, widthSag, heightSag, bytesLineSag, QImage.Format_Grayscale8)
        qImgSag = qImgSag.convertToFormat(QImage.Format_ARGB32)
        self.imSagPIL = qImToPIL(qImgSag)

        if self.masterParamap is not None and self.cmap is not None:
            paramapSag = self.paramap[self.newXVal, :, :, :]
            paramapSag = np.require(paramapSag, np.uint8, "C")

            bytesLineSagParamap, _ = paramapSag[:, :, 0].strides
            paramapSagIm = QImage(paramapSag, paramapSag.shape[1], paramapSag.shape[0], bytesLineSagParamap, QImage.Format_ARGB32)

            pmapSagPIL = qImToPIL(paramapSagIm)
            self.imSagPIL.paste(pmapSagPIL, mask=pmapSagPIL)
        else:
            tempSag = self.maskCoverImg[self.newXVal, :, :, :]
            tempSag = np.require(tempSag, np.uint8, "C")
            maskSagH, maskSagW = tempSag[:, :, 0].shape
            maskBytesLineSag, _ = tempSag[:, :, 0].strides

            curMaskSagIm = QImage(tempSag, maskSagW, maskSagH, maskBytesLineSag, QImage.Format_ARGB32)

            maskSag = qImToPIL(curMaskSagIm)
            self.imSagPIL.paste(maskSag, mask=maskSag)

        self.pixmapSag = QPixmap.fromImage(ImageQt(self.imSagPIL))
        self.sagPlane.setPixmap(self.pixmapSag.scaled(
            self.sagPlane.width(), self.sagPlane.height(), Qt.KeepAspectRatio))

    def changeCorSlices(self):
        self.coronalFrameNum.setText(str(self.newYVal + 1))

        data2dCor = self.data4dImg[:, self.newYVal, :, self.curSliceIndex]
        data2dCor = np.fliplr(np.rot90(data2dCor, 3))
        data2dCor = np.require(data2dCor, np.uint8, "C")
        heightCor, widthCor = data2dCor.shape  # getting height and width for each plane
        bytesLineCor, _ = data2dCor.strides

        qImgCor = QImage(data2dCor, widthCor, heightCor, bytesLineCor, QImage.Format_Grayscale8)
        qImgCor = qImgCor.convertToFormat(QImage.Format_ARGB32)
        self.imCorPIL = qImToPIL(qImgCor)

        if self.masterParamap is not None and self.cmap is not None:
            paramapCor = self.paramap[:, self.newYVal, :, :]
            paramapCor = np.fliplr(np.rot90(tempCor, 3))
            paramapCor = np.require(paramapCor, np.uint8, "C")

            bytesLineCorParamap, _ = paramapCor[:, :, 0].strides
            paramapCorIm = QImage(paramapCor, paramapCor.shape[1], paramapCor.shape[0], bytesLineCorParamap, QImage.Format_ARGB32)

            pmapCorPIL = qImToPIL(paramapCorIm)
            self.imCorPIL.paste(pmapCorPIL, mask=pmapCorPIL)
        else:
            tempCor = self.maskCoverImg[:, self.newYVal, :, :] 
            tempCor = np.fliplr(np.rot90(tempCor, 3))
            tempCor = np.require(tempCor, np.uint8, "C")
            maskCorH, maskCorW = tempCor[:, :, 0].shape
            maskBytesLineCor, _ = tempCor[:, :, 0].strides

            curMaskCorIm = QImage(tempCor, maskCorW, maskCorH, maskBytesLineCor, QImage.Format_ARGB32)

            maskCor = qImToPIL(curMaskCorIm)
            self.imCorPIL.paste(maskCor, mask=maskCor)

        self.pixmapCor = QPixmap.fromImage(ImageQt(self.imCorPIL))
        self.corPlane.setPixmap(self.pixmapCor.scaled(
            self.corPlane.width(), self.corPlane.height(), Qt.KeepAspectRatio))

