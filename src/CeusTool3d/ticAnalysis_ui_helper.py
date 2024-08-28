import platform

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QWidget, QApplication, QHBoxLayout
from PyQt5.QtGui import QPixmap, QPainter, QImage
from PyQt5.QtCore import QLine, Qt

from src.CeusTool3d.ticAnalysis_ui import Ui_ticEditor
from src.CeusTool3d.ceusAnalysis_ui_helper import CeusAnalysisGUI

system = platform.system()


class TicAnalysisGUI(Ui_ticEditor, QWidget):
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

        self.deSelectLastPointButton.setHidden(True)
        self.removeSelectedPointsButton.setHidden(True)
        self.restoreLastPointsButton.setHidden(True)
        self.acceptTicButton.setHidden(True)
        self.acceptT0Button.setHidden(True)
        self.t0Slider.setHidden(True)

        self.t0Slider.setValue(0)

        self.data4dImg = None
        self.dataFrame = None
        self.curSliceIndex = None
        self.newXVal = None
        self.newYVal = None
        self.newZVal = None
        self.maskCoverImg = None
        self.widthAx = None
        self.heightAx = None
        self.bytesLineAx = None
        self.maskAxW = None
        self.maskAxH = None
        self.maskBytesLineAx = None
        self.widthSag = None
        self.heightSag = None
        self.bytesLineSag = None
        self.maskSagW = None
        self.maskSagH = None
        self.pointsPlotted = None
        self.maskBytesLineSag = None
        self.widthCor = None
        self.heightCor = None
        self.bytesLineCor = None
        self.maskCorW = None
        self.maskCorH = None
        self.maskBytesLineCor = None
        self.sliceArray = None
        self.x = None
        self.y = None
        self.z = None
        self.voxelScale = None
        self.xCur = 0
        self.yCur = 0

        self.axCoverPixmap = QPixmap(231, 211)
        self.axCoverPixmap.fill(Qt.transparent)
        self.axCoverLabel.setPixmap(self.axCoverPixmap)
        self.sagCoverPixmap = QPixmap(231, 211)
        self.sagCoverPixmap.fill(Qt.transparent)
        self.sagCoverLabel.setPixmap(self.sagCoverPixmap)
        self.corCoverPixmap = QPixmap(231, 211)
        self.corCoverPixmap.fill(Qt.transparent)
        self.corCoverLabel.setPixmap(self.corCoverPixmap)

        self.fig = plt.figure()
        self.canvas = FigureCanvas(self.fig)
        self.horizLayout = QHBoxLayout(self.ticFrame)
        self.horizLayout.addWidget(self.canvas)
        self.canvas.draw()
        self.ax = self.fig.add_subplot(111)

        self.selectT0Button.clicked.connect(self.initT0)
        self.automaticallySelectT0Button.clicked.connect(self.deferAutomaticT0)

        self.t0Index = -2
        self.selectedPoints = []
        self.frontPointsX = []
        self.frontPointsY = []
        self.removedPointsX = []
        self.removedPointsY = []
        self.ceusAnalysisGui = CeusAnalysisGUI()
        self.ceusAnalysisGui.lastGui = self
        self.lastGui = None
        self.prevLine = None
        self.timeLine = None
        self.backButton.clicked.connect(self.backToLastScreen)
        self.acceptT0Button.clicked.connect(self.acceptT0)

    def backToLastScreen(self):
        self.lastGui.restartVoiButton.clicked.connect(self.lastGui.restartVoi)
        self.lastGui.dataFrame = self.dataFrame
        self.lastGui.show()
        self.hide()

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
        if not self.t0Slider.isHidden():
            self.curSliceIndex = self.findSliceFromTime(self.t0Slider.value())
        self.changeAxialSlices()
        self.changeSagSlices()
        self.changeCorSlices()

    def initT0(self):
        self.acceptT0Button.setHidden(False)
        self.selectT0Button.setHidden(True)
        self.automaticallySelectT0Button.setHidden(True)
        self.t0Slider.setHidden(False)

        self.t0Slider.setMinimum(int(min(self.ticX[:, 0])))
        self.t0Slider.setMaximum(int(max(self.ticX[:, 0])))
        self.t0Slider.valueChanged.connect(self.t0ScrollValueChanged)
        self.t0Slider.setValue(0)
        if self.prevLine is not None:
            self.prevLine.remove()
            self.t0Index = -2
        self.prevLine = self.ax.axvline(
            x=self.t0Slider.value(), color="green", label="axvline - full height"
        )
        self.canvas.draw()
        try:
            self.acceptTicButton.clicked.disconnect()
        except TypeError:
            pass
        self.acceptTicButton.clicked.connect(self.ceusAnalysisGui.acceptTIC)

    def deferAutomaticT0(self):
        self.automaticallySelectT0Button.setHidden(True)
        self.selectT0Button.setHidden(True)
        self.deSelectLastPointButton.setHidden(False)
        self.deSelectLastPointButton.clicked.connect(self.deselectLast)
        self.removeSelectedPointsButton.setHidden(False)
        self.removeSelectedPointsButton.clicked.connect(self.removeSelectedPoints)
        self.restoreLastPointsButton.setHidden(False)
        self.restoreLastPointsButton.clicked.connect(self.restoreLastPoints)
        self.acceptTicButton.setHidden(False)
        self.t0Index = -1  # enables rectangular selector
        self.ax.clear()
        self.graph(self.ticX, self.ticY)
        try:
            self.acceptTicButton.clicked.disconnect()
        except TypeError:
            pass
        self.acceptTicButton.clicked.connect(self.ceusAnalysisGui.acceptTICt0)

    def graph(self, x, y):
        global ticX, ticY
        # y -= min(y)
        self.ticX = x
        self.ticY = y
        ticX = self.ticX
        ticY = self.ticY
        self.ax.plot(x[:, 0], y, picker=True)
        self.ax.scatter(x[:, 0], y, color="r")
        self.ax.set_xlabel("Time (s)", fontsize=11, labelpad=1)
        self.ax.set_ylabel("Signal Amplitude", fontsize=11, labelpad=1)
        self.ax.set_title("Time Intensity Curve (TIC)", fontsize=14, pad=1.5)
        self.ax.tick_params("both", pad=0.3, labelsize=7.2)
        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)
        plt.xticks(np.arange(0, int(max(self.ticX[:, 0])) + 10, 10))
        range = max(x[:, 0]) - min(x[:, 0])
        self.ax.set_xlim(
            xmin=min(x[:, 0]) - (0.05 * range), xmax=max(x[:, 0]) + (0.05 * range)
        )
        if self.timeLine is not None:
            self.ax.add_line(self.timeLine)
        self.fig.subplots_adjust(left=0.1, right=0.97, top=0.9, bottom=0.1)
        self.fig.canvas.mpl_connect("pick_event", self.selectPoint)

        if self.t0Index > -2:
            self.mask = np.zeros(self.ticX[:, 0].shape, dtype=bool)
            self.selector = RectangleSelector(
                self.ax,
                self.rect_highlight,
                useblit=True,
                props=dict(facecolor="cyan", alpha=0.2),
            )

        self.canvas.draw()

    def t0ScrollValueChanged(self):
        self.prevLine.remove()
        self.prevLine = self.ax.axvline(
            x=self.t0Slider.value(), color="green", label="axvline - full height"
        )
        self.sliceValueChanged()
        self.canvas.draw()

    def removeSelectedPoints(self):
        if len(self.selectedPoints):
            self.selectedPoints.sort()
            j = 0
            curRemovedX = []
            curRemovedY = []
            for i in range(len(self.ticX)):
                if i == self.selectedPoints[j]:
                    curRemovedX.append(self.ticX[i])
                    curRemovedY.append(self.ticY[i])
                    j += 1
                    if j == len(self.selectedPoints):
                        break
            self.ticX = np.delete(self.ticX, self.selectedPoints, axis=0)
            self.ticY = np.delete(self.ticY, self.selectedPoints)
            self.ax.clear()
            self.graph(self.ticX, self.ticY)
            self.removedPointsX.append(curRemovedX)
            self.removedPointsY.append(curRemovedY)
            self.selectedPoints = []

    def acceptT0(self):
        self.t0Slider.setHidden(True)
        self.acceptT0Button.setHidden(True)
        self.deSelectLastPointButton.setHidden(False)
        self.deSelectLastPointButton.clicked.connect(self.deselectLast)
        self.removeSelectedPointsButton.setHidden(False)
        self.removeSelectedPointsButton.clicked.connect(self.removeSelectedPoints)
        self.restoreLastPointsButton.setHidden(False)
        self.restoreLastPointsButton.clicked.connect(self.restoreLastPoints)
        self.acceptTicButton.setHidden(False)

        if self.t0Index == -2:
            for i in range(len(self.ticX[:, 0])):
                if self.ticX[:, 0][i] > self.t0Slider.value():
                    break
            self.t0Index = i

        self.selectedPoints = list(range(self.t0Index))
        if len(self.selectedPoints):
            self.removeSelectedPoints()
            self.frontPointsX = self.removedPointsX[-1]
            self.frontPointsY = self.removedPointsY[-1]
            self.removedPointsX.pop()
            self.removedPointsY.pop()
        # self.ticX[:,0] -= (min(self.ticX[:,0]) - 1)
        self.ax.clear()
        self.graph(self.ticX, self.ticY)

    def rect_highlight(self, event1, event2):
        self.mask |= self.inside(event1, event2)
        x = self.ticX[:, 0][self.mask]
        y = self.ticY[self.mask]
        addedIndices = np.sort(np.array(list(range(len(self.ticY))))[self.mask])
        for index in addedIndices:
            self.selectedPoints.append(index)
        self.ax.scatter(x, y, color="orange")
        self.canvas.draw()

    def inside(self, event1, event2):
        # Returns a boolean mask of the points inside the rectangle defined by
        # event1 and event2
        x0, x1 = sorted([event1.xdata, event2.xdata])
        y0, y1 = sorted([event1.ydata, event2.ydata])
        mask = (
            (self.ticX[:, 0] > x0)
            & (self.ticX[:, 0] < x1)
            & (self.ticY > y0)
            & (self.ticY < y1)
        )
        return mask

    def deselectLast(self):
        if len(self.selectedPoints):
            lastPt = self.selectedPoints[-1]
            self.selectedPoints.pop()
            self.ax.scatter(self.ticX[lastPt][0], self.ticY[lastPt], color="red")
            self.canvas.draw()
            self.mask = np.zeros(self.ticX[:, 0].shape, dtype=bool)

    def restoreLastPoints(self):
        if len(self.removedPointsX) > 0:
            for i in range(len(self.selectedPoints)):
                self.deselectLast()
            self.selectedPoints = []
            j = 0
            i = 0
            max = self.ticX.shape[0] + len(self.removedPointsX[-1])
            while i < self.ticX.shape[0] - 1:
                if (
                    self.ticX[i][0] < self.removedPointsX[-1][j][0]
                    and self.removedPointsX[-1][j][0] < self.ticX[i + 1][0]
                ):
                    self.ticX = np.insert(
                        self.ticX, i + 1, self.removedPointsX[-1][j], axis=0
                    )
                    self.ticY = np.insert(self.ticY, i + 1, self.removedPointsY[-1][j])
                    j += 1
                    if j == len(self.removedPointsX[-1]):
                        break
                i += 1
            if i < max and j < len(self.removedPointsX[-1]):
                while j < len(self.removedPointsX[-1]):
                    self.ticX = np.insert(
                        self.ticX, i + 1, self.removedPointsX[-1][j], axis=0
                    )
                    self.ticY = np.append(self.ticY, self.removedPointsY[-1][j])
                    j += 1
                    i += 1
            self.removedPointsX.pop()
            self.removedPointsY.pop()
            self.ax.clear()
            ticX = self.ticX
            ticY = self.ticY
            self.graph(ticX, ticY)

    def changeAxialSlices(self):
        self.data2dAx = self.data4dImg[
            :, :, self.newZVal, self.curSliceIndex
        ]  # , self.curSlice] #defining 2D data for axial
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
            QPixmap.fromImage(self.curMaskAxIm).scaled(231, 211)
        )  # displaying QPixmap in the QLabels
        self.axialPlane.setPixmap(
            QPixmap.fromImage(self.qImgAx).scaled(231, 211)
        )  # otherwise, would just display the normal unmodified q_img

    def changeSagSlices(self):
        self.data2dSag = self.data4dImg[
            self.newXVal, :, :, self.curSliceIndex
        ]  # , self.curSlice]
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
            QPixmap.fromImage(self.curMaskSagIm).scaled(231, 211)
        )
        self.sagPlane.setPixmap(QPixmap.fromImage(self.qImgSag).scaled(231, 211))

    def changeCorSlices(self):
        self.data2dCor = self.data4dImg[
            :, self.newYVal, :, self.curSliceIndex
        ]  # , self.curSlice]
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
            QPixmap.fromImage(self.curMaskCorIm).scaled(231, 211)
        )
        self.corPlane.setPixmap(QPixmap.fromImage(self.qImgCor).scaled(231, 211))

    def updateCrosshair(self):
        scrolling = "none"
        if self.xCur < 591 and self.xCur > 360 and self.yCur < 331 and self.yCur > 120:
            self.actualX = int((self.xCur - 361) * (self.widthAx - 1) / 231)
            self.actualY = int((self.yCur - 121) * (self.heightAx - 1) / 211)
            scrolling = "ax"
            self.axCoverLabel.pixmap().fill(Qt.transparent)
            painter = QPainter(self.axCoverLabel.pixmap())
            painter.setPen(Qt.yellow)
            axVertLine = QLine(self.xCur - 361, 0, self.xCur - 361, 211)
            axLatLine = QLine(0, self.yCur - 121, 231, self.yCur - 121)
            painter.drawLines([axVertLine, axLatLine])
            painter.end()
            self.update()
        elif (
            self.xCur < 871 and self.xCur > 640 and self.yCur < 331 and self.yCur > 120
        ):
            self.actualX = int((self.xCur - 641) * (self.widthSag - 1) / 231)
            self.actualY = int((self.yCur - 121) * (self.heightSag - 1) / 211)
            scrolling = "sag"
            self.sagCoverLabel.pixmap().fill(Qt.transparent)
            painter = QPainter(self.sagCoverLabel.pixmap())
            painter.setPen(Qt.yellow)
            sagVertLine = QLine(self.xCur - 641, 0, self.xCur - 641, 211)
            sagLatLine = QLine(0, self.yCur - 121, 231, self.yCur - 121)
            painter.drawLines([sagVertLine, sagLatLine])
            painter.end()
            self.update()
        elif (
            self.xCur < 1131 and self.xCur > 920 and self.yCur < 331 and self.yCur > 120
        ):
            self.actualX = int((self.xCur - 921) * (self.widthCor - 1) / 231)
            self.actualY = int((self.yCur - 121) * (self.heightCor - 1) / 211)
            scrolling = "cor"
            self.corCoverLabel.pixmap().fill(Qt.transparent)
            painter = QPainter(self.corCoverLabel.pixmap())
            painter.setPen(Qt.yellow)
            corVertLine = QLine(self.xCur - 921, 0, self.xCur - 921, 211)
            corLatLine = QLine(0, self.yCur - 121, 231, self.yCur - 121)
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
                int(self.newZVal / self.z * 231),
                0,
                int(self.newZVal / self.z * 231),
                211,
            )
            sagLatLine = QLine(
                0,
                int(self.newYVal / self.y * 211),
                231,
                int(self.newYVal / self.y * 211),
            )
            painter.drawLines([sagVertLine, sagLatLine])
            painter.end()

            self.corCoverLabel.pixmap().fill(Qt.transparent)
            painter = QPainter(self.corCoverLabel.pixmap())
            painter.setPen(Qt.yellow)
            corVertLine = QLine(
                int(self.newXVal / self.x * 231),
                0,
                int(self.newXVal / self.x * 231),
                211,
            )
            corLatLine = QLine(
                0,
                int(self.newZVal / self.z * 211),
                231,
                int(self.newZVal / self.z * 211),
            )
            painter.drawLines([corVertLine, corLatLine])
            painter.end()

        elif scrolling == "sag":
            self.newZVal = self.actualX
            self.newYVal = self.actualY
            self.changeAxialSlices()
            self.changeCorSlices()
            self.axCoverLabel.pixmap().fill(Qt.transparent)
            painter = QPainter(self.axCoverLabel.pixmap())
            painter.setPen(Qt.yellow)
            axVertLine = QLine(
                int(self.newXVal / self.x * 231),
                0,
                int(self.newXVal / self.x * 231),
                211,
            )
            axLatLine = QLine(
                0,
                int(self.newYVal / self.y * 211),
                231,
                int(self.newYVal / self.y * 211),
            )
            painter.drawLines([axVertLine, axLatLine])
            painter.end()

            self.corCoverLabel.pixmap().fill(Qt.transparent)
            painter = QPainter(self.corCoverLabel.pixmap())
            painter.setPen(Qt.yellow)
            corVertLine = QLine(
                int(self.newXVal / self.x * 231),
                0,
                int(self.newXVal / self.x * 231),
                211,
            )
            corLatLine = QLine(
                0,
                int(self.newZVal / self.z * 211),
                231,
                int(self.newZVal / self.z * 211),
            )
            painter.drawLines([corVertLine, corLatLine])
            painter.end()

        elif scrolling == "cor":
            self.newXVal = self.actualX
            self.newZVal = self.actualY
            self.changeAxialSlices()
            self.changeSagSlices()
            self.axCoverLabel.pixmap().fill(Qt.transparent)
            painter = QPainter(self.axCoverLabel.pixmap())
            painter.setPen(Qt.yellow)
            axVertLine = QLine(
                int(self.newXVal / self.x * 231),
                0,
                int(self.newXVal / self.x * 231),
                211,
            )
            axLatLine = QLine(
                0,
                int(self.newYVal / self.y * 211),
                231,
                int(self.newYVal / self.y * 211),
            )
            painter.drawLines([axVertLine, axLatLine])
            painter.end()

            self.sagCoverLabel.pixmap().fill(Qt.transparent)
            painter = QPainter(self.sagCoverLabel.pixmap())
            painter.setPen(Qt.yellow)
            sagVertLine = QLine(
                int(self.newZVal / self.z * 231),
                0,
                int(self.newZVal / self.z * 231),
                211,
            )
            sagLatLine = QLine(
                0,
                int(self.newYVal / self.y * 211),
                231,
                int(self.newYVal / self.y * 211),
            )
            painter.drawLines([sagVertLine, sagLatLine])
            painter.end()
            self.update()

    def mousePressEvent(self, event):
        self.xCur = event.x()
        self.yCur = event.y()
        self.newPointPlotted = False

    def mouseMoveEvent(self, event):
        self.xCur = event.x()
        self.yCur = event.y()
        self.updateCrosshair()

    def selectPoint(self, event):
        if self.t0Slider.isHidden():
            thisline = event.artist
            xdata = thisline.get_xdata()
            ind = event.ind[0]
            if self.timeLine is not None:
                self.timeLine.remove()
            self.timeLine = self.ax.axvline(
                x=xdata[ind],
                color=(0, 0, 1, 0.3),
                label="axvline - full height",
                zorder=1,
            )
            self.curSliceIndex = self.findSliceFromTime(xdata[ind])
            self.changeAxialSlices()
            self.changeSagSlices()
            self.changeCorSlices()
            self.canvas.draw()


if __name__ == "__main__":
    import sys
    from numpy import genfromtxt

    # my_data = genfromtxt('/Users/davidspector/Home/Stanford/USImgAnalysisGui_v2/Data/newest_test_tic.csv', delimiter=',')[1:]
    my_data = genfromtxt(
        "/Users/davidspector/Home/Stanford/USImgAnalysisGui_v2/Data/C3P13_original_tic.csv",
        delimiter=",",
    )[1:]
    # my_data = genfromtxt('/Users/davidspector/Home/Stanford/USImgAnalysisGui_v2/Data/C3P13_original_tic.csv', delimiter=',')

    test_ticX = np.array([[my_data[i, 0], i] for i in range(len(my_data[:, 0]))])
    # test_ticY = my_data[:,1]
    test_ticY = my_data[:, 1] - min(my_data[:, 1])

    normalizer = max(test_ticY)

    print(np.average(my_data[:, 1]))

    app = QApplication(sys.argv)
    ui = TicAnalysisGUI()
    ui.show()
    ui.graph(test_ticX, test_ticY)
    sys.exit(app.exec_())
