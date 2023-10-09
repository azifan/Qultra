from CeusTool3d.ceusAnalysis_ui import *
from CeusTool3d.exportData_ui_helper import *
import Utils.lognormalFunctions as lf

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from PyQt5.QtWidgets import QWidget, QApplication, QFileDialog, QHBoxLayout
from PyQt5.QtGui import QImage, QPixmap, QPainter
from PyQt5.QtCore import QLine, Qt

import platform
system = platform.system()

class CeusAnalysisGUI(Ui_ceusAnalysis, QWidget):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.lastGui = None
        self.painted = "none"
        self.pointsPlotted = None
        self.dataFrame = None
        self.data4dImg = None
        self.curSliceIndex = None
        self.newXVal = None
        self.newYVal = None
        self.newZVal = None
        self.x = None
        self.y = None
        self.z = None
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
        self.maskBytesLineSag = None
        self.widthCor = None
        self.heightCor = None
        self.bytesLineCor = None
        self.maskCorW = None
        self.maskCorH = None
        self.maskBytesLineCor = None
        self.sliceArray = None
        self.voxelScale = None
        self.sliceSpinBoxChanged = False
        self.sliceSliderChanged = False

        self.setMouseTracking(True)

        self.axCoverPixmap = QPixmap(321, 301)
        self.axCoverPixmap.fill(Qt.transparent)
        self.axCoverLabel.setPixmap(self.axCoverPixmap)

        self.sagCoverPixmap = QPixmap(321, 301)
        self.sagCoverPixmap.fill(Qt.transparent)
        self.sagCoverLabel.setPixmap(self.sagCoverPixmap)

        self.corCoverPixmap = QPixmap(321, 301)
        self.corCoverPixmap.fill(Qt.transparent)
        self.corCoverLabel.setPixmap(self.corCoverPixmap)

        self.horizLayout = QHBoxLayout(self.ticDisplay)
        self.fig = plt.figure()
        self.canvas = FigureCanvas(self.fig)
        self.horizLayout.addWidget(self.canvas)
        self.canvas.draw()
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel("Time (s)", fontsize=4, labelpad=0.5)
        self.ax.set_ylabel("Signal Amplitude", fontsize=4, labelpad=0.5)
        self.ax.set_title("Time Intensity Curve (TIC)", fontsize=5, pad=1.5)
        self.ax.tick_params('both', pad=0.3, labelsize=3.6)
        plt.xticks(fontsize=3)
        plt.yticks(fontsize=3)

        self.voiAlphaSpinBox.setValue(100)

        self.backButton.clicked.connect(self.backToLastScreen)
        self.saveDataButton.clicked.connect(self.saveData)
        self.exportDataButton.clicked.connect(self.moveToExport)
        self.curSliceSlider.valueChanged.connect(self.curSliceSliderValueChanged)
        self.curSliceSpinBox.valueChanged.connect(self.curSliceSpinBoxValueChanged)
        self.voiAlphaSpinBox.valueChanged.connect(self.alphaValueChanged)

    def mouseMoveEvent(self, event):
        self.xCur = event.x()
        self.yCur = event.y()
        self.updateCrosshair()

    def updateCrosshair(self):
        scrolling = "none"
        # if self.scrolling:
        if self.xCur < 721 and self.xCur > 400 and self.yCur < 341 and self.yCur > 40 and (self.painted == "none" or self.painted == "ax"):
            self.actualX = int((self.xCur - 401)*(self.widthAx-1)/321)
            self.actualY = int((self.yCur - 41)*(self.heightAx-1)/301)
            scrolling = "ax"
            self.axCoverLabel.pixmap().fill(Qt.transparent)
            painter = QPainter(self.axCoverLabel.pixmap())
            painter.setPen(Qt.yellow)
            axVertLine = QLine(self.xCur - 401, 0, self.xCur - 401, 301)
            axLatLine = QLine(0, self.yCur - 41, 321, self.yCur - 41)
            painter.drawLines([axVertLine, axLatLine])
            painter.end()
        elif self.xCur < 1131 and self.xCur > 810 and self.yCur < 341 and self.yCur > 40 and (self.painted == "none" or self.painted == "sag"):
            self.actualX = int((self.xCur-811)*(self.widthSag-1)/321)
            self.actualY = int((self.yCur-41)*(self.heightSag-1)/301)
            scrolling = "sag"
            self.sagCoverLabel.pixmap().fill(Qt.transparent)
            painter = QPainter(self.sagCoverLabel.pixmap())
            painter.setPen(Qt.yellow)
            sagVertLine = QLine(self.xCur - 811, 0, self.xCur - 811, 301)
            sagLatLine = QLine(0, self.yCur - 41, 321, self.yCur - 41)
            painter.drawLines([sagVertLine, sagLatLine])
            painter.end()
        elif self.xCur < 1131 and self.xCur > 810 and self.yCur < 711 and self.yCur > 410 and (self.painted == "none" or self.painted == "cor"):
            self.actualX = int((self.xCur-811)*(self.widthCor-1)/321)
            self.actualY = int((self.yCur-411)*(self.heightCor-1)/301)
            scrolling = "cor"
            self.corCoverLabel.pixmap().fill(Qt.transparent)
            painter = QPainter(self.corCoverLabel.pixmap())
            painter.setPen(Qt.yellow)
            corVertLine = QLine(self.xCur - 811, 0, self.xCur - 811, 301)
            corLatLine = QLine(0, self.yCur - 411, 321, self.yCur-411)
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
            sagVertLine = QLine(int(self.newZVal/self.z*321), 0, int(self.newZVal/self.z*321), 301)
            sagLatLine = QLine(0, int(self.newYVal/self.y*301), 321, int(self.newYVal/self.y*301))
            painter.drawLines([sagVertLine, sagLatLine])
            painter.end()
            
            self.corCoverLabel.pixmap().fill(Qt.transparent)
            painter = QPainter(self.corCoverLabel.pixmap())
            painter.setPen(Qt.yellow)
            corVertLine = QLine(int(self.newXVal/self.x*321), 0, int(self.newXVal/self.x*321), 301)
            corLatLine = QLine(0, int(self.newZVal/self.z*301), 321, int(self.newZVal/self.z*301))
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
            axVertLine = QLine(int(self.newXVal/self.x*321), 0, int(self.newXVal/self.x*321), 301)
            axLatLine = QLine(0, int(self.newYVal/self.y*301), 321, int(self.newYVal/self.y*301))
            painter.drawLines([axVertLine, axLatLine])
            painter.end()
            
            self.corCoverLabel.pixmap().fill(Qt.transparent)
            painter = QPainter(self.corCoverLabel.pixmap())
            painter.setPen(Qt.yellow)
            corVertLine = QLine(int(self.newXVal/self.x*321), 0, int(self.newXVal/self.x*321), 301)
            corLatLine = QLine(0, int(self.newZVal/self.z*301), 321, int(self.newZVal/self.z*301))
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
            axVertLine = QLine(int(self.newXVal/self.x*321), 0, int(self.newXVal/self.x*321), 301)
            axLatLine = QLine(0, int(self.newYVal/self.y*301), 321, int(self.newYVal/self.y*301))
            painter.drawLines([axVertLine, axLatLine])
            painter.end()

            self.sagCoverLabel.pixmap().fill(Qt.transparent)
            painter = QPainter(self.sagCoverLabel.pixmap())
            painter.setPen(Qt.yellow)
            sagVertLine = QLine(int(self.newZVal/self.z*321), 0, int(self.newZVal/self.z*321), 301)
            sagLatLine = QLine(0, int(self.newYVal/self.y*301), 321, int(self.newYVal/self.y*301))
            painter.drawLines([sagVertLine, sagLatLine])
            painter.end()
            self.update()
    
    def alphaValueChanged(self):
        self.curAlpha = int(self.voiAlphaSpinBox.value())
        self.voiAlphaSpinBoxChanged = False
        self.voiAlphaStatus.setValue(self.curAlpha)
        for i in range(len(self.pointsPlotted)):
            self.maskCoverImg[self.pointsPlotted[i][0], self.pointsPlotted[i][1], self.pointsPlotted[i][2],3] = self.curAlpha
        self.changeAxialSlices()
        self.changeSagSlices()
        self.changeCorSlices()

    def moveToExport(self):
        if len(self.dataFrame):
            del self.exportDataGUI
            self.exportDataGUI = ExportDataGUI()
            self.exportDataGUI.dataFrame = self.dataFrame
            self.exportDataGUI.lastGui = self
            self.exportDataGUI.setFilenameDisplays(self.imagePathInput.text())
            self.exportDataGUI.show()
            self.hide()

    def saveData(self):
        if self.newData is None:
            self.newData = {"Patient": self.imagePathInput.text(), "Area Under Curve (AUC)": self.auc, \
                            "Peak Enhancement (PE)": self.pe, "Time to Peak (TP)": self.tp, \
                            "Mean Transit Time (MTT)": self.mtt, "TMPPV": self.tmppv, "VOI Volume (mm^3)": self.voxelScale}
            self.dataFrame = self.dataFrame.append(self.newData, ignore_index=True)

    def backToLastScreen(self):
        self.lastGui.dataFrame = self.dataFrame
        self.lastGui.show()
        self.hide()


    def acceptTIC(self):
        self.pointsPlotted = self.lastGui.pointsPlotted
        self.dataFrame = self.lastGui.dataFrame
        self.data4dImg = self.lastGui.data4dImg
        self.curSliceIndex = self.lastGui.curSliceIndex
        self.newXVal = self.lastGui.newXVal
        self.newYVal = self.lastGui.newYVal
        self.newZVal = self.lastGui.newZVal
        self.x = self.lastGui.x
        self.y = self.lastGui.y
        self.z = self.lastGui.z
        self.maskCoverImg = self.lastGui.maskCoverImg
        self.widthAx = self.lastGui.widthAx
        self.heightAx = self.lastGui.heightAx
        self.bytesLineAx = self.lastGui.bytesLineAx
        self.maskAxW = self.lastGui.maskAxW
        self.maskAxH = self.lastGui.maskAxH
        self.maskBytesLineAx = self.lastGui.maskBytesLineAx
        self.widthSag = self.lastGui.widthSag
        self.heightSag = self.lastGui.heightSag
        self.bytesLineSag = self.lastGui.bytesLineSag
        self.maskSagW = self.lastGui.maskSagW
        self.maskSagH = self.lastGui.maskSagH
        self.maskBytesLineSag = self.lastGui.maskBytesLineSag
        self.widthCor = self.lastGui.widthCor
        self.heightCor = self.lastGui.heightCor
        self.bytesLineCor = self.lastGui.bytesLineCor
        self.maskCorW = self.lastGui.maskCorW
        self.maskCorH = self.lastGui.maskCorH
        self.maskBytesLineCor = self.lastGui.maskBytesLineCor
        self.sliceArray = self.lastGui.sliceArray
        self.voxelScale = self.lastGui.voxelScale

        self.exportDataButton.setHidden(False)
        self.saveDataButton.setHidden(False)

        self.analysisParamsSidebar.setStyleSheet(u"QFrame {\n"
"	background-color: rgb(99, 0, 174);\n"
"	border: 1px solid black;\n"
"}")

        self.ticAnalysisSidebar.setStyleSheet(u"QFrame {\n"
"	background-color: rgb(99, 0, 174);\n"
"	border: 1px solid black;\n"
"}")

        self.ax.clear()
        self.ax.plot(self.lastGui.ticX[:,0], self.lastGui.ticY)

        # self.sliceArray = self.ticEditor.ticX[:,1]
        # if self.curSliceIndex>= len(self.sliceArray):
        #     self.curSliceSlider.setValue(len(self.sliceArray)-1)
        #     self.curSliceSliderValueChanged()
        # self.curSliceSlider.setMaximum(len(self.sliceArray)-1)
        # self.curSliceSpinBox.setMaximum(len(self.sliceArray)-1)

        tmppv = np.max(self.lastGui.ticY)
        self.lastGui.ticY = self.lastGui.ticY/tmppv;
        x = self.lastGui.ticX[:,0] - np.min(self.lastGui.ticX[:,0])

        # Bunch of checks
        if np.isnan(np.sum(self.lastGui.ticY)):
            print('STOPPED:NaNs in the VOI')
            return;
        if np.isinf(np.sum(self.lastGui.ticY)):
            print('STOPPED:InFs in the VOI')
            return;

        # Do the fitting
        try:
            params, popt, wholecurve = lf.data_fit([x, self.lastGui.ticY], tmppv);
            self.ax.plot(self.lastGui.ticX[:,0], wholecurve)
            range = max(self.lastGui.ticX[:,0]) - min(self.lastGui.ticX[:,0])
            self.ax.set_xlim(xmin=min(self.lastGui.ticX[:,0])-(0.05*range), xmax=max(self.lastGui.ticX[:,0])+(0.05*range))
        except RuntimeError:
            print('RunTimeError')
            params = np.array([np.max(self.lastGui.ticY)*tmppv, np.trapz(self.lastGui.ticY*tmppv, x=self.lastGui.ticX[:,0]), self.lastGui.ticX[-1,0], np.argmax(self.lastGui.ticY), np.max(self.lastGui.ticX[:,0])*2, 0]);
        self.fig.subplots_adjust(left=0.1, right=0.97, top=0.85, bottom=0.25)
        self.canvas.draw()
        self.lastGui.ticY *= tmppv

        self.aucVal.setText(str(np.around(params[1], decimals=3)))
        self.peVal.setText(str(np.around(params[0], decimals=3)))
        self.tpVal.setText(str(np.around(params[2], decimals=2)))
        self.mttVal.setText(str(np.around(params[3], decimals=2)))
        self.tmppvVal.setText(str(np.around(tmppv, decimals=1)))
        self.voiVolumeVal.setText(str(np.around(self.voxelScale, decimals=1)))
        self.auc = params[1]
        self.pe = params[0]
        self.tp = params[2]
        self.mtt = params[3]
        self.tmppv = tmppv
        self.dataFrame = self.lastGui.dataFrame

        self.lastGui.hide()
        self.curSliceSlider.setValue(self.lastGui.curSliceIndex)
        self.curSliceSliderValueChanged()
        self.alphaValueChanged()
        self.show()

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
            self.curSliceIndex= int(self.curSliceSlider.value())
            self.curSliceSpinBox.setValue(self.sliceArray[self.curSliceIndex])
            self.sliceSliderChanged = False
        self.changeAxialSlices()
        self.changeSagSlices()
        self.changeCorSlices()

    def findSliceFromTime(self, inputtedTime):
        i = 0
        while i < len(self.sliceArray):
            if inputtedTime < self.sliceArray[i]:
                break
            i += 1
        if i == len(self.sliceArray):
            i -= 1
        elif i > 0:
            if (self.sliceArray[i] - inputtedTime) > (self.sliceArray[i-1] - inputtedTime):
                i -= 1
        if i < 0:
            i = 0
        return i

    def changeAxialSlices(self):

        self.axialFrameNum.setText(str(self.newZVal+1))

        self.data2dAx = self.data4dImg[:,:,self.newZVal, self.curSliceIndex]#, self.curSliceIndex #defining 2D data for axial
        self.data2dAx = np.flipud(self.data2dAx) #flipud
        self.data2dAx = np.rot90(self.data2dAx,3) #rotate
        self.data2dAx = np.require(self.data2dAx,np.uint8,'C')

        self.bytesLineAx, _ = self.data2dAx.strides
        self.qImgAx = QImage(self.data2dAx,self.widthAx, self.heightAx, self.bytesLineAx, QImage.Format_Grayscale8)

        tempAx = self.maskCoverImg[:,:,self.newZVal,:] #2D data for axial
        tempAx = np.flipud(tempAx) #flipud
        tempAx = np.rot90(tempAx,3) #rotate ccw 270
        tempAx = np.require(tempAx,np.uint8, 'C')

        self.curMaskAxIm = QImage(tempAx, self.maskAxW, self.maskAxH, self.maskBytesLineAx, QImage.Format_ARGB32) #creating QImage

        self.maskLayerAx.setPixmap(QPixmap.fromImage(self.curMaskAxIm).scaled(321,301)) #displaying QPixmap in the QLabels
        self.axialPlane.setPixmap(QPixmap.fromImage(self.qImgAx).scaled(321,301)) #otherwise, would just display the normal unmodified q_img


    def changeSagSlices(self):

        self.sagittalFrameNum.setText(str(self.newXVal+1))

        self.data2dSag = self.data4dImg[self.newXVal,:,:, self.curSliceIndex]#, self.curSliceIndex
        self.data2dSag = np.flipud(self.data2dSag) #flipud
        self.data2dSag = np.rot90(self.data2dSag,2) #rotate
        self.data2dSag = np.fliplr(self.data2dSag)
        self.data2dSag = np.require(self.data2dSag,np.uint8,'C')

        self.bytesLineSag, _ = self.data2dSag.strides
        self.qImgSag = QImage(self.data2dSag,self.widthSag, self.heightSag, self.bytesLineSag, QImage.Format_Grayscale8)

        tempSag = self.maskCoverImg[self.newXVal,:,:,:] #2D data for sagittal
        tempSag = np.flipud(tempSag) #flipud
        tempSag = np.rot90(tempSag,2) #rotate ccw 180
        tempSag = np.fliplr(tempSag)
        tempSag = np.require(tempSag,np.uint8,'C')
        
        self.curMaskSagIm = QImage(tempSag, self.maskSagW, self.maskSagH, self.maskBytesLineSag, QImage.Format_ARGB32)

        self.maskLayerSag.setPixmap(QPixmap.fromImage(self.curMaskSagIm).scaled(321,301))
        self.sagPlane.setPixmap(QPixmap.fromImage(self.qImgSag).scaled(321,301))


    def changeCorSlices(self):

        self.coronalFrameNum.setText(str(self.newYVal+1))

        self.data2dCor = self.data4dImg[:,self.newYVal,:, self.curSliceIndex]#, self.curSliceIndex
        self.data2dCor = np.rot90(self.data2dCor,1) #rotate
        self.data2dCor = np.flipud(self.data2dCor) #flipud
        self.data2dCor = np.require(self.data2dCor, np.uint8,'C')

        self.bytesLineCor, _ = self.data2dCor.strides
        self.qImgCor = QImage(self.data2dCor,self.widthCor,self.heightCor, self.bytesLineCor, QImage.Format_Grayscale8)

        tempCor = self.maskCoverImg[:,self.newYVal,:,:] #2D data for coronal
        tempCor = np.rot90(tempCor,1) #rotate ccw 90
        tempCor = np.flipud(tempCor) #flipud
        tempCor = np.require(tempCor,np.uint8,'C')

        self.curMaskCorIm = QImage(tempCor, self.maskCorW, self.maskCorH, self.maskBytesLineCor, QImage.Format_ARGB32)

        self.maskLayerCor.setPixmap(QPixmap.fromImage(self.curMaskCorIm).scaled(321,301))
        self.corPlane.setPixmap(QPixmap.fromImage(self.qImgCor).scaled(321,301))