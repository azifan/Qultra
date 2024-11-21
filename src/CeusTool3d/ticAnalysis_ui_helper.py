import platform

import numpy as np
import matplotlib.pyplot as plt
from PIL.ImageQt import ImageQt
from matplotlib.widgets import RectangleSelector
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtWidgets import QWidget, QApplication, QHBoxLayout
from PyQt6.QtGui import QPixmap, QPainter, QImage, QCursor, QResizeEvent
from PyQt6.QtCore import QLine, Qt, QPoint, pyqtSlot

from src.CeusTool3d.ticAnalysis_ui import Ui_ticEditor
from src.CeusTool3d.ceusAnalysis_ui_helper import CeusAnalysisGUI
from src.Utils.qtSupport import MouseTracker, qImToPIL

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

        self.setLayout(self.fullScreenLayout)

        self.deSelectLastPointButton.hide(); self.removeSelectedPointsButton.hide()
        self.restoreLastPointsButton.hide(); self.acceptTicButton.hide()
        self.navigatingLabel.hide(); self.acceptT0Button.hide(); self.t0Slider.hide()
        self.acceptT0Button.hide(); self.t0Slider.hide(); self.toggleButton.hide()
        self.toggleButton.setCheckable(True)
        self.t0Slider.setValue(0)

        self.data4dImg = None; self.interpolatedPoints = None; self.curSliceIndex = None
        self.newXVal = None; self.newYVal = None; self.newZVal = None
        self.maskCoverImg = None; self.sliceArray = None; self.voxelScale = None
        self.x = None; self.y = None; self.z = None
        self.bmode4dImg = None; self.ceus4dImg = None
        self.lastGui = None; self.prevLine = None; self.timeLine = None
        self.selectedPoints = []; self.frontPointsX = []; self.frontPointsY = []
        self.removedPointsX = []; self.removedPointsY = []
        self.t0Index = -2
        self.ceusAnalysisGui = CeusAnalysisGUI()
        self.ceusAnalysisGui.lastGui = self

        self.fig = plt.figure()
        self.canvas = FigureCanvas(self.fig)
        self.horizLayout = QHBoxLayout(self.ticFrame)
        self.horizLayout.addWidget(self.canvas)
        self.canvas.draw()
        self.ax = self.fig.add_subplot(111)

        self.selectT0Button.clicked.connect(self.initT0)
        self.automaticallySelectT0Button.clicked.connect(self.deferAutomaticT0)
        self.backButton.clicked.connect(self.backToLastScreen)
        self.acceptT0Button.clicked.connect(self.acceptT0)
        self.toggleButton.clicked.connect(self.toggleIms)

        trackerAx = MouseTracker(self.axialPlane)
        trackerAx.positionChanged.connect(self.axCoordChanged)
        trackerAx.positionClicked.connect(self.planeClicked)
        trackerSag = MouseTracker(self.sagPlane)
        trackerSag.positionChanged.connect(self.sagCoordChanged)
        trackerSag.positionClicked.connect(self.planeClicked)
        trackerCor = MouseTracker(self.corPlane)
        trackerCor.positionChanged.connect(self.corCoordChanged)
        trackerCor.positionClicked.connect(self.planeClicked)

    def toggleIms(self):
        if self.toggleButton.isChecked():
            self.data4dImg = self.bmode4dImg
        else:
            self.data4dImg = self.ceus4dImg
        self.updateCrosshairs()

    @pyqtSlot(QPoint)
    def planeClicked(self, pos):
        if self.navigatingLabel.isHidden():
            self.navigatingLabel.show(); self.observingLabel.hide()
            self.axialPlane.setCursor(QCursor(Qt.CursorShape.BlankCursor))
            self.sagPlane.setCursor(QCursor(Qt.CursorShape.BlankCursor))
            self.corPlane.setCursor(QCursor(Qt.CursorShape.BlankCursor))
        else:
            self.navigatingLabel.hide(); self.observingLabel.show()
            self.axialPlane.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            self.sagPlane.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            self.corPlane.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        

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

    def backToLastScreen(self):
        self.lastGui.show()
        self.lastGui.resize(self.size())
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
        self.updateCrosshairs()

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
            self.canvas.draw()
            self.updateCrosshairs()

    def changeAxialSlices(self):
        data2dAx = self.data4dImg[:, :, self.newZVal, self.curSliceIndex]
        data2dAx = np.rot90(np.flipud(data2dAx), 3)  # rotate
        data2dAx = np.require(data2dAx, np.uint8, "C")
        heightAx, widthAx = data2dAx.shape
        bytesLineAx, _ = data2dAx.strides
        
        qImgAx = QImage(data2dAx, widthAx, heightAx, bytesLineAx, QImage.Format.Format_Grayscale8)
        qImgAx = qImgAx.convertToFormat(QImage.Format.Format_ARGB32)

        tempAx = self.maskCoverImg[:, :, self.newZVal, :]  # 2D data for axial
        tempAx = np.rot90(np.flipud(tempAx), 3)  # rotate ccw 270
        tempAx = np.require(tempAx, np.uint8, "C")
        maskAxH, maskAxW = tempAx[:, :, 0].shape
        maskBytesLineAx, _ = tempAx[:, :, 0].strides

        curMaskAxIm = QImage(tempAx, maskAxW, maskAxH, maskBytesLineAx, QImage.Format.Format_ARGB32)

        imAxPIL = qImToPIL(qImgAx); maskAx = qImToPIL(curMaskAxIm)
        imAxPIL.paste(maskAx, mask=maskAx)
        pixmapAx = QPixmap.fromImage(ImageQt(imAxPIL))
        self.axialPlane.setPixmap(pixmapAx.scaled(
            self.axialPlane.width(), self.axialPlane.height(), Qt.AspectRatioMode.KeepAspectRatio))

    def changeSagSlices(self):
        data2dSag = self.data4dImg[self.newXVal, :, :, self.curSliceIndex]
        data2dSag = np.require(data2dSag, np.uint8, "C")
        heightSag, widthSag = data2dSag.shape
        bytesLineSag, _ = data2dSag.strides

        qImgSag = QImage(data2dSag, widthSag, heightSag, bytesLineSag, QImage.Format.Format_Grayscale8)
        qImgSag = qImgSag.convertToFormat(QImage.Format.Format_ARGB32)

        tempSag = self.maskCoverImg[self.newXVal, :, :, :]
        tempSag = np.require(tempSag, np.uint8, "C")
        maskSagH, maskSagW = tempSag[:, :, 0].shape
        maskBytesLineSag, _ = tempSag[:, :, 0].strides

        curMaskSagIm = QImage(tempSag, maskSagW, maskSagH, maskBytesLineSag, QImage.Format.Format_ARGB32)

        imSagPIL = qImToPIL(qImgSag); maskSag = qImToPIL(curMaskSagIm)
        imSagPIL.paste(maskSag, mask=maskSag)
        pixmapSag = QPixmap.fromImage(ImageQt(imSagPIL))
        self.sagPlane.setPixmap(pixmapSag.scaled(
            self.sagPlane.width(), self.sagPlane.height(), Qt.AspectRatioMode.KeepAspectRatio))

    def changeCorSlices(self):
        data2dCor = self.data4dImg[:, self.newYVal, :, self.curSliceIndex]
        data2dCor = np.fliplr(np.rot90(data2dCor, 3))
        data2dCor = np.require(data2dCor, np.uint8, "C")
        heightCor, widthCor = data2dCor.shape
        bytesLineCor, _ = data2dCor.strides

        qImgCor = QImage(data2dCor, widthCor, heightCor, bytesLineCor, QImage.Format.Format_Grayscale8)
        qImgCor = qImgCor.convertToFormat(QImage.Format.Format_ARGB32)

        tempCor = self.maskCoverImg[:, self.newYVal, :, :]
        tempCor = np.fliplr(np.rot90(tempCor, 3))
        tempCor = np.require(tempCor, np.uint8, "C")
        maskCorH, maskCorW = tempCor[:, :, 0].shape
        maskBytesLineCor, _ = tempCor[:, :, 0].strides

        curMaskCorIm = QImage(tempCor, maskCorW,maskCorH, maskBytesLineCor, QImage.Format.Format_ARGB32)

        imCorPIL = qImToPIL(qImgCor); maskCor = qImToPIL(curMaskCorIm)
        imCorPIL.paste(maskCor, mask=maskCor)
        pixmapCor = QPixmap.fromImage(ImageQt(imCorPIL))
        self.corPlane.setPixmap(pixmapCor.scaled(
            self.corPlane.width(), self.corPlane.height(), Qt.AspectRatioMode.KeepAspectRatio))
        
    def updateCrosshairs(self):
        self.changeAxialSlices(); self.changeSagSlices(); self.changeCorSlices()
        xCoordAx = int((self.newXVal/self.x) * self.axialPlane.pixmap().width())
        yCoordAx = int((self.newYVal/self.y) * self.axialPlane.pixmap().height())
        xCoordSag = int((self.newZVal/self.z) * self.sagPlane.pixmap().width())
        yCoordSag = int((self.newYVal/self.y) * self.sagPlane.pixmap().height())
        xCoordCor = int((self.newXVal/self.x) * self.corPlane.pixmap().width())
        yCoordCor = int((self.newZVal/self.z) * self.corPlane.pixmap().height())

        pixmaps = [self.axialPlane.pixmap(), self.sagPlane.pixmap(), self.corPlane.pixmap()]
        points = [(xCoordAx, yCoordAx), (xCoordSag, yCoordSag), (xCoordCor, yCoordCor)]
        for i, pixmap in enumerate(pixmaps):
            painter = QPainter(pixmap); painter.setPen(Qt.GlobalColor.yellow)
            coord = points[i]
            vertLine = QLine(coord[0], 0, coord[0], pixmap.height())
            latLine = QLine(0, coord[1], pixmap.width(), coord[1])
            painter.drawLines([vertLine, latLine])
            painter.end()
            if i == 0:
                self.axialPlane.setPixmap(pixmap)
            elif i == 1:
                self.sagPlane.setPixmap(pixmap)
            else:         
                self.corPlane.setPixmap(pixmap)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self.axialPlane.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sagPlane.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.corPlane.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.updateCrosshairs()


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
