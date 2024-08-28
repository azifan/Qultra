from scipy.io import loadmat
import numpy as np
from scipy.signal import hilbert

class InfoStruct():
    def __init__(self):
        # Designed fro RF analysis using Terason US System
        # self.minFrequency = 7000000
        # self.maxFrequency = 17000000
        self.minFrequency = 3000000
        self.maxFrequency = 15000000
        self.lowBandFreq = 5000000
        self.upBandFreq = 13000000
        self.depth = None
        self.centerFrequency = 9000000 #Hz

        # For B-Mode image rendering
        self.clipFact = 0.95 
        self.dynRange = 55

        self.studyMode = None
        self.filename = None
        self.filepath = None
        self.probe = None
        self.system = None
        self.studyID = None
        self.studyEXT = None
        self.samples = None
        self.lines = None
        self.width = None
        self.rxFrequency = None
        self.samplingFrequency = None
        self.txFrequency = None
        self.targetFOV = None
        self.numFocalZones = None
        self.numFrames = None
        self.frameSize = None
        self.widthAxis = None
        self.lineDensity = None
        self.lateralRes = None
        self.axialRes = None
        self.maxval = None
        self.tx = None

class DataStruct():
    def __init__(self):
        self.rf = None
        self.bMode = None
        self.scRf = None
        self.scBmode = None
        self.widthPixels = None
        self.depthPixels = None

def readFileInfo(path):
    input = loadmat(path)
    b_data_Zone1 = np.array(input["b_data_Zone1"])
    b_data_Zone2 = np.array(input["b_data_Zone2"])

    Info = InfoStruct()
    Info.studyMode = 'RF'
    Info.lines = input["NumberOfLines"][0][0]
    Info.depth = input["SectorDepthCM"][0][0] * 10 #mm
    Info.rxFrequency = input["FPS"][0][0] * 1000000 #Hz
    Info.samplingFrequency = input["FPS"][0][0] * 1000000 #Hz
    Info.numFocalZones = 2

    focalDepthZone0 = input["FocalDepthZone0"][0][0]

    return Info, focalDepthZone0, b_data_Zone1, b_data_Zone2

def readFileImg(b_data_Zone1, b_data_Zone2, focalDepthZone0, OmniOn, Info):
    # Blend the zones overlap
    M, N = b_data_Zone1.shape
    if OmniOn == 1:
        b_data1 = (b_data_Zone1[:M, :int(N/2)] + b_data_Zone1[:M, int(N/2):])/2
        b_data2 = (b_data_Zone1[:M, :int(N/2)] + b_data_Zone2[:M, int(N/2):])/2
    else:
        b_data1 = b_data_Zone1[:M, :int(N/2)]
        b_data2 = b_data_Zone2[:M, :int(N/2)]
    
    # Hardcoded vals are specific to Terason images used for a study
    endScanOneIndex = round(focalDepthZone0/(Info.depth/10)*M)

    rfData = np.zeros(b_data1.shape)
    b_data_av = (b_data1[endScanOneIndex:2*endScanOneIndex,:]+b_data2[endScanOneIndex:2*endScanOneIndex,:])/2
    rfData[:endScanOneIndex, :] = b_data1[:endScanOneIndex,:]
    rfData[endScanOneIndex:2*endScanOneIndex,:] = b_data_av
    rfData[2*endScanOneIndex:,:] = b_data2[2*endScanOneIndex:,:]

    bmode = np.zeros(rfData.shape)
    for i in range(rfData.shape[1]):
        bmode[:,i] = 20*np.log10(abs(hilbert(rfData[:,i])))

    # dynrange of 40
    bmode = np.clip(bmode, np.amax(bmode)-40, np.amax(bmode))
    bmode -= np.amin(bmode)
    bmode *= (255/np.amax(bmode))

    Data = DataStruct()
    Data.rf = rfData
    Data.bMode = bmode
    Data.widthPixels = bmode.shape[1]
    Data.depthPixels = bmode.shape[0]

    Info.width = Info.depth*2
    Info.axialRes = Info.depth/bmode.shape[0]
    Info.lateralRes = Info.width/bmode.shape[1]
    
    return Data, Info


def getImage(filePath, phantomPath, OmniOn=1):
    # Credit: Steven R. Broadstone, D.Sc., Teratech Corporation dba Terason
    # Parser inspired by MATLAB code writen by Steven
    # Written to parse RF data taken with two focal zones

    imgInfoStruct, focalDepthZone0, b_data_Zone1, b_data_Zone2 = readFileInfo(filePath)
    imgDataStruct, imgInfoStruct = readFileImg(b_data_Zone1, b_data_Zone2, focalDepthZone0, OmniOn, imgInfoStruct)

    refInfoStruct, focalDepthZone0, b_data_Zone1, b_data_Zone2 = readFileInfo(phantomPath)
    refDataStruct, refInfoStruct = readFileImg(b_data_Zone1, b_data_Zone2, focalDepthZone0, OmniOn, refInfoStruct)

    return imgDataStruct, imgInfoStruct, refDataStruct, refInfoStruct