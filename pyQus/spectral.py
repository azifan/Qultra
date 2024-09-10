from typing import List

import numpy as np
from PIL import Image, ImageDraw

from pyQus.analysisObjects import UltrasoundImage, Config, Window
from pyQus.transforms import computeHanningPowerSpec, computeHilbertPowerSpec, spectralAnalysisDefault6db

class SpectralAnalysis:
    def __init__(self):
        self.ultrasoundImage: UltrasoundImage
        self.config: Config
        self.roiWindows: List[Window] = []
        self.waveLength: float
        self.attenuationCoef: float
        self.attenuationCorr: float
        self.backScatterCoef: float

        self.scSplineX: List[float] = [] # pix
        self.splineX: List[float] = [] # pix
        self.scSplineY: List[float] = [] # pix
        self.splineY: List[float] = [] # pix

    def initAnalysisConfig(self):
        speedOfSoundInTissue = 1540  # m/s
        self.waveLength = (
            speedOfSoundInTissue / self.config.centerFrequency
        ) * 1000  # mm
        if self.config.axWinSize is None: # not pre-loaded config
            self.config.axWinSize = 10 * self.waveLength
            self.config.latWinSize = 10 * self.waveLength
            self.config.axialOverlap = 0.5; self.config.lateralOverlap = 0.5
            self.config.windowThresh = 0.95

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
            print("Run 'generateRoiWindows' first")
            return
    
        fs = self.config.samplingFrequency
        f0 = self.config.transducerFreqBand[0]
        f1 = self.config.transducerFreqBand[1]
        lowFreq = self.config.analysisFreqBand[0]
        upFreq = self.config.analysisFreqBand[1]

        # Compute spectral parameters for each window
        for window in self.roiWindows:
            imgWindow = self.ultrasoundImage.rf[window.top: window.bottom+1, window.left: window.right+1]
            refWindow = self.ultrasoundImage.phantomRf[window.top: window.bottom+1, window.left: window.right+1]
            f, ps = computeHanningPowerSpec(
                imgWindow, f0, f1, fs
            )  # initially had round(img_gain), but since not used in function, we left it out
            f, rPs = computeHanningPowerSpec(
                refWindow, f0, f1, fs
            )  # Same as above, except for round(ref_gain)
            nps = np.asarray(ps) - np.asarray(rPs)  # SUBTRACTION method: log data

            window.results.nps = nps
            window.results.ps = np.asarray(ps)
            window.results.rPs = np.asarray(rPs)
            window.results.f = np.asarray(f)

            # Compute QUS parameters
            mbf, _, _, p = spectralAnalysisDefault6db(nps, f, lowFreq, upFreq)
            window.results.mbf = mbf
            window.results.ss = p[0]
            window.results.si = p[1]

        minLeft = min([window.left for window in self.roiWindows])
        maxRight = max([window.right for window in self.roiWindows])
        minTop = min([window.top for window in self.roiWindows])
        maxBottom = max([window.bottom for window in self.roiWindows])

        imgWindow = self.ultrasoundImage.rf[minTop: maxBottom+1, minLeft: maxRight+1]
        refWindow = self.ultrasoundImage.phantomRf[minTop: maxBottom+1, minLeft: maxRight+1]
        self.attenuationCoef, self.attenuationCorr = self.computeAttenuationCoef(imgWindow, refWindow)
        self.backScatterCoef = self.computeBackscatterCoefficient(imgWindow, refWindow)
    
    def computeAttenuationCoef(self, rfData, refRfData, verasonics=False):
        samplingFrequency = self.config.samplingFrequency
        startFrequency = self.config.analysisFreqBand[0]
        endFrequency = self.config.analysisFreqBand[1]
        axialRes = self.ultrasoundImage.axialResRf

        sliceDepth = 100

        intensities = []
        for i in range(rfData.shape[0]//sliceDepth):
            sub_window_rf = rfData[i*sliceDepth: (i+1)*sliceDepth]
            f, ps = computeHanningPowerSpec(sub_window_rf, startFrequency, endFrequency, samplingFrequency)
            intensities.append(ps[len(f)//2])

        refIntensities = []
        for i in range(rfData.shape[0]//sliceDepth):
            sub_window_rf = refRfData[i*sliceDepth: (i+1)*sliceDepth]
            f, ps = computeHanningPowerSpec(sub_window_rf, startFrequency, endFrequency, samplingFrequency)
            refIntensities.append(ps[len(f)//2])

        depthCm = np.arange(len(intensities))*sliceDepth*self.ultrasoundImage.axialResRf/10
        normalizedIntensities = np.subtract(intensities, refIntensities)
        p = np.polyfit(depthCm, normalizedIntensities, 1)
        y = depthCm*p[0] + p[1]
        corr = np.corrcoef(y, normalizedIntensities)[0,1]
        attenuationCoeff = -p[0]/(2*self.config.centerFrequency/1e6)
        return attenuationCoeff, corr
    
    def computeBackscatterCoefficient(self, rfData, refRfData):
        f, rf = computeHanningPowerSpec(rfData, self.config.analysisFreqBand[0], self.config.analysisFreqBand[1],
                                     self.config.samplingFrequency)
        _, refRf = computeHanningPowerSpec(refRfData, self.config.analysisFreqBand[0], self.config.analysisFreqBand[1],
                                     self.config.samplingFrequency)
        
        depthDistance = rfData.shape[0]*self.ultrasoundImage.axialResRf/10 #cm
        
        nps = rf[len(f)//2]-refRf[len(f)//2]
        bsc = 1e-3*nps/2*10**(-4*depthDistance*self.config.centerFrequency/1e6*-self.attenuationCoef/(self.config.samplingFrequency/1e6))
        return abs(bsc)