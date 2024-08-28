from typing import List

import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from pyQus.spectral import SpectralAnalysis
from src.DataLayer.dataObjects import ScConfig
from src.DataLayer.transforms import condenseArr, expandArr, scanConvert


class SpectralData:
    def __init__(self):
        self.spectralAnalysis: SpectralAnalysis
        self.dataFrame: pd.DataFrame
        self.depth: float # mm
        self.width: float # mm
        self.roiWidthScale: int
        self.roiDepthScale: int
        self.rectCoords: List[int]
        
        self.mbfIm: np.ndarray
        self.ssIm: np.ndarray
        self.siIm: np.ndarray
        self.scMbfIm: np.ndarray
        self.scSsIm: np.ndarray
        self.scSiIm: np.ndarray

        self.minMbf: float; self.maxMbf: float; self.mbfArr: List[float]
        self.minSs: float; self.maxSs: float; self.ssArr: List[float]
        self.minSi: float; self.maxSi: float; self.siArr: List[float]

        self.scConfig: ScConfig | None = None
        self.mbfCmap: list = plt.get_cmap("viridis").colors
        self.ssCmap: list = plt.get_cmap("magma").colors
        self.siCmap: list = plt.get_cmap("plasma").colors

    def convertImagesToRGB(self):
        self.spectralAnalysis.ultrasoundImage.bmode = cv2.cvtColor(
            np.array(self.spectralAnalysis.ultrasoundImage.bmode).astype('uint8'),
            cv2.COLOR_GRAY2RGB
        )
        if self.spectralAnalysis.ultrasoundImage.scBmode is not None:
            self.spectralAnalysis.ultrasoundImage.scBmode = cv2.cvtColor(
                np.array(self.spectralAnalysis.ultrasoundImage.scBmode).astype('uint8'),
                cv2.COLOR_GRAY2RGB
            )

    def drawCmaps(self):
        if not len(self.spectralAnalysis.roiWindows):
            print("No analyzed windows to color")
            return
        
        self.mbfArr = [window.results.mbf for window in self.spectralAnalysis.roiWindows]
        self.minMbf = min(self.mbfArr); self.maxMbf = max(self.mbfArr)
        self.ssArr = [window.results.ss for window in self.spectralAnalysis.roiWindows]
        self.minSs = min(self.ssArr); self.maxSs = max(self.ssArr)
        self.siArr = [window.results.si for window in self.spectralAnalysis.roiWindows]
        self.minSi = min(self.siArr); self.maxSi = max(self.siArr)

        if not len(self.spectralAnalysis.ultrasoundImage.bmode.shape) == 3:
            self.convertImagesToRGB()
        self.mbfIm = self.spectralAnalysis.ultrasoundImage.bmode.copy()
        self.ssIm = self.mbfIm.copy(); self.siIm = self.ssIm.copy()

        for window in self.spectralAnalysis.roiWindows:
            self.mbfIm[window.top: window.bottom+1, window.left: window.right+1] = np.array(
                self.mbfCmap[int((255 / (self.maxMbf-self.minMbf))*(window.results.mbf-self.minMbf))]
            ) * 255
            self.ssIm[window.top: window.bottom+1, window.left: window.right+1] = np.array(
                self.ssCmap[int((255 / (self.maxSs-self.minSs))*(window.results.ss-self.minSs))]
            ) * 255
            self.siIm[window.top: window.bottom+1, window.left: window.right+1] = np.array(
                self.siCmap[int((255 / (self.maxSi-self.minSi))*(window.results.si-self.minSi))]
            ) * 255

    def scanConvertRGB(self, image):
        condensedIm = condenseArr(image)

        scStruct, _, _ = scanConvert(condensedIm, self.scConfig.width, self.scConfig.tilt,
                                        self.scConfig.startDepth, self.scConfig.endDepth)

        return expandArr(scStruct.scArr)
    
    def scanConvertCmaps(self):
        if self.mbfIm is None:
            print("Generate cmaps first")
            return
        
        self.scMbfIm = self.scanConvertRGB(self.mbfIm)
        self.scSsIm = self.scanConvertRGB(self.ssIm)
        self.scSiIm = self.scanConvertRGB(self.siIm)

    @property
    def bmode(self):
        assert len(self.spectralAnalysis.ultrasoundImage.bmode.shape) == 3
        return self.spectralAnalysis.ultrasoundImage.bmode
    
    @property
    def scBmode(self):
        assert len(self.spectralAnalysis.ultrasoundImage.scBmode.shape) == 3
        return self.spectralAnalysis.ultrasoundImage.scBmode
    
    @property
    def finalBmode(self):
        if self.scConfig is not None:
            return self.scBmode
        return self.bmode
    
    @finalBmode.setter
    def finalBmode(self, value: np.ndarray):
        if self.scConfig is not None:
            self.scBmode = value
        else:
            self.bmode = value
    
    @property
    def splineX(self):
        if self.scConfig is not None:
            return self.spectralAnalysis.scSplineX
        return self.spectralAnalysis.splineX
    
    @splineX.setter
    def splineX(self, value: List[float]):
        if self.scConfig is not None:
            self.spectralAnalysis.scSplineX = value
        else:
            self.spectralAnalysis.splineX = value

    @property
    def splineY(self):
        if self.scConfig is not None:
            return self.spectralAnalysis.scSplineY
        return self.spectralAnalysis.splineY
    
    @splineY.setter
    def splineY(self, value: List[float]):
        if self.scConfig is not None:
            self.spectralAnalysis.scSplineY = value
        else:
            self.spectralAnalysis.splineY = value
    
    @property
    def waveLength(self):
        return self.spectralAnalysis.waveLength
    
    @property
    def axWinSize(self):
        return self.spectralAnalysis.config.axWinSize
    
    @axWinSize.setter
    def axWinSize(self, value: float):
        self.spectralAnalysis.config.axWinSize = value

    @property
    def latWinSize(self):
        return self.spectralAnalysis.config.latWinSize
    
    @latWinSize.setter
    def latWinSize(self, value: float):
        self.spectralAnalysis.config.latWinSize = value

    @property
    def axOverlap(self):
        return self.spectralAnalysis.config.axialOverlap
    
    @axOverlap.setter
    def axOverlap(self, value: float):
        self.spectralAnalysis.config.axialOverlap = value
    
    @property
    def latOverlap(self):
        return self.spectralAnalysis.config.lateralOverlap
    
    @latOverlap.setter
    def latOverlap(self, value: float):
        self.spectralAnalysis.config.lateralOverlap = value
    
    @property
    def roiWindowThreshold(self):
        return self.spectralAnalysis.config.windowThresh
    
    @roiWindowThreshold.setter
    def roiWindowThreshold(self, value: float):
        self.spectralAnalysis.config.windowThresh = value
    
    @property
    def analysisFreqBand(self):
        return self.spectralAnalysis.config.analysisFreqBand
    
    @analysisFreqBand.setter
    def analysisFreqBand(self, value: List[int]):
        self.spectralAnalysis.config.analysisFreqBand = value

    @property
    def transducerFreqBand(self):
        return self.spectralAnalysis.config.transducerFreqBand
    
    @transducerFreqBand.setter
    def transducerFreqBand(self, value: List[int]):
        self.spectralAnalysis.config.transducerFreqBand = value
    
    @property
    def samplingFrequency(self):
        return self.spectralAnalysis.config.samplingFrequency
    
    @samplingFrequency.setter
    def samplingFrequency(self, value: int):
        self.spectralAnalysis.config.samplingFrequency = value
    
    @property
    def pixWidth(self):
        return self.finalBmode.shape[1]
    
    @property
    def pixDepth(self):
        return self.finalBmode.shape[0]

    @property
    def numSamplesDrOut(self):
        return self.scConfig.numSamplesDrOut
    
    @property
    def lateralRes(self):
        return self.width / self.finalBmode.shape[1]
    
    @property
    def axialRes(self):
        return self.depth / self.finalBmode.shape[0]
    
    @property
    def finalMbfIm(self):
        if self.scConfig is not None:
            return self.scMbfIm
        return self.mbfIm

    @property
    def finalSsIm(self):
        if self.scConfig is not None:
            return self.scSsIm
        return self.ssIm
    
    @property
    def finalSiIm(self):
        if self.scConfig is not None:
            return self.scSiIm
        return self.siIm