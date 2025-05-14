import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import pyqtgraph as pg
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtWidgets import QWidget, QHBoxLayout
from matplotlib.patches import Rectangle

from pyquantus.utc import UtcData
from src.UtcTool2d.rfAnalysis_ui import Ui_rfAnalysis
from src.UtcTool2d.exportData_ui_helper import ExportDataGUI
import src.UtcTool2d.analysisParamsSelection_ui_helper as AnalysisParamsSelection
from src.UtcTool2d.psGraphDisplay_ui_helper import PsGraphDisplay
from src.UtcTool2d.saveConfig_ui_helper import SaveConfigGUI
from src.UtcTool2d.windowsTooLarge_ui_helper import WindowsTooLargeGUI

class RfAnalysisGUI(QWidget, Ui_rfAnalysis):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setLayout(self.fullScreenLayout)

        self.exportDataGUI = ExportDataGUI()
        self.lastGui: AnalysisParamsSelection.AnalysisParamsGUI
        self.utcData: UtcData
        self.frame: int
        self.newData = None
        self.psGraphDisplay = PsGraphDisplay()
        self.saveConfigGUI = SaveConfigGUI()
        self.windowsTooLargeGUI = WindowsTooLargeGUI()
        self.selectedImage: np.ndarray | None = None
        self.selected_window_index = None
        
        # Flag to track if we're in component selection mode
        self.component_selected = False

        # Display B-Mode
        self.horizontalLayout = QHBoxLayout(self.imDisplayFrame)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.figure = plt.figure()
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self.figure)
        self.horizontalLayout.addWidget(self.canvas)

        self.displayMbfButton.setCheckable(True)
        self.displaySiButton.setCheckable(True)
        self.displaySsButton.setCheckable(True)

        self.displayMbfButton.clicked.connect(self.mbfChecked)
        self.displaySsButton.clicked.connect(self.ssChecked)
        self.displaySiButton.clicked.connect(self.siChecked)
        
        self._shape_cid = None
        self._highlight = None

        # shape button
        self.shapeSelectionButton.setCheckable(True)
        self.shapeSelectionButton.clicked.connect(self.shapeSelectionButtonClicked)

        # Prepare heatmap legend plot
        self.horizLayoutLeg = QHBoxLayout(self.legend)
        self.horizLayoutLeg.setObjectName("horizLayoutLeg")
        self.figLeg = plt.figure()
        self.legAx = self.figLeg.add_subplot(111)
        self.cax = self.figLeg.add_axes([0, 0.1, 0.35, 0.8])
        self.canvasLeg = FigureCanvas(self.figLeg)
        self.horizLayoutLeg.addWidget(self.canvasLeg)
        self.canvasLeg.draw()
        self.backButton.clicked.connect(self.backToLastScreen)
        self.exportDataButton.clicked.connect(self.moveToExport)
        self.displayNpsButton.clicked.connect(self.displayNps)
        self.displayNpsButton.setCheckable(True)
        self.saveConfigButton.clicked.connect(self.saveConfig)
        self.updateLegend("clear")

    def saveConfig(self):
        self.saveConfigGUI.imName = self.imagePathInput.text()
        self.saveConfigGUI.phantomName = self.phantomPathInput.text()
        self.saveConfigGUI.config = self.utcData.utcAnalysis.config
        self.saveConfigGUI.show()

    def completeUtcAnalysis(self) -> int:
        if hasattr(self.utcData, 'scConfig'):
            self.utcData.utcAnalysis.splineToPreSc()
        self.utcData.utcAnalysis.generateRoiWindows()
        success = self.utcData.utcAnalysis.computeUtcWindows(extraParams=False)
        if success < 0:
            self.windowsTooLargeGUI.show()
            return -1
        self.utcData.drawCmaps()
        if hasattr(self.utcData, 'scConfig'):
            self.utcData.scanConvertCmaps()

        mbfMean = np.mean(self.utcData.mbfArr)
        ssMean = np.mean(np.array(self.utcData.ssArr))
        siMean = np.mean(self.utcData.siArr)
        self.avMbfVal.setText(f"{np.round(mbfMean, decimals=1)}")
        self.avSsVal.setText(f"{np.round(ssMean, decimals=2)}")
        self.avSiVal.setText(f"{np.round(siMean, decimals=1)}")

        # Store data that will be needed for NPS plotting
        self.npsArr = [window.results.nps for window in self.utcData.utcAnalysis.roiWindows]
        self.avNps = np.mean(self.npsArr, axis=0)
        self.freqData = self.utcData.utcAnalysis.roiWindows[0].results.f
        
        # Calculate data for the average linear fit line
        self.x_fit = np.linspace(min(self.freqData), max(self.freqData), 100)
        self.y_fit = ssMean*self.x_fit/1e6 + siMean
        
        del self.psGraphDisplay
        self.psGraphDisplay = PsGraphDisplay()
        
        # Reset component selection flag
        self.component_selected = False
        
        # Initial NPS plot setup - this creates the default view
        self.setupDefaultNpsPlot()

        self.plotOnCanvas()
        return 0
        
    def setupDefaultNpsPlot(self):
        """Setup the default NPS plot with all windows and average data"""
        if not hasattr(self, 'psGraphDisplay') or not hasattr(self, 'npsArr'):
            return
            
        # Clear any existing plots
        self.psGraphDisplay.plotGraph.clear()
        
        # Plot individual NPS curves with low opacity
        for i, nps in enumerate(self.npsArr):
            self.psGraphDisplay.plotGraph.plot(self.freqData/1e6, nps, 
                                             pen=pg.mkPen(color=(0, 0, 255, 51)))
        
        # Plot average NPS with higher visibility
        self.psGraphDisplay.plotGraph.plot(self.freqData/1e6, self.avNps, 
                                         pen=pg.mkPen(color="r", width=2), 
                                         name="Average NPS")
        
        # Plot average linear fit line
        self.psGraphDisplay.plotGraph.plot(self.x_fit/1e6, self.y_fit, 
                                         pen=pg.mkPen(color=(255, 172, 28), width=2), 
                                         name="Average Linear Fit")
        
        # Plot frequency band markers if available
        if hasattr(self.utcData, 'analysisFreqBand'):
            self.psGraphDisplay.plotGraph.plot(2*[self.utcData.analysisFreqBand[0]/1e6], 
                                             [np.amin(self.npsArr), np.amax(self.npsArr)], 
                                             pen=pg.mkPen(color="m", width=2))
            self.psGraphDisplay.plotGraph.plot(2*[self.utcData.analysisFreqBand[1]/1e6], 
                                             [np.amin(self.npsArr), np.amax(self.npsArr)], 
                                             pen=pg.mkPen(color="m", width=2))
        
        # Set y-range to fit all data
        self.psGraphDisplay.plotGraph.setYRange(np.amin(self.npsArr), np.amax(self.npsArr))
        
        # Set a clear title
        self.psGraphDisplay.plotGraph.setTitle("All NPS Data")
    
    def shapeSelectionButtonClicked(self):
        print("Shape Selection button clicked")
        
        # Check if shape selection should be activated
        if self.shapeSelectionButton.isChecked():
            # Keep the current parametric map view (don't force MBF)
            if not (self.displayMbfButton.isChecked() or 
                   self.displaySsButton.isChecked() or 
                   self.displaySiButton.isChecked()):
                # If no parametric map is displayed, show MBF as default
                self.displayMbfButton.setChecked(True)
                self.mbfChecked()
                
            # Enable click events on the canvas for selecting shapes
            if self._shape_cid is None:
                self._shape_cid = self.canvas.mpl_connect('button_press_event', self.onImageClick)
            
            # Change button text to indicate selection mode is active
            self.shapeSelectionButton.setText("Cancel Selection")
            self.component_selected = True
        else:
            # Disable shape selection mode
            if self._shape_cid is not None:
                self.canvas.mpl_disconnect(self._shape_cid)
                self._shape_cid = None
            self.shapeSelectionButton.setText("Select Component")
            
            # Redraw without selection highlight if any exists
            if self._highlight is not None:
                self._highlight.remove()
                self._highlight = None
                self.canvas.draw()
            
            # Reset component selection flag
            self.component_selected = False
            
            # Reset to default NPS view if NPS is currently displayed
            if self.displayNpsButton.isChecked():
                self.setupDefaultNpsPlot()

    def onImageClick(self, event):
        """Handle mouse clicks on the image to select components using finalWindowIdxMap"""
        if not event.inaxes:
            return
        
        print(f"Image clicked at: {event.xdata}, {event.ydata}")
        
        # Get the image dimensions
        image_height, image_width = self.selectedImage.shape[:2]
        
        if not hasattr(self.utcData, 'finalWindowIdxMap') or self.utcData.finalWindowIdxMap is None:
            print("Window index map not available")
            return
        
        # Convert click coordinates to integer pixel indices
        # Adjust for possible differences in display vs actual image dimensions
        x_pixel = int(event.xdata / image_width * self.utcData.finalWindowIdxMap.shape[1])
        y_pixel = int(event.ydata / image_height * self.utcData.finalWindowIdxMap.shape[0])
        
        # Ensure pixel coordinates are within the valid range
        x_pixel = max(0, min(x_pixel, self.utcData.finalWindowIdxMap.shape[1] - 1))
        y_pixel = max(0, min(y_pixel, self.utcData.finalWindowIdxMap.shape[0] - 1))
        
        # Get the window index from the map
        selected_index = self.utcData.finalWindowIdxMap[y_pixel, x_pixel]
        
        print(f"Pixel coordinates: ({x_pixel}, {y_pixel}), Selected index: {selected_index}")
        
        # Check if a valid window was selected (-1 indicates no window at that position)
        if selected_index >= 0:
            print(f"Selected window {selected_index}")
            self.highlightSelectedWindow(selected_index)
            self.updateNpsGraphWithSelection(selected_index)
            
            # Set the component selected flag
            self.component_selected = True
            
            # If NPS graph isn't visible yet, show it
            if not self.displayNpsButton.isChecked():
                self.displayNpsButton.setChecked(True)
                self.displayNps()
        else:
            print("No window at selected position")

    def highlightSelectedWindow(self, window_index):
        """Highlight the selected window on the image"""
        # Clear any existing highlight
        if self._highlight is not None:
            self._highlight.remove()
        
        # Get window boundaries
        window = self.utcData.utcAnalysis.roiWindows[window_index]
        left = window.left
        right = window.right
        top = window.top
        bottom = window.bottom
        width = right - left
        height = bottom - top
        
        # Create a rectangle patch to highlight the selected window
        self._highlight = Rectangle(
            (left, top), width, height,
            linewidth=2, edgecolor='r', facecolor='none', zorder=10
        )
        self.ax.add_patch(self._highlight)
        
        # Store the selected window index
        self.selected_window_index = window_index
        
        # Print selection details for debugging
        print(f"Highlighted window {window_index}: left={left}, right={right}, top={top}, bottom={bottom}")
        
        # Redraw canvas to show the highlight
        self.canvas.draw()

    def updateNpsGraphWithSelection(self, window_index):
        """Update the NPS graph to show only selected window data and its linear fit"""
        # Make sure the PS graph display exists
        if not hasattr(self, 'psGraphDisplay') or self.psGraphDisplay is None:
            return
            
        # Clear previous plots in the NPS graph
        self.psGraphDisplay.plotGraph.clear()
        
        # Get frequency data
        window = self.utcData.utcAnalysis.roiWindows[window_index]
        f = window.results.f
        
        # Get the selected window's NPS
        selected_nps = window.results.nps
        
        # Get window's specific SS and SI values for the linear fit
        window_ss = window.results.ss if hasattr(window.results, 'ss') else 0
        window_si = window.results.si if hasattr(window.results, 'si') else 0
        window_mbf = window.results.mbf if hasattr(window.results, 'mbf') else 0
        
        # Create the linear fit line for this specific window
        x = np.linspace(min(f), max(f), 100)
        y = window_ss*x/1e6 + window_si
        
        # Plot selected window's NPS
        self.psGraphDisplay.plotGraph.plot(f/1e6, selected_nps, 
                                          pen=pg.mkPen(color="b", width=2), 
                                          name=f"Window {window_index+1} NPS")
        
        # Plot this window's specific linear fit line
        self.psGraphDisplay.plotGraph.plot(x/1e6, y, 
                                          pen=pg.mkPen(color="g", width=2), 
                                          name="Window Linear Fit")
        
        # Plot frequency band markers
        if hasattr(self.utcData, 'analysisFreqBand'):
            self.psGraphDisplay.plotGraph.plot(2*[self.utcData.analysisFreqBand[0]/1e6], 
                                              [np.amin(selected_nps), np.amax(selected_nps)], 
                                              pen=pg.mkPen(color="m", width=2))
            self.psGraphDisplay.plotGraph.plot(2*[self.utcData.analysisFreqBand[1]/1e6], 
                                              [np.amin(selected_nps), np.amax(selected_nps)], 
                                              pen=pg.mkPen(color="m", width=2))
        
        # Set y-range to fit the data
        self.psGraphDisplay.plotGraph.setYRange(np.amin(selected_nps), np.amax(selected_nps))
        
        # Add window statistics to the title
        self.psGraphDisplay.plotGraph.setTitle(
            f"Window {window_index+1}: MBF={window_mbf:.2f}dB, SS={window_ss:.4f}dB/MHz, SI={window_si:.2f}dB"
        )
        
        # Add window statistics to the info area if it exists
        if hasattr(self.psGraphDisplay, 'infoLabel'):
            self.psGraphDisplay.infoLabel.setText(
                f"Window {window_index+1}:\n"
                f"MBF: {window_mbf:.2f} dB\n"
                f"SS: {window_ss:.4f} dB/MHz\n"
                f"SI: {window_si:.2f} dB"
            )
        
        # Make sure the NPS graph is visible
        self.psGraphDisplay.show()
        
    def displayNps(self):
        print("Display NPS button clicked")
        if self.displayNpsButton.isChecked():
            # If in component selection mode with a window selected, show that window's specific NPS
            if self.component_selected and self.selected_window_index is not None:
                self.updateNpsGraphWithSelection(self.selected_window_index)
            else:
                # Otherwise, show the default view with all NPS data
                self.setupDefaultNpsPlot()
            self.psGraphDisplay.show()
        else:
            self.psGraphDisplay.hide()

    def moveToExport(self):
        # if len(self.utcData.dataFrame):
        del self.exportDataGUI
        self.exportDataGUI = ExportDataGUI()
        curData = {
                "Patient": [self.imagePathInput.text()],
                "Phantom": [self.phantomPathInput.text()],
                "Midband Fit (MBF)": [np.mean(self.utcData.mbfArr)],
                "Spectral Slope (SS)": [np.mean(self.utcData.ssArr)],
                "Spectral Intercept (SI)": [np.mean(self.utcData.siArr)],
                "ROI Name": "",
                "Frame Number": [self.frame],
            }
        self.exportDataGUI.dataFrame = pd.DataFrame.from_dict(curData)
        self.exportDataGUI.lastGui = self
        self.exportDataGUI.setFilenameDisplays(
            self.imagePathInput.text(), self.phantomPathInput.text()
        )
        self.exportDataGUI.show()
        self.exportDataGUI.resize(self.size())
        self.hide()

    def backToLastScreen(self):
        self.psGraphDisplay.hide()
        del self.psGraphDisplay
        self.lastGui.utcData = self.utcData
        self.lastGui.show()
        self.lastGui.resize(self.size())
        self.hide()
        
        # Reset component selection state
        self.component_selected = False
        self.selected_window_index = None

    def setFilenameDisplays(self, imageName, phantomName):
        self.imagePathInput.setHidden(False)
        self.phantomPathInput.setHidden(False)
        self.imagePathInput.setText(imageName)
        self.phantomPathInput.setText(phantomName)

    def plotOnCanvas(self):  # Plot current image on GUI
        self.ax.clear()
        self.selectedImage = self.utcData.finalBmode if self.selectedImage is None else self.selectedImage
        quotient = self.utcData.depth / self.utcData.width
        self.ax.imshow(self.selectedImage, aspect=quotient*(self.selectedImage.shape[1]/self.selectedImage.shape[0]))
        self.figure.set_facecolor((0, 0, 0, 0))
        self.ax.axis("off")

        self.ax.plot(
            self.utcData.splineX,
            self.utcData.splineY,
            color="cyan",
            zorder=1,
            linewidth=0.75,
        )
        self.figure.subplots_adjust(
            left=0, right=1, bottom=0, top=1, hspace=0.2, wspace=0.2
        )
        
        # Removed cursor initialization from here as per feedback
        
        plt.tick_params(bottom=False, left=False, labelbottom=False, labelleft=False)
        
        # Re-add highlight rectangle if one exists
        if self._highlight is not None and self.selected_window_index is not None:
            window = self.utcData.utcAnalysis.roiWindows[self.selected_window_index]
            left = window.left
            right = window.right
            top = window.top
            bottom = window.bottom
            width = right - left
            height = bottom - top
            
            self._highlight = Rectangle(
                (left, top), width, height,
                linewidth=2, edgecolor='r', facecolor='none', zorder=10
            )
            self.ax.add_patch(self._highlight)
        
        self.canvas.draw()  # Refresh canvas

    def mbfChecked(self):
        if self.displayMbfButton.isChecked():
            if self.displaySsButton.isChecked() or self.displaySiButton.isChecked():
                self.displaySsButton.setChecked(False)
                self.displaySiButton.setChecked(False)
            self.selectedImage = self.utcData.finalMbfIm
            self.updateLegend("MBF")
        else:
            self.selectedImage = self.utcData.finalBmode
            self.updateLegend("clear")
        self.plotOnCanvas()
        
    def ssChecked(self):
        if self.displaySsButton.isChecked():
            if self.displayMbfButton.isChecked() or self.displaySiButton.isChecked():
                self.displayMbfButton.setChecked(False)
                self.displaySiButton.setChecked(False)
            self.selectedImage = self.utcData.finalSsIm
            self.updateLegend("SS")
        else:
            self.selectedImage = self.utcData.finalBmode
            self.updateLegend("clear")
        self.plotOnCanvas()
        
    def siChecked(self):
        if self.displaySiButton.isChecked():
            if self.displayMbfButton.isChecked() or self.displaySsButton.isChecked():
                self.displayMbfButton.setChecked(False)
                self.displaySsButton.setChecked(False)
            self.selectedImage = self.utcData.finalSiIm
            self.updateLegend("SI")
        else:
            self.selectedImage = self.utcData.finalBmode
            self.updateLegend("clear")
        self.plotOnCanvas()

    def updateLegend(self, curDisp):
        self.legAx.clear()
        self.figLeg.set_visible(True)
        a = np.array([[0, 1]])
        if curDisp == "" or curDisp == "clear":
            self.figLeg.set_visible(False)
            self.canvasLeg.draw()
            return
        elif curDisp == "MBF":
            img = self.legAx.imshow(a, cmap="viridis")
            self.legAx.set_visible(False)
            self.figLeg.colorbar(
                orientation="vertical", cax=self.cax, mappable=img
            )
            self.legAx.text(2.1, 0.21, "Midband Fit", rotation=270, size=9)
            minVal = self.utcData.minMbf
            maxVal = self.utcData.maxMbf
        elif curDisp == "SS":
            img = self.legAx.imshow(a, cmap="magma")
            self.legAx.set_visible(False)
            self.figLeg.colorbar(orientation="vertical", cax=self.cax, mappable=img)
            self.legAx.text(2.2, 0, "Spectral Slope (1e-6)", rotation=270, size=6)
            self.legAx.tick_params("y", labelsize=7, pad=0.7)
            minVal = self.utcData.minSs
            maxVal = self.utcData.maxSs
        elif curDisp == "SI":
            img = self.legAx.imshow(a, cmap="plasma")
            self.legAx.set_visible(False)
            self.figLeg.colorbar(orientation="vertical", cax=self.cax, mappable=img)
            self.legAx.text(2.2, 0.09, "Spectral Intercept", rotation=270, size=6)
            self.legAx.tick_params("y", labelsize=7, pad=0.7)
            minVal = self.utcData.minSi
            maxVal = self.utcData.maxSi
        else:
            raise ValueError("Invalid value for curDisp")
            
        self.legAx.tick_params("y", labelsize=7, pad=0.5)
        self.cax.set_yticks([0, 0.25, 0.5, 0.75, 1])
        self.cax.set_yticklabels(
            [
                np.round(minVal, 1),
                np.round(
                    ((maxVal - minVal) / 4)
                    + minVal,
                    1,
                ),
                np.round(
                    ((maxVal - minVal) / 2)
                    + minVal,
                    1,
                ),
                np.round(
                    (3 * (maxVal - minVal) / 4)
                    + minVal,
                    1,
                ),
                np.round(maxVal, 1),
            ]
        )
        self.figLeg.set_facecolor((1, 1, 1, 1))
        self.canvasLeg.draw()