
from typing import List

import numpy as np

class SpectralResults:
    def __init__(self):
        self.mbf: float = None # midband fit
        self.ss: float = None # spectral slope
        self.si: float = None # spectral intercept
        self.atCoef: float = None # attenuation coefficient
        self.nps: np.ndarray = None # normalized power spectrum
        self.ps: np.ndarray = None # image power spectrum
        self.rPs: np.ndarray = None # phantom power spectrum
        self.f: np.ndarray = None # frequency array

class Window:
    def __init__(self):
        self.left: int = None
        self.right: int = None
        self.top: int = None
        self.bottom: int = None
        self.results = SpectralResults()

class Config:
    def __init__(self):
        self.transducerFreqBand: List[int] = None # [min, max] (Hz)
        self.analysisFreqBand: List[int] = None # [lower, upper] (Hz)
        self.samplingFrequency: int = None # Hz
        self.axWinSize: float = None # axial length per window (mm)
        self.latWinSize: float = None # lateral width per window (mm)
        self.windowThresh: float = None # % of window area required to be in ROI
        self.axialOverlap: float = None # % of ax window length to move before next window
        self.lateralOverlap: float = None # % of lat window length to move before next window
        self.centerFrequency: float = None # Hz

class UltrasoundImage:
    def __init__(self):
        self.scBmode: np.ndarray = None # rgb
        self.bmode: np.ndarray = None # rgb
        self.rf: np.ndarray = None
        self.phantomRf: np.ndarray = None
        self.axialResRf: float = None # mm/pix
        self.lateralResRf: float = None # mm/pix
        self.xmap: np.ndarray = None # maps (y,x) in SC coords to x preSC coord
        self.ymap: np.ndarray = None # maps (y,x) in SC coords to y preSC coord
        