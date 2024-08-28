from typing import List

import numpy as np
from numpy.matlib import repmat
from PIL import Image, ImageDraw

from pyQus.analysisObjects import UltrasoundImage, Config, Window
from pyQus.transforms import computePowerSpec, spectralAnalysisDefault6db

class SpectralAnalysis:
    def __init__(self):
        self.ultrasoundImage: UltrasoundImage = None
        self.config: Config = None
        self.roiWindows: List[Window] = []

        self.scSplineX: List[float]  = None # pix
        self.splineX: List[float] = None # pix
        self.scSplineY: List[float] = None # pix
        self.splineY: List[float] = None # pix

    def splineToPreSc(self):
        self.splineX = [self.ultrasoundImage.xmap[int(y), int(x)] for x, y in zip(self.scSplineX, self.scSplineY)]
        self.splineY = [self.ultrasoundImage.ymap[int(y), int(x)] for x, y in zip(self.scSplineX, self.scSplineY)]

    def generateRoiWindows(self):
        # Some axial/lateral dims
        axialPixSize = round(self.config.axWinSize / self.ultrasoundImage.axialResRf) # mm/(mm/pix)
        lateralPixSize = round(self.config.latWinSize / self.ultrasoundImage.lateralResRf) # mm(mm/pix)
        axial = list(range(self.ultrasoundImage.rf.shape[0]))
        lateral = list(range(self.ultrasoundImage.rf.shape[1]))

        # Overlap fraction determines the incremental distance between ROIs
        axialIncrement = axialPixSize * (1 - self.config.axialOverlap)
        lateralIncrement = lateralPixSize * (1 - self.config.lateralOverlap)

        # Determine ROIS - Find Region to Iterate Over
        axialStart = max(min(self.splineY), axial[0])
        axialEnd = min(max(self.splineY), axial[-1] - axialPixSize)
        lateralStart = max(min(self.splineX), lateral[0])
        lateralEnd = min(max(self.splineX), lateral[-1] - lateralPixSize)

        self.roiWindows = []

        # Determine all points inside the user-defined polygon that defines analysis region
        # The 'mask' matrix - "1" inside region and "0" outside region
        # Pair x and y spline coordinates
        spline = []
        if len(self.splineX) != len(self.splineY):
            print("Spline has unequal amount of x and y coordinates")
            return
        for i in range(len(self.splineX)):
            spline.append((self.splineX[i], self.splineY[i]))

        img = Image.new("L", (self.ultrasoundImage.rf.shape[1], self.ultrasoundImage.rf.shape[0]), 0)
        ImageDraw.Draw(img).polygon(spline, outline=1, fill=1)
        mask = np.array(img)

        for axialPos in np.arange(axialStart, axialEnd, axialIncrement):
            for lateralPos in np.arange(lateralStart, lateralEnd, lateralIncrement):
                # Convert axial and lateral positions in mm to Indices
                axialAbsAr = abs(axial - axialPos)
                axialInd = np.where(axialAbsAr == min(axialAbsAr))[0][0]
                lateralAbsAr = abs(lateral - lateralPos)
                lateralInd = np.where(lateralAbsAr == min(lateralAbsAr))[0][0]

                # Determine if ROI is Inside Analysis Region
                maskVals = mask[
                    axialInd : (axialInd + axialPixSize),
                    lateralInd : (lateralInd + lateralPixSize),
                ]

                # Define Percentage Threshold
                totalNumberOfElementsInRegion = maskVals.size
                numberOfOnesInRegion = len(np.where(maskVals == 1)[0])
                percentageOnes = numberOfOnesInRegion / totalNumberOfElementsInRegion

                if percentageOnes > self.config.windowThresh:
                    # Add ROI to output structure, quantize back to valid distances
                    newWindow = Window()
                    newWindow.left = int(lateral[lateralInd])
                    newWindow.right = int(lateral[lateralInd + lateralPixSize - 1])
                    newWindow.top = int(axial[axialInd])
                    newWindow.bottom = int(axial[axialInd + axialPixSize - 1])
                    self.roiWindows.append(newWindow)
    
    def computeSpecWindows(self):
        if not len(self.roiWindows):
            print("Run 'roiWindowsGenerator' first")
            return
    
        fs = self.config.samplingFrequency
        f0 = self.config.transducerFreqBand[0]
        f1 = self.config.transducerFreqBand[1]
        lowFreq = self.config.analysisFreqBand[0]
        upFreq = self.config.analysisFreqBand[1]

        # Compute spectral parameters for each window
        for window in self.roiWindows:
            imgWindow = self.ultrasoundImage.rf[window.top : window.bottom, window.left : window.right]
            refWindow = self.ultrasoundImage.phantomRf[window.top : window.bottom, window.left : window.right]
            f, ps = computePowerSpec(
                imgWindow, f0, f1, fs
            )  # initially had round(img_gain), but since not used in function, we left it out
            f, rPs = computePowerSpec(
                refWindow, f0, f1, fs
            )  # Same as above, except for round(ref_gain)
            nps = np.asarray(ps) - np.asarray(rPs)  # SUBTRACTION method: log data

            window.results.nps = nps
            window.results.ps = np.asarray(ps)
            window.results.rPs = np.asarray(rPs)
            window.results.f = np.asarray(f)

            # Compute QUS parameters
            mbf, _, _, p, _, _ = spectralAnalysisDefault6db(nps, f, lowFreq, upFreq)
            window.results.mbf = mbf
            window.results.ss = p[0]
            window.results.si = p[1]