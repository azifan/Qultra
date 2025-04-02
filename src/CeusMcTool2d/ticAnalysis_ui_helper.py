import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtWidgets import QWidget, QApplication, QHBoxLayout
from PyQt6.QtGui import QImage, QPixmap

import src.Utils.lognormalFunctions as lf
from src.CeusMcTool2d.ticAnalysis_ui import Ui_ticEditor
from src.CeusMcTool2d.ceusAnalysis_ui_helper import CeusAnalysisGUI


class TicAnalysisGUI(Ui_ticEditor, QWidget):
    def __init__(self):
        # self.selectImage = QWidget()
        super().__init__()
        self.setupUi(self)

        self.deSelectLastPointButton.setHidden(True)
        self.removeSelectedPointsButton.setHidden(True)
        self.restoreLastPointsButton.setHidden(True)
        self.acceptTicButton.setHidden(True)
        self.acceptT0Button.setHidden(True)
        self.t0Slider.setHidden(True)

        self.t0Slider.setValue(0)

        self.mcResultsArray = None
        self.curFrameIndex = None
        self.xCur = None
        self.yCur = None
        self.sliceArray = None
        self.x = None
        self.y = None
        self.ceusAnalysisGui = None
        self.roiArea = None
        self.x0_bmode = None
        self.y0_bmode = None
        self.w_bmode = None
        self.h_bmode = None
        self.x0_CE = None
        self.y0_CE = None
        self.w_CE = None
        self.h_CE = None
        self.ticArray = None
        self.segCoverMask = None
        self.mc = False

        self.axRes, self.latRes, self.cineRate, self.fullPath = None, None, None, None

        self.fig = plt.figure()
        self.canvas = FigureCanvas(self.fig)
        self.horizLayout = QHBoxLayout(self.ticFrame)
        self.horizLayout.addWidget(self.canvas)
        self.canvas.draw()
        self.ax = self.fig.add_subplot(111)

        self.selectT0Button.clicked.connect(self.initT0)
        self.automaticT0Button.clicked.connect(self.deferAutomaticT0)

        self.t0Index = -2
        self.selectedPoints = []
        self.frontPointsX = []
        self.frontPointsY = []
        self.removedPointsX = []
        self.removedPointsY = []
        self.ceusResultsGui = None
        self.lastGui = None
        self.prevLine = None
        self.timeLine = None
        self.backButton.clicked.connect(self.backToLastScreen)
        self.acceptT0Button.clicked.connect(self.acceptT0)

    def backToLastScreen(self):
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
            self.curFrameIndex = self.findSliceFromTime(self.t0Slider.value())
        self.updateIm()
        self.update()

    def updateIm(self):
        self.x = self.mcResultsArray.shape[2]
        self.y = self.mcResultsArray.shape[1]
        self.numSlices = self.mcResultsArray.shape[0]
        self.imX0 = 370
        self.imX1 = 1141
        self.imY0 = 10
        self.imY1 = 351
        xLen = self.imX1 - self.imX0
        yLen = self.imY1 - self.imY0

        quotient = self.x / self.y
        if quotient > (xLen / yLen):
            self.widthScale = xLen
            self.depthScale = int(self.widthScale / quotient)
            emptySpace = yLen - self.depthScale
            yBuffer = int(emptySpace / 2)
            self.imY0 += yBuffer
            self.imY1 -= yBuffer
        else:
            self.widthScale = int(yLen * quotient)
            self.depthScale = yLen
            emptySpace = xLen - self.widthScale
            xBuffer = int(emptySpace / 2)
            self.imX0 += xBuffer
            self.imX1 -= xBuffer
        self.imDisplayLabel.move(self.imX0, self.imY0)
        self.imDisplayLabel.resize(self.widthScale, self.depthScale)
        self.maskDisplayLabel.move(self.imX0, self.imY0)
        self.maskDisplayLabel.resize(self.widthScale, self.depthScale)

        self.mcData = np.require(self.mcResultsArray[self.curFrameIndex], np.uint8, "C")
        self.bytesLineMc, _ = self.mcData[:, :, 0].strides
        self.qImgMc = QImage(
            self.mcData, self.x, self.y, self.bytesLineMc, QImage.Format.Format_RGB888
        )
        self.imDisplayLabel.setPixmap(
            QPixmap.fromImage(self.qImgMc).scaled(self.widthScale, self.depthScale)
        )

        self.maskCoverImg = np.require(
            self.segCoverMask[self.curFrameIndex], np.uint8, "C"
        )
        self.bytesLineMask, _ = self.maskCoverImg[:, :, 0].strides
        self.qImgMask = QImage(
            self.maskCoverImg, self.x, self.y, self.bytesLineMask, QImage.Format.Format_ARGB32
        )
        self.maskDisplayLabel.setPixmap(
            QPixmap.fromImage(self.qImgMask).scaled(self.widthScale, self.depthScale)
        )

    def initT0(self):
        self.acceptT0Button.setHidden(False)
        self.selectT0Button.setHidden(True)
        self.automaticT0Button.setHidden(True)
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

    def deferAutomaticT0(self):
        self.automaticT0Button.setHidden(True)
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
        self.acceptTicButton.clicked.connect(self.acceptTICt0)

    def graph(self, x, y):
        global ticX, ticY
        # y -= min(y)
        # x[:,0] -= np.min(x[:,0])
        # y = y / np.max(y)
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
        plt.xticks(np.arange(int(np.min(x[:, 0])), int(max(self.ticX[:, 0])) + 10, 10))
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
            yRange = max(self.ticY) - min(self.ticY)
            self.ax.set_ylim(
                ymin=min(self.ticY) - (0.05 * yRange),
                ymax=max(self.ticY) + (0.05 * yRange),
            )
            self.removedPointsX.append(curRemovedX)
            self.removedPointsY.append(curRemovedY)
            self.selectedPoints = []

    def setFilenameDisplays(self, imageName):
        self.imagePathInput.setHidden(False)

        imFile = imageName.split("/")[-1]

        self.imagePathInput.setText(imFile)
        self.inputTextPath = imageName

    def acceptTICt0(self):
        self.acceptTIC(1)

    def acceptTIC(self, autoT0=0):
        del self.ceusAnalysisGui
        self.ceusAnalysisGui = CeusAnalysisGUI()
        self.ceusAnalysisGui.show()
        self.ceusAnalysisGui.ax.clear()
        self.ceusAnalysisGui.ax.plot(self.ticX[:, 0], self.ticY)
        self.ceusAnalysisGui.setFilenameDisplays(self.imagePathInput.text())

        tmppv = np.max(self.ticY)
        self.ticY = self.ticY / tmppv
        x = self.ticX[:, 0] - np.min(self.ticX[:, 0])

        # Bunch of checks
        if np.isnan(np.sum(self.ticY)):
            print("STOPPED:NaNs in the VOI")
            return
        if np.isinf(np.sum(self.ticY)):
            print("STOPPED:InFs in the VOI")
            return

        # Do the fitting
        try:
            params, _, wholecurve = lf.data_fit([x, self.ticY], tmppv, autoT0)
            self.ceusAnalysisGui.ax.plot(self.ticX[:, 0], wholecurve)
            range = max(self.ticX[:, 0]) - min(self.ticX[:, 0])
            self.ceusAnalysisGui.ax.set_xlim(
                xmin=min(self.ticX[:, 0]) - (0.05 * range),
                xmax=max(self.ticX[:, 0]) + (0.05 * range),
            )
            self.ceusAnalysisGui.wholecurve = np.array(wholecurve)
        except RuntimeError:
            print("RunTimeError")
            params = np.array(
                [
                    np.max(self.ticY),
                    np.trapz(self.ticY, x=self.ticX[:, 0]),
                    self.ticX[-1, 0],
                    np.argmax(self.ticY),
                    np.max(self.ticX[:, 0]) * 2,
                    0,
                ]
            )
            # params = np.array([np.max(self.ticY)*tmppv, np.trapz(self.ticY*tmppv, x=self.ticX[:,0]), self.ticX[-1,0], np.argmax(self.ticY), np.max(self.ticX[:,0])*2, 0]);
        self.fig.subplots_adjust(left=0.1, right=0.97, top=0.85, bottom=0.25)
        self.canvas.draw()
        self.ticY *= tmppv

        self.ceusAnalysisGui.aucVal.setText(str(np.around(params[1], decimals=3)))
        self.ceusAnalysisGui.peVal.setText(str(np.around(params[0], decimals=3)))
        self.ceusAnalysisGui.tpVal.setText(str(np.around(params[2], decimals=2)))
        self.ceusAnalysisGui.mttVal.setText(str(np.around(params[3], decimals=2)))
        if self.axRes != -1:
            self.ceusAnalysisGui.voiVolumeVal.setText(
                str(np.around(self.roiArea*self.axRes*self.latRes, decimals=1))
            )
            self.ceusAnalysisGui.voiVolumeLabel.setText("ROI Area\n(mm^2)")
        else:
            self.ceusAnalysisGui.voiVolumeVal.setText(
                str(np.around(self.roiArea, decimals=1))
            )
            self.ceusAnalysisGui.voiVolumeLabel.setText("ROI Area\n(Pix)")

        self.ceusAnalysisGui.auc = params[1]
        self.ceusAnalysisGui.pe = params[0]
        self.ceusAnalysisGui.tp = params[2]
        self.ceusAnalysisGui.mtt = params[3]
        if params[4] != 0:
            self.ceusAnalysisGui.t0Val.setText(str(np.around(params[4], decimals=2)))
        else:
            self.ceusAnalysisGui.t0Val.setText(
                str(np.around(self.ticX[0, 0], decimals=2))
            )
        self.ceusAnalysisGui.mc = self.mc
        self.ceusAnalysisGui.roiArea = self.roiArea
        self.ceusAnalysisGui.curFrameIndex = self.curFrameIndex
        self.ceusAnalysisGui.xCur = self.xCur
        self.ceusAnalysisGui.yCur = self.yCur
        self.ceusAnalysisGui.x = self.x
        self.ceusAnalysisGui.y = self.y
        self.ceusAnalysisGui.sliceArray = self.sliceArray
        self.ceusAnalysisGui.x0_bmode = self.x0_bmode
        self.ceusAnalysisGui.y0_bmode = self.y0_bmode
        self.ceusAnalysisGui.w_bmode = self.w_bmode
        self.ceusAnalysisGui.h_bmode = self.h_bmode
        self.ceusAnalysisGui.x0_CE = self.x0_CE
        self.ceusAnalysisGui.y0_CE = self.y0_CE
        self.ceusAnalysisGui.w_CE = self.w_CE
        self.ceusAnalysisGui.h_CE = self.h_CE
        self.ceusAnalysisGui.mcResultsArray = self.mcResultsArray
        self.ceusAnalysisGui.segCoverMask = self.segCoverMask
        self.ceusAnalysisGui.axRes, self.ceusAnalysisGui.latRes = self.axRes, self.latRes
        self.ceusAnalysisGui.cineRate, self.ceusAnalysisGui.fullPath = self.cineRate, self.fullPath

        self.ceusAnalysisGui.curSliceSlider.setMaximum(self.mcResultsArray.shape[0] - 1)
        self.ceusAnalysisGui.curSliceSpinBox.setMaximum(
            self.mcResultsArray.shape[0] - 1
        )
        self.ceusAnalysisGui.curSliceSpinBox.setValue(self.curFrameIndex)
        self.ceusAnalysisGui.curSliceSlider.setValue(self.curFrameIndex)
        self.ceusAnalysisGui.curSliceTotal.setText(
            str(self.mcResultsArray.shape[0] - 1)
        )

        self.ceusAnalysisGui.updateIm()
        self.ceusAnalysisGui.show()
        self.ceusAnalysisGui.curSliceSlider.setValue(self.curFrameIndex)
        self.ceusAnalysisGui.lastGui = self
        self.hide()

    def acceptT0(self):
        self.t0Slider.setHidden(True)
        self.t0Slider.setHidden(True)
        self.acceptT0Button.setHidden(True)
        self.deSelectLastPointButton.setHidden(False)
        self.deSelectLastPointButton.clicked.connect(self.deselectLast)
        self.removeSelectedPointsButton.setHidden(False)
        self.removeSelectedPointsButton.clicked.connect(self.removeSelectedPoints)
        self.restoreLastPointsButton.setHidden(False)
        self.restoreLastPointsButton.clicked.connect(self.restoreLastPoints)
        self.acceptTicButton.setHidden(False)
        self.acceptTicButton.clicked.connect(self.acceptTIC)

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
        yRange = max(self.ticY) - min(self.ticY)
        self.ax.set_ylim(
            ymin=min(self.ticY) - (0.05 * yRange), ymax=max(self.ticY) + (0.05 * yRange)
        )

    def rect_highlight(self, event1, event2):
        self.mask |= self.inside(event1, event2)
        x = self.ticX[:, 0][self.mask]
        y = self.ticY[self.mask]
        addedIndices = np.sort(np.array(list(range(len(self.ticY))))[self.mask])
        self.selectedPoints = []
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
            curMax = self.ticX.shape[0] + len(self.removedPointsX[-1])
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
            if i < curMax and j < len(self.removedPointsX[-1]):
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
            yRange = max(self.ticY) - min(self.ticY)
            self.ax.set_ylim(
                ymin=min(self.ticY) - (0.05 * yRange),
                ymax=max(self.ticY) + (0.05 * yRange),
            )

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
            self.curFrameIndex = self.findSliceFromTime(xdata[ind])
            self.updateIm()
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


def convertArToCmap(cmapName, intensities):
    cmap = plt.get_cmap(cmapName)
    successfulPixels = np.argwhere(intensities >= 0)
    maxIntensity = np.amax(intensities[successfulPixels])
    minIntensity = np.amin(intensities[successfulPixels])
    cmapArray = np.zeros(intensities.shape[0], intensities.shape[1], 5)
    if maxIntensity == minIntensity:
        cmapArray[successfulPixels] = cmapArray[125] + [255]
        return cmapArray
    else:
        for pixel in successfulPixels:
            cmapArray[pixel] = cmap[
                int(
                    255
                    * (intensities[pixel] - minIntensity)
                    / (maxIntensity - minIntensity)
                )
            ] + [255]

    return cmapArray
