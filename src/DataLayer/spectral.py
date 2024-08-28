import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from pyQus.spectral import SpectralAnalysis
from src.DataLayer.dataObjects import ScConfig
from src.DataLayer.transforms import condenseArr, expandArr, scanConvert


class SpectralData:
    def __init__(self):
        self.spectralAnalysis: SpectralAnalysis = None
        self.scConfig: ScConfig = None
        self.dataFrame: pd.Dataframe = None
        
        self.mbfIm: np.ndarray = None
        self.ssIm: np.ndarray = None
        self.siIm: np.ndarray = None
        self.scMbfIm: np.ndarray = None
        self.scSsIm: np.ndarray = None
        self.scSiIm: np.ndarray = None

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
        
        mbfArr = [window.results.mbf for window in self.spectralAnalysis.roiWindows]
        minMbf = min(mbfArr); maxMbf = max(mbfArr)
        ssArr = [window.results.ss for window in self.spectralAnalysis.roiWindows]
        minSs = min(ssArr); maxSs = max(ssArr)
        siArr = [window.results.si for window in self.spectralAnalysis.roiWindows]
        minSi = min(siArr); maxSi = max(siArr)

        if not len(self.spectralAnalysis.ultrasoundImage.bmode.shape) == 3:
            self.convertImagesToRGB()
        self.mbfIm = self.spectralAnalysis.ultrasoundImage.bmode.copy()
        self.ssIm = self.mbfIm.copy(); self.siIm = self.ssIm.copy()

        for window in self.spectralAnalysis.roiWindows:
            self.mbfIm[window.top: window.bottom+1, window.left: window.right+1] = np.array(
                self.mbfCmap[int((255 / (maxMbf-minMbf))*(window.results.mbf-minMbf))]
            ) * 255
            self.ssIm[window.top: window.bottom+1, window.left: window.right+1] = np.array(
                self.ssCmap[int((255 / (maxSs-minSs))*(window.results.ss-minSs))]
            ) * 255
            self.siIm[window.top: window.bottom+1, window.left: window.right+1] = np.array(
                self.siCmap[int((255 / (maxSi-minSi))*(window.results.si-minSi))]
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
    def splineX(self):
        if self.scConfig is not None:
            return self.spectralAnalysis.scSplineX
        return self.spectralAnalysis.splineX
    
    @property
    def splineY(self):
        if self.scConfig is not None:
            return self.spectralAnalysis.scSplineY
        return self.spectralAnalysis.splineY