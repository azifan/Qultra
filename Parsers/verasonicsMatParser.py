from mat73 import loadmat as loadmat73
from scipy.io import loadmat
from scipy.signal import hilbert
import numpy as np
from Utils.parserTools import iqToRf

class AnalysisParamsStruct():
    def __init__(self):
        self.t_tilt= 0
        self.t_width = 70
        self.startDepth = 0.04
        self.endDepth = 0.16
        self.endHeight = 500
        self.clip_fact = 0.95
        self.dyn_range = 55
        self.depth = 0.16
        self.width = 0.265

class FileStruct():
    def __init__(self, filedirectory, filename):
        self.name = filename
        self.directory = filedirectory

class OutImStruct():
    def __init__(self):
        self.data = None
        self.orig = None
        self.xmap = None
        self.ymap = None

class DataOutputStruct():
    def __init__(self):
        self.scRF = None
        self.scBmode = None
        self.rf = None
        self.bMode = None

class InfoStruct():
    def __init__(self):
        self.minFrequency = 0
        self.maxFrequency = 15000000
        self.lowBandFreq = 3500000 #Hz
        self.upBandFreq = 10250000 #Hz
        self.centerFrequency = 6875000 #Hz

        self.studyMode = None
        self.filename = None
        self.filepath = None
        self.probe = None
        self.system = None
        self.studyID = None
        self.studyEXT = None
        self.samples = None
        self.lines = None
        self.depthOffset = None
        self.depth = None
        self.width = None
        self.rxFrequency = None
        self.samplingFrequency = None
        self.txFrequency = None
        self.centerFrequency = None
        self.targetFOV = None
        self.numFocalZones = None
        self.numFrames = None
        self.frameSize = None
        self.depthAxis = None
        self.widthAxis = None
        self.lineDensity = None
        self.height = None
        self.pitch = None
        self.dynRange = None
        self.yOffset = None
        self.xOffset = None
        self.gain = None
        self.rxGain = None
        self.userGain = None
        self.txPower = None
        self.power = None
        self.PRF = None
        self.width = None
        self.lateralRes = None
        self.axialRes = None
        self.maxval = None

        # Philips Specific - may repeat and need clean up
        self.tilt1 = None
        self.width1 = None
        self.startDepth1 = None
        self.endDepth1 = None
        self.endHeight = None
        self.clip_fact = None
        self.dyn_range = None
        self.numSonoCTAngles = None

        # One if preSC, the other is postSC resolutions
        self.yResRF = None 
        self.xResRF = None
        self.yRes = None
        self.xRes = None

        # Quad 2 or accounting for change in line density
        self.quad2x = None



def getImage(filename, filedirectory, refname, refdirectory):
    AnalysisParams = AnalysisParamsStruct()
    Files = FileStruct(filedirectory, filename)
    RefFiles = FileStruct(refdirectory, refname)

    [ImgInfo, RefInfo, ImgData, RefData] = getData(Files, RefFiles, AnalysisParams)
    
    return ImgData.scBmode, ImgData, ImgInfo, RefData, RefInfo



def getData(Files, RefFiles, AnalysisParams):
    try:
        input = loadmat(str(Files.directory + Files.name))
    except:
        input = loadmat73(str(Files.directory + Files.name))
    ImgInfo = readFileInfo(Files.name, Files.directory, input)
    [ImgData, ImgInfo] = readFileImg(ImgInfo, input)

    try:
        input = loadmat(str(RefFiles.directory + RefFiles.name))
    except:
        input = loadmat73(str(RefFiles.directory + RefFiles.name))
    RefInfo = readFileInfo(RefFiles.name, RefFiles.directory, input)
    [RefData, RefInfo] = readFileImg(RefInfo, input)

    return [ImgInfo, RefInfo, ImgData, RefData]

def readFileInfo(filename, filepath, input):    
    studyID = filename[:-4]
    studyEXT = filename[-4:]

    Info = InfoStruct()
    Info.studyMode = "RF"
    Info.filename = filename
    Info.filepath = filepath
    Info.probe = "C5-?"
    Info.system = "EPIQ7"
    Info.studyID = studyID
    Info.studyEXT = studyEXT
    # Info.samples = input["pt"][0][0]
    # Info.lines = np.array(input["rf_data_all_fund"]).shape[0]
    Info.depthOffset = 0.04 # probeStruct.transmitoffset
    Info.depth = 40 #mm
    Info.width = 192 #mm
    Info.rxFrequency = 31250000
    Info.samplingFrequency = 31250000
    Info.txFrequency = 6875000 #7812500
    Info.centerFrequency = 6875000 #7812500
    Info.targetFOV = 0
    Info.numFocalZones = 1
    # Info.numFrames = input["NumFrame"][0][0]
    Info.frameSize = np.nan
    Info.depthAxis = np.nan
    Info.widthAxis = np.nan
    # Info.lineDensity = input["multilinefactor"][0][0]
    Info.height = 500
    Info.pitch = 0
    Info.dynRange = 55
    Info.yOffset = 0
    Info.xOffset = 0
    Info.gain = 0
    Info.rxGain = 0
    Info.userGain = 0
    Info.txPower = 0
    Info.power = 0
    Info.PRF = 0

    # Philips Specific
    Info.tilt1 = 0
    Info.width1 = 70
    Info.startDepth1 = 0.04
    Info.endDepth1 = 0.16
    Info.endHeight = 500
    Info.clip_fact = 0.95
    # Info.numSonoCTAngles = input["NumSonoCTAngles"][0][0]
    
    Info.yResRF = 1
    Info.xResRF = 1
    Info.yRes = 1
    Info.xRes = 1
    Info.quad2x = 1

    return Info

def readFileImg(Info, input):
    iqData = np.array(input["IQData"])
    rfData = iqToRf(iqData, 7813000) # get frequency from Preset.Trans.frequency (times 1000000 since stored in MHz)

    bmode = np.zeros(iqData.shape).astype(np.int32)

    # Do Hilbert Transform on each column
    for i in range(iqData.shape[1]):
        bmode[:,i] = 20*np.log10(abs(iqData[:,i]))

    bmode = np.clip(bmode, (0.95*np.amax(bmode)-55), 0.95*np.amax(bmode)).astype(np.float32)
    # bmode -= np.amin(bmode)
    # bmode *= (255/np.amax(bmode))
    # plt.imshow(bmode, cmap="Greys_r")

    ModeIM = rfData

    Data = DataOutputStruct()
    Data.rf = ModeIM
    Data.bMode = bmode
    
    Data.scRF = ModeIM
    Data.scBmode = bmode
    Info.maxval = np.amax(bmode)

    # Info.height = 126.8344
    # Info.width = Info.height*bmode.shape[0]/bmode.shape[1]
    Info.lateralRes = Info.width/bmode.shape[0]
    Info.axialRes = Info.height/bmode.shape[1]

    return Data, Info

if __name__ == "__main__":
    getImage('FatQuantData1.mat', '/Users/davidspector/Documents/MATLAB/Data/', 'FatQuantPhantom1.mat', '/Users/davidspector/Documents/MATLAB/Data/', 0)