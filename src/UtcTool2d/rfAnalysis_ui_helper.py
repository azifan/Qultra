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
        
        self._shape_cid   = None
        self._highlight   = None

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

        npsArr = [window.results.nps for window in self.utcData.utcAnalysis.roiWindows]
        avNps = np.mean(npsArr, axis=0)
        f = self.utcData.utcAnalysis.roiWindows[0].results.f
        x = np.linspace(min(f), max(f), 100)
        y = ssMean*x/1e6 + siMean

        del self.psGraphDisplay
        self.psGraphDisplay = PsGraphDisplay()

        # ps = self.utcData.utcAnalysis.roiWindows[0].results.ps
        # rps = self.utcData.utcAnalysis.roiWindows[0].results.rPs
        # nps = self.utcData.utcAnalysis.roiWindows[0].results.nps
        # self.psGraphDisplay.plotGraph.plot(f/1e6, ps, pen=pg.mkPen(color="b"), name="PS")
        # self.psGraphDisplay.plotGraph.plot(f/1e6, rps, pen=pg.mkPen(color="r"), name="rPS")
        # self.psGraphDisplay.plotGraph.plot(f/1e6, nps+np.amin(ps), pen=pg.mkPen(color="g"), name="NPS")
        
        print("here is where we are")

        for nps in npsArr:
            self.psGraphDisplay.plotGraph.plot(f/1e6, nps, pen=pg.mkPen(color=(0, 0, 255, 51)))
        self.psGraphDisplay.plotGraph.plot(f/1e6, avNps, pen=pg.mkPen(color="r", width=2))
        self.psGraphDisplay.plotGraph.plot(x/1e6, y, pen=pg.mkPen(color=(255, 172, 28), width=2))
        self.psGraphDisplay.plotGraph.plot(2*[self.utcData.analysisFreqBand[0]/1e6], [np.amin(npsArr), np.amax(npsArr)], 
                                            pen=pg.mkPen(color="m", width=2))
        self.psGraphDisplay.plotGraph.plot(2*[self.utcData.analysisFreqBand[1]/1e6], [np.amin(npsArr), np.amax(npsArr)], 
                                            pen=pg.mkPen(color="m", width=2))
        self.psGraphDisplay.plotGraph.setYRange(np.amin(npsArr), np.amax(npsArr))

        self.plotOnCanvas()
        return 0
    
    def shapeSelectionButtonClicked(self):
        print("Shape Selection button clicked")
        
        # Check if shape selection should be activated
        if self.shapeSelectionButton.isChecked():
            if not self.displayMbfButton.isChecked():
                # If MBF isn't displayed yet, we should display it first
                self.displayMbfButton.setChecked(True)
                self.mbfChecked()
                
            # Enable click events on the canvas for selecting shapes
            if self._shape_cid is None:
                self._shape_cid = self.canvas.mpl_connect('button_press_event', self.onImageClick)
            self.cursor.set_active(True)  # Activate the cursor to show where user can click
            
            # Change button text to indicate selection mode is active
            self.shapeSelectionButton.setText("Cancel Selection")
        else:
            # Disable shape selection mode
            if self._shape_cid is not None:
                self.canvas.mpl_disconnect(self._shape_cid)
                self._shape_cid = None
            self.cursor.set_active(False)
            self.shapeSelectionButton.setText("Select Component")
            # Redraw without selection highlight if any exists
            if self._highlight is not None:
                self._highlight.remove()
                self._highlight = None
                self.canvas.draw()

    def onImageClick(self, event):
        """Handle mouse clicks on the image to select components"""
        if not event.inaxes:
            return
        
        print(f"Image clicked at: {event.xdata}, {event.ydata}")
        
        # Get the displayed image size
        display_height, display_width = self.selectedImage.shape[:2]
        
        # Get the relative position within the image (0 to 1)
        rel_x = event.xdata / display_width
        rel_y = event.ydata / display_height
        
        # Find the window that corresponds most closely to this relative position
        selected_window = None
        min_distance = float('inf')
        
        for i, window in enumerate(self.utcData.utcAnalysis.roiWindows):
            # Calculate relative position of window center
            window_width = window.right - window.left
            window_height = window.bottom - window.top
            
            window_center_x = window.left + window_width / 2
            window_center_y = window.top + window_height / 2
            
            # Convert to relative position (0 to 1)
            max_x = max([w.right for w in self.utcData.utcAnalysis.roiWindows])
            max_y = max([w.bottom for w in self.utcData.utcAnalysis.roiWindows])
            
            rel_window_x = window_center_x / max_x
            rel_window_y = window_center_y / max_y
            
            # Calculate distance in relative space
            dx = rel_window_x - rel_x
            dy = rel_window_y - rel_y
            distance = dx*dx + dy*dy
            
            print(f"Window {i}: rel_pos=({rel_window_x:.3f}, {rel_window_y:.3f}), click=({rel_x:.3f}, {rel_y:.3f}), distance={distance:.6f}")
            
            # Update closest window if this one is closer
            if distance < min_distance:
                min_distance = distance
                selected_window = i
        
        print(f"Selected window based on minimum distance: {selected_window}, distance={min_distance:.6f}")
        
        # Only select if the distance is below a threshold
        distance_threshold = 0.1  # Adjust if needed (0.1 = 10% of image size)
        
        if selected_window is not None and min_distance < distance_threshold:
            print(f"Selected window {selected_window}")
            self.highlightSelectedWindow(selected_window)
            self.updateNpsGraphWithSelection(selected_window)
            
            # If NPS graph isn't visible yet, show it
            if not self.displayNpsButton.isChecked():
                self.displayNpsButton.setChecked(True)
                self.displayNps()
        else:
            print("No window selected (too far)")

        # Alternative approach that might work better:
        # Simply use x and y index to find the corresponding window in a grid layout
        if selected_window is None:
            # Get all unique x and y positions to determine the grid
            x_positions = sorted(list(set([w.left for w in self.utcData.utcAnalysis.roiWindows])))
            y_positions = sorted(list(set([w.top for w in self.utcData.utcAnalysis.roiWindows])))
            
            # Calculate number of columns and rows
            num_cols = len(x_positions)
            num_rows = len(y_positions)
            
            # Calculate the grid cell size
            cell_width = display_width / num_cols
            cell_height = display_height / num_rows
            
            # Calculate grid indices based on click position
            grid_x = int(event.xdata / cell_width)
            grid_y = int(event.ydata / cell_height)
            
            # Constrain to valid range
            grid_x = max(0, min(grid_x, num_cols - 1))
            grid_y = max(0, min(grid_y, num_rows - 1))
            
            # Calculate the window index based on grid position
            # This assumes windows are arranged in a grid pattern
            grid_index = grid_y * num_cols + grid_x
            
            # Make sure we don't go out of bounds
            if 0 <= grid_index < len(self.utcData.utcAnalysis.roiWindows):
                selected_window = grid_index
                print(f"Selected window based on grid: {selected_window}")
                self.highlightSelectedWindow(selected_window)
                self.updateNpsGraphWithSelection(selected_window)
                
                # If NPS graph isn't visible yet, show it
                if not self.displayNpsButton.isChecked():
                    self.displayNpsButton.setChecked(True)
                    self.displayNps()

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
        """Update the NPS graph to highlight the selected window's data"""
        # Make sure the PS graph display exists
        if not hasattr(self, 'psGraphDisplay') or self.psGraphDisplay is None:
            return
            
        # Clear previous plots in the NPS graph
        self.psGraphDisplay.plotGraph.clear()
        
        # Get frequency data
        window = self.utcData.utcAnalysis.roiWindows[window_index]
        f = window.results.f
        
        # Get NPS data for all windows (for background)
        npsArr = [win.results.nps for win in self.utcData.utcAnalysis.roiWindows]
        avNps = np.mean(npsArr, axis=0)
        
        # Get mean values for the linear fit line
        ssMean = np.mean(self.utcData.ssArr)
        siMean = np.mean(self.utcData.siArr)
        x = np.linspace(min(f), max(f), 100)
        y = ssMean*x/1e6 + siMean
        
        # Plot other windows' NPS data with low opacity
        for i, nps in enumerate(npsArr):
            if i != window_index:
                self.psGraphDisplay.plotGraph.plot(f/1e6, nps, pen=pg.mkPen(color=(0, 0, 255, 30)))
        
        # Plot average NPS
        self.psGraphDisplay.plotGraph.plot(f/1e6, avNps, pen=pg.mkPen(color="r", width=2), name="Average")
        
        # Plot selected window's NPS with highlight
        selected_nps = npsArr[window_index]
        self.psGraphDisplay.plotGraph.plot(f/1e6, selected_nps, pen=pg.mkPen(color="y", width=3), name=f"Window {window_index+1}")
        
        # Plot linear fit line
        self.psGraphDisplay.plotGraph.plot(x/1e6, y, pen=pg.mkPen(color=(255, 172, 28), width=2), name="Linear Fit")
        
        # Plot frequency band markers
        self.psGraphDisplay.plotGraph.plot(2*[self.utcData.analysisFreqBand[0]/1e6], [np.amin(npsArr), np.amax(npsArr)], 
                                            pen=pg.mkPen(color="m", width=2))
        self.psGraphDisplay.plotGraph.plot(2*[self.utcData.analysisFreqBand[1]/1e6], [np.amin(npsArr), np.amax(npsArr)], 
                                            pen=pg.mkPen(color="m", width=2))
        
        # Add information about the selected window
        window_mbf = window.results.mbf if hasattr(window.results, 'mbf') else "N/A"
        window_ss = window.results.ss if hasattr(window.results, 'ss') else "N/A"
        window_si = window.results.si if hasattr(window.results, 'si') else "N/A"
        
        # Add legend item with window statistics
        self.psGraphDisplay.plotGraph.setTitle(f"Selected Window {window_index+1}: MBF={window_mbf:.2f}, SS={window_ss:.4f}, SI={window_si:.2f}")
        
        # Set y-range to fit all data
        self.psGraphDisplay.plotGraph.setYRange(np.amin(npsArr), np.amax(npsArr))
        
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
        self.cursor = matplotlib.widgets.Cursor(
            self.ax, color="gold", linewidth=0.4, useblit=True
        )
        self.cursor.set_active(False)
        plt.tick_params(bottom=False, left=False, labelbottom=False, labelleft=False)
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
        global curDisp
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