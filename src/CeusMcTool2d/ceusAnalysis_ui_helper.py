import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.colors as colors
import nibabel as nib
from PyQt6.QtWidgets import QWidget, QApplication, QHBoxLayout, QFileDialog
from PyQt6.QtGui import QPixmap, QImage

from src.CeusMcTool2d.ceusAnalysis_ui import Ui_ceusAnalysis
from src.CeusMcTool2d.exportData_ui_helper import ExportDataGUI
from src.CeusMcTool2d.genParamap_ui_helper import GenParamapGUI, ParamapInputs

def truncate_colormap(cmap, minval=0.0, maxval=1.0, n=100):
    new_cmap = colors.LinearSegmentedColormap.from_list(
        "trunc({n},{a:.2f},{b:.2f})".format(n=cmap.name, a=minval, b=maxval),
        cmap(np.linspace(minval, maxval, n)),
    )
    return new_cmap


class CeusAnalysisGUI(Ui_ceusAnalysis, QWidget):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.mcResultsArray = None
        self.curFrameIndex = None
        self.xCur = None
        self.yCur = None
        self.x = None
        self.y = None
        self.sliceArray = None
        self.lastGui = None
        self.x0_bmode = None
        self.y0_bmode = None
        self.w_bmode = None
        self.h_bmode = None
        self.x0_CE = None
        self.y0_CE = None
        self.w_CE = None
        self.h_CE = None
        self.exportDataGUI = None
        self.auc = None
        self.pe = None
        self.tp = None
        self.mtt = None
        self.segCoverMask = None
        # self.tmppv = None
        self.genParamapGUI = None
        self.roiArea = None
        self.newData = None
        self.wholecurve: np.ndarray
        self.axRes, self.latRes, self.cineRate, self.fullPath, self.mc = None, None, None, None, None


        self.fig = plt.figure()
        self.canvas = FigureCanvas(self.fig)
        self.horizLayout = QHBoxLayout(self.ticDisplay)
        self.horizLayout.addWidget(self.canvas)
        self.canvas.draw()
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel("Time (s)", fontsize=4, labelpad=0.5)
        self.ax.set_ylabel("Signal Amplitude", fontsize=4, labelpad=0.5)
        self.ax.set_title("Time Intensity Curve (TIC)", fontsize=5, pad=1.5)
        self.ax.tick_params("both", pad=0.3, labelsize=3.6)
        plt.xticks(fontsize=3)
        plt.yticks(fontsize=3)

        self.backFromTic()
        self.showTicButton.setHidden(False)
        self.loadParamapButton.setHidden(False)
        self.aucParamapButton.setHidden(True)
        self.peParamapButton.setHidden(True)
        self.mttParamapButton.setHidden(True)
        self.tpParamapButton.setHidden(True)
        self.backFromParamapButton.setHidden(True)
        self.legend.setHidden(True)
        self.masterParamap = []
        self.curParamap = 0
        self.ticBackButton.clicked.connect(self.backFromTic)
        self.showTicButton.clicked.connect(self.showTic)
        self.backFromParamapButton.clicked.connect(self.backFromParamap)
        self.loadParamapButton.clicked.connect(self.loadParamaps)
        self.aucParamapButton.setCheckable(True)
        self.aucParamapButton.clicked.connect(self.showAuc)
        self.peParamapButton.setCheckable(True)
        self.peParamapButton.clicked.connect(self.showPe)
        self.mttParamapButton.setCheckable(True)
        self.mttParamapButton.clicked.connect(self.showMtt)
        self.tpParamapButton.setCheckable(True)
        self.tpParamapButton.clicked.connect(self.showTp)

        self.horizontalLayout = QHBoxLayout(self.legend)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.figure_leg = plt.figure()
        self.canvas_leg = FigureCanvas(self.figure_leg)
        self.horizontalLayout.addWidget(self.canvas_leg)
        self.curAlpha = 255

        # self.aucParamap = None
        # self.peParamap = None
        # self.tpParamap = None
        # self.mttParamap = None
        # self.tmppvParamap = None

        # self.bmodeCoverPixmap = QPixmap(381, 351)
        # self.bmodeCoverPixmap.fill(Qt.GlobalColor.transparent)
        # self.bmodeCoverLabel.setPixmap(self.bmodeCoverPixmap)

        self.setMouseTracking(True)

        self.curSliceSlider.valueChanged.connect(self.curSliceSliderValueChanged)
        self.curSliceSpinBox.valueChanged.connect(self.curSliceSpinBoxValueChanged)
        self.backButton.clicked.connect(self.backToLastScreen)
        self.exportDataButton.clicked.connect(self.moveToExport)
        self.genParamapButton.clicked.connect(self.startGenParamap)

    def showAuc(self):
        self.figure_leg.clear()
        if self.aucParamapButton.isChecked():
            self.peParamapButton.setChecked(False)
            self.tpParamapButton.setChecked(False)
            self.mttParamapButton.setChecked(False)

            self.curParamap = 1
            self.cmap = plt.get_cmap("viridis").colors
            self.ax_leg = self.figure_leg.add_subplot(111)

            arr = np.linspace(0,100,1000).reshape((1000,1))
            new_cmap1 = truncate_colormap(plt.get_cmap("viridis"))
            self.ax_leg.imshow(arr, aspect='auto', cmap=new_cmap1, origin='lower')
            self.ax_leg.tick_params(axis='y', labelsize=5, pad=0.4)
            self.ax_leg.set_xticks([])
            self.ax_leg.set_yticks([0, 250, 500, 750, 1000])
            self.ax_leg.set_yticklabels(
                [
                    np.round(self.minAuc, decimals=1),
                    np.round(
                        self.minAuc + ((self.maxAuc - self.minAuc) / 4), decimals=1
                    ),
                    np.round(
                        self.minAuc + (2*(self.maxAuc - self.minAuc) / 4), decimals=1
                    ),
                    np.round(
                        self.minAuc + (3 * (self.maxAuc - self.minAuc) / 4), decimals=1
                    ),
                    np.round(self.maxAuc, decimals=1),
                ]
            )
            self.figure_leg.subplots_adjust(
                left=0.4, right=0.95, bottom=0.05, top=0.96
            )
            self.canvas_leg.draw()

            for point in self.pointsPlotted:
                if self.maxAuc == self.minAuc:
                    color = self.cmap[125]
                else:
                    aucVal = self.masterParamap[point[0], point[1], 0]
                    if not self.masterParamap[point[0], point[1], 3]:
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
                self.paramap[point[0], point[1]] = [
                    int(color[2] * 255),
                    int(color[1] * 255),
                    int(color[0] * 255),
                    int(self.curAlpha),
                ]
        else:
            self.curParamap = 0
            self.canvas_leg.draw()
        self.updateIm()

    def showPe(self):
        self.figure_leg.clear()
        if self.peParamapButton.isChecked():
            self.aucParamapButton.setChecked(False)
            self.tpParamapButton.setChecked(False)
            self.mttParamapButton.setChecked(False)

            self.curParamap = 2
            self.cmap = plt.get_cmap("magma").colors
            self.ax_leg = self.figure_leg.add_subplot(111)

            arr = np.linspace(0,100,1000).reshape((1000,1))
            new_cmap1 = truncate_colormap(plt.get_cmap("magma"))
            self.ax_leg.imshow(arr, aspect='auto', cmap=new_cmap1, origin='lower')
            self.ax_leg.tick_params(axis='y', labelsize=5, pad=0.4)
            self.ax_leg.set_xticks([])
            self.ax_leg.set_yticks([0, 250, 500, 750, 1000])
            self.ax_leg.set_yticklabels(
                [
                    np.round(self.minPe, decimals=1),
                    np.round(
                        self.minPe + ((self.maxPe - self.minPe) / 4), decimals=1
                    ),
                    np.round(
                        self.minPe + (2*(self.maxPe - self.minPe) / 4), decimals=1
                    ),
                    np.round(
                        self.minPe + (3 * (self.maxPe - self.minPe) / 4), decimals=1
                    ),
                    np.round(self.maxPe, decimals=1),
                ]
            )
            self.figure_leg.subplots_adjust(
                left=0.4, right=0.95, bottom=0.05, top=0.96
            )
            self.canvas_leg.draw()

            for point in self.pointsPlotted:
                if self.maxPe == self.minPe:
                    color = self.cmap[125]
                else:
                    peVal = self.masterParamap[point[0], point[1], 1]
                    if not self.masterParamap[point[0], point[1], 3]:
                        color = [0, 0, 0]  # window not able to be fit
                    elif self.maxPe == self.minPe:
                        color = self.cmap[125]
                    else:
                        color = self.cmap[
                            int(
                                (255 / (self.maxPe - self.minPe))
                                * (peVal - self.minPe)
                            )
                        ]
                self.paramap[point[0], point[1]] = [
                    int(color[2] * 255),
                    int(color[1] * 255),
                    int(color[0] * 255),
                    int(self.curAlpha),
                ]
        else:
            self.curParamap = 0
            self.canvas_leg.draw()
        self.updateIm()
    
    def showTp(self):
        self.figure_leg.clear()
        if self.tpParamapButton.isChecked():
            self.peParamapButton.setChecked(False)
            self.aucParamapButton.setChecked(False)
            self.mttParamapButton.setChecked(False)

            self.curParamap = 3
            self.cmap = plt.get_cmap("plasma").colors
            self.ax_leg = self.figure_leg.add_subplot(111)

            arr = np.linspace(0,100,1000).reshape((1000,1))
            new_cmap1 = truncate_colormap(plt.get_cmap("plasma"))
            self.ax_leg.imshow(arr, aspect='auto', cmap=new_cmap1, origin='lower')
            self.ax_leg.tick_params(axis='y', labelsize=5, pad=0.4)
            self.ax_leg.set_xticks([])
            self.ax_leg.set_yticks([0, 250, 500, 750, 1000])
            self.ax_leg.set_yticklabels(
                [
                    np.round(self.minTp, decimals=1),
                    np.round(
                        self.minTp + ((self.maxTp - self.minTp) / 4), decimals=1
                    ),
                    np.round(
                        self.minTp + (2*(self.maxTp - self.minTp) / 4), decimals=1
                    ),
                    np.round(
                        self.minTp + (3 * (self.maxTp - self.minTp) / 4), decimals=1
                    ),
                    np.round(self.maxTp, decimals=1),
                ]
            )
            self.figure_leg.subplots_adjust(
                left=0.4, right=0.95, bottom=0.05, top=0.96
            )
            self.canvas_leg.draw()

            for point in self.pointsPlotted:
                if self.maxTp == self.minTp:
                    color = self.cmap[125]
                else:
                    tpVal = self.masterParamap[point[0], point[1], 1]
                    if not self.masterParamap[point[0], point[1], 3]:
                        color = [0, 0, 0]  # window not able to be fit
                    elif self.maxTp == self.minTp:
                        color = self.cmap[125]
                    else:
                        color = self.cmap[
                            min(int(
                                (255 / (self.maxTp - self.minTp))
                                * (tpVal - self.minTp)
                            ), 255
                            )
                        ]
                self.paramap[point[0], point[1]] = [
                    int(color[2] * 255),
                    int(color[1] * 255),
                    int(color[0] * 255),
                    int(self.curAlpha),
                ]
        else:
            self.curParamap = 0
            self.canvas_leg.draw()
        self.updateIm()

    def showMtt(self):
        self.figure_leg.clear()
        if self.mttParamapButton.isChecked():
            self.peParamapButton.setChecked(False)
            self.tpParamapButton.setChecked(False)
            self.aucParamapButton.setChecked(False)
            
            self.curParamap = 4
            self.cmap = plt.get_cmap("cividis").colors
            self.ax_leg = self.figure_leg.add_subplot(111)

            arr = np.linspace(0,100,1000).reshape((1000,1))
            new_cmap1 = truncate_colormap(plt.get_cmap("cividis"))
            self.ax_leg.imshow(arr, aspect='auto', cmap=new_cmap1, origin='lower')
            self.ax_leg.tick_params(axis='y', labelsize=5, pad=0.4)
            self.ax_leg.set_xticks([])
            self.ax_leg.set_yticks([0, 250, 500, 750, 1000])
            self.ax_leg.set_yticklabels(
                [
                    np.round(self.minMtt, decimals=1),
                    np.round(
                        self.minMtt + ((self.maxMtt - self.minMtt) / 4), decimals=1
                    ),
                    np.round(
                        self.minMtt + (2*(self.maxMtt - self.minMtt) / 4), decimals=1
                    ),
                    np.round(
                        self.minMtt + (3 * (self.maxMtt - self.minMtt) / 4), decimals=1
                    ),
                    np.round(self.maxMtt, decimals=1),
                ]
            )
            self.figure_leg.subplots_adjust(
                left=0.4, right=0.95, bottom=0.05, top=0.96
            )
            self.canvas_leg.draw()

            for point in self.pointsPlotted:
                if self.maxMtt == self.minMtt:
                    color = self.cmap[125]
                else:
                    mttVal = self.masterParamap[point[0], point[1], 1]
                    if not self.masterParamap[point[0], point[1], 3]:
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
                self.paramap[point[0], point[1]] = [
                    int(color[2] * 255),
                    int(color[1] * 255),
                    int(color[0] * 255),
                    int(self.curAlpha),
                ]
        else:
            self.curParamap = 0
            self.canvas_leg.draw()
        self.updateIm()
    
    def startGenParamap(self):
        try:
            del self.genParamapGUI
        except AttributeError:
            pass

        if self.mc:
            print("Parametric map generation is not supported on motion compensation segmentation")
            return # no supported yet

        inputs = ParamapInputs()
        inputs.image = np.transpose(self.mcResultsArray, axes=(2,1,0,3))
        inputs.mc = self.mc
        inputs.seg_mask = np.transpose(np.sum(self.segCoverMask, axis=3))
        inputs.seg_mask[:,self.y0_bmode:self.y0_bmode+self.h_bmode] = 0

        if self.axRes != -1:
            inputs.res0, inputs.res1 = self.axRes, self.latRes
        else: # default to mm/pix res for ax and lat
            inputs.res0, inputs.res1 = 1, 1

        inputs.timeConst = 1/self.cineRate

        self.genParamapGUI = GenParamapGUI(inputs)

        if self.axRes == -1: # default to mm/pix res for ax and lat
            self.genParamapGUI.imageDepthLabel.setText("CE Image Depth (pix)")
            self.genParamapGUI.imageWidthLabel.setText("CE Image Width (pix)")
            self.genParamapGUI.axWinSizeLabel.setText("Axial Window Size (pix)")
            self.genParamapGUI.latWinSizeLabel.setText("Lat Window Size (pix)")
        
        imWidth = abs(self.latRes)*(self.w_CE)
        imDepth = abs(self.axRes)*(self.h_CE)
        self.genParamapGUI.imageDepthVal.setText(str(np.round(imDepth, decimals=2)))
        self.genParamapGUI.imageWidthVal.setText(str(np.round(imWidth, decimals=2)))

        self.genParamapGUI.axWinSizeVal.setValue(imDepth/50)
        self.genParamapGUI.latWinSizeVal.setValue(imWidth/50)
        self.genParamapGUI.axOverlapVal.setValue(50)
        self.genParamapGUI.latOverlapVal.setValue(50)

        dir, filename = os.path.split(self.fullPath)
        ext = os.path.splitext(self.fullPath)[-1]
        filename = filename[: (-1 * len(ext))]
        if filename.endswith(".nii"):
            filename = filename[:-4]
        path = os.path.join(dir, "nifti_paramaps_QUANTUS")
        self.genParamapGUI.newFolderPathInput.setText(path)
        self.genParamapGUI.newFileNameInput.setText(str(filename + ".nii.gz"))
        if not os.path.exists(path):
            os.mkdir(path)
        self.genParamapGUI.show()
    

    def loadParamaps(self):
        fileName, _ = QFileDialog.getOpenFileName(
            None, "Open File", filter="*.nii.gz *.nii"
        )
        if fileName != "":
            nibIm = nib.load(fileName)
            self.masterParamap = nibIm.get_fdata().astype(np.double)
            self.masterParamap = np.transpose(self.masterParamap, axes=(1,0,2))
            if self.masterParamap.shape[0] == self.mcResultsArray.shape[2]:
                self.masterParamap = np.transpose(self.masterParamap, axes=(1,0,2))
            if self.masterParamap.shape[0] < self.mcResultsArray.shape[1]: # for separate CEUS and NIfTI
                self.masterParamap = np.pad(self.masterParamap, [(0, (self.mcResultsArray.shape[1]-self.masterParamap.shape[0])), (0,0), (0,0)], mode='constant', constant_values=0)
        else:
            return
        self.paramap = np.zeros(
            (
                self.mcResultsArray.shape[1],
                self.mcResultsArray.shape[2],
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
        if len(self.masterParamap.shape) == 3: # constant ROI
            xlist, ylist = np.where(np.sum(self.segCoverMask[self.curFrameIndex,self.y0_CE:self.y0_CE+self.h_CE,:], axis=2) > 0)
            self.pointsPlotted = np.transpose([xlist, ylist])
        else: #MC ROI
            return # implement once MC paramap can be run without running out of memory

        for i in range(len(self.pointsPlotted)):
            if (
                self.masterParamap[
                    self.pointsPlotted[i][0],
                    self.pointsPlotted[i][1],
                ][3]
                != 0
            ):
                if (
                    self.masterParamap[
                        self.pointsPlotted[i][0],
                        self.pointsPlotted[i][1],
                    ][0]
                    > self.maxAuc
                ):
                    self.maxAuc = self.masterParamap[
                        self.pointsPlotted[i][0],
                        self.pointsPlotted[i][1],
                    ][0]
                if (
                    self.masterParamap[
                        self.pointsPlotted[i][0],
                        self.pointsPlotted[i][1],
                    ][0]
                    < self.minAuc
                ):
                    self.minAuc = self.masterParamap[
                        self.pointsPlotted[i][0],
                        self.pointsPlotted[i][1],
                    ][0]
                if (
                    self.masterParamap[
                        self.pointsPlotted[i][0],
                        self.pointsPlotted[i][1],
                    ][1]
                    > self.maxPe
                ):
                    self.maxPe = self.masterParamap[
                        self.pointsPlotted[i][0],
                        self.pointsPlotted[i][1],
                    ][1]
                if (
                    self.masterParamap[
                        self.pointsPlotted[i][0],
                        self.pointsPlotted[i][1],
                    ][1]
                    < self.minPe
                ):
                    self.minPe = self.masterParamap[
                        self.pointsPlotted[i][0],
                        self.pointsPlotted[i][1],
                    ][1]
                if (
                    self.masterParamap[
                        self.pointsPlotted[i][0],
                        self.pointsPlotted[i][1],
                    ][2]
                    > self.maxTp
                ):
                    self.maxTp = self.masterParamap[
                        self.pointsPlotted[i][0],
                        self.pointsPlotted[i][1],
                    ][2]
                if (
                    self.masterParamap[
                        self.pointsPlotted[i][0],
                        self.pointsPlotted[i][1],
                    ][2]
                    < self.minTp
                ):
                    self.minTp = self.masterParamap[
                        self.pointsPlotted[i][0],
                        self.pointsPlotted[i][1],
                    ][2]
                if (
                    self.masterParamap[
                        self.pointsPlotted[i][0],
                        self.pointsPlotted[i][1],
                    ][3]
                    > self.maxMtt
                ):
                    self.maxMtt = self.masterParamap[
                        self.pointsPlotted[i][0],
                        self.pointsPlotted[i][1],
                    ][3]
                if (
                    self.masterParamap[
                        self.pointsPlotted[i][0],
                        self.pointsPlotted[i][1],
                    ][3]
                    < self.minMtt
                ):
                    self.minMtt = self.masterParamap[
                        self.pointsPlotted[i][0],
                        self.pointsPlotted[i][1],
                    ][3]

        self.showTicButton.setHidden(True)
        self.loadParamapButton.setHidden(True)
        self.aucParamapButton.setHidden(False)
        self.peParamapButton.setHidden(False)
        self.mttParamapButton.setHidden(False)
        self.tpParamapButton.setHidden(False)
        self.backFromParamapButton.setHidden(False)
        self.legend.setHidden(False)
        self.updateIm()

    def backFromParamap(self):
        self.paramap = []
        self.curParamap = 0
        self.showTicButton.setHidden(False)
        self.loadParamapButton.setHidden(False)
        self.aucParamapButton.setHidden(True)
        self.peParamapButton.setHidden(True)
        self.mttParamapButton.setHidden(True)
        self.tpParamapButton.setHidden(True)
        self.backFromParamapButton.setHidden(True)
        self.legend.setHidden(True)
        self.updateIm()

    def showTic(self):
        self.ticDisplay.setHidden(False)
        self.aucLabel.setHidden(False)
        self.peLabel.setHidden(False)
        self.mttLabel.setHidden(False)
        self.tpLabel.setHidden(False)
        self.voiVolumeLabel.setHidden(False)
        self.aucVal.setHidden(False)
        self.peVal.setHidden(False)
        self.mttVal.setHidden(False)
        self.tpVal.setHidden(False)
        self.voiVolumeVal.setHidden(False)
        self.t0Label.setHidden(False)
        self.t0Val.setHidden(False)
        self.ticBackButton.setHidden(False)

        self.showTicButton.setHidden(True)
        self.loadParamapButton.setHidden(True)

    def backFromTic(self):
        self.ticDisplay.setHidden(True)
        self.aucLabel.setHidden(True)
        self.peLabel.setHidden(True)
        self.mttLabel.setHidden(True)
        self.tpLabel.setHidden(True)
        self.voiVolumeLabel.setHidden(True)
        self.aucVal.setHidden(True)
        self.peVal.setHidden(True)
        self.mttVal.setHidden(True)
        self.tpVal.setHidden(True)
        self.voiVolumeVal.setHidden(True)
        self.t0Label.setHidden(True)
        self.t0Val.setHidden(True)
        self.ticBackButton.setHidden(True)

        self.showTicButton.setHidden(False)
        self.loadParamapButton.setHidden(False)

    def moveToExport(self):
        del self.exportDataGUI
        self.exportDataGUI = ExportDataGUI()
        normFact = np.max(self.lastGui.ticY)
        y = self.lastGui.ticY / normFact
        x = self.lastGui.ticX[:, 0] - np.min(self.lastGui.ticX[:, 0])
        curData = {
                "Patient": [self.imagePathInput.text().split("_")[0]],
                "Area Under Curve (AUC)": [self.auc],
                "Peak Enhancement (PE)": [self.pe],
                "Time to Peak (TP)": [self.tp],
                "Mean Transit Time (MTT)": [self.mtt],
                "t0": [self.t0Val.text()],
                "TMPPV": [normFact],
                "ROI Area (mm^2)": [self.roiArea*self.axRes*self.latRes],
                "TIC y vals": [str(np.array(y))],
                "TIC t vals": [str(np.array(x))],
                "Lognorm y vals": [str(np.array(self.wholecurve)) if hasattr(self, "wholecurve") else None],
            }
        self.exportDataGUI.dataFrame = pd.DataFrame.from_dict(curData)
        self.exportDataGUI.lastGui = self
        self.exportDataGUI.setFilenameDisplays(self.imagePathInput.text())
        self.exportDataGUI.show()
        self.exportDataGUI.resize(self.size())
        self.hide()

    def backToLastScreen(self):
        self.lastGui.fig.subplots_adjust(left=0.1, right=0.97, top=0.9, bottom=0.1)
        self.lastGui.show()
        self.hide()

    def updateIm(self):
        self.x = self.mcResultsArray.shape[2]
        self.y = self.mcResultsArray.shape[1]
        self.numSlices = self.mcResultsArray.shape[0]
        self.imX0 = 410
        self.imX1 = 1101
        self.imY0 = 80
        self.imY1 = 501
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
        self.imPlane.move(self.imX0, self.imY0)
        self.imPlane.resize(self.widthScale, self.depthScale)
        self.maskCoverLabel.move(self.imX0, self.imY0)
        self.maskCoverLabel.resize(self.widthScale, self.depthScale)

        self.mcData = np.require(self.mcResultsArray[self.curFrameIndex], np.uint8, "C")
        self.bytesLine, _ = self.mcData[:, :, 0].strides
        self.qImg = QImage(
            self.mcData, self.x, self.y, self.bytesLine, QImage.Format.Format_RGB888
        )
        self.imPlane.setPixmap(
            QPixmap.fromImage(self.qImg).scaled(self.widthScale, self.depthScale)
        )

        if self.curParamap:
            if len(self.masterParamap.shape) == 3: # constant ROI
                self.maskCoverImg = np.require(
                    self.paramap, np.uint8, "C"
                )
            else:
                pass # implement MC once works
        else:
            self.maskCoverImg = np.require(
                self.segCoverMask[self.curFrameIndex], np.uint8, "C"
            )
        self.bytesLineMask, _ = self.maskCoverImg[:, :, 0].strides
        self.qImgMask = QImage(
            self.maskCoverImg, self.x, self.y, self.bytesLineMask, QImage.Format.Format_ARGB32
        )
        self.maskCoverLabel.setPixmap(
            QPixmap.fromImage(self.qImgMask).scaled(self.widthScale, self.depthScale)
        )

    def setFilenameDisplays(self, imageName):
        self.imagePathInput.setHidden(False)

        imFile = imageName.split("/")[-1]

        self.imagePathInput.setText(imFile)
        self.inputTextPath = imageName

    def curSliceSpinBoxValueChanged(self):
        self.curFrameIndex = int(self.curSliceSpinBox.value())
        self.curSliceSlider.setValue(self.curFrameIndex)
        self.updateIm()
        self.update()

    def curSliceSliderValueChanged(self):
        self.curFrameIndex = int(self.curSliceSlider.value())
        self.curSliceSpinBox.setValue(self.curFrameIndex)
        self.updateIm()
        self.update()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    # selectWindow = QWidget()
    ui = CeusAnalysisGUI()
    # ui.selectImage.show()
    ui.show()
    sys.exit(app.exec_())
