import struct
import numpy as np
# from Utils.parserTools import scanConvert, iqToRf
from scipy.signal import hilbert

import numpy as np
from numpy.matlib import repmat
from scipy.interpolate import RectBivariateSpline

class OutImStruct():
    def __init__(self):
        self.data = None
        self.orig = None
        self.xmap = None
        self.ymap = None

def scanConvert(inIm, width, tilt, startDepth, endDepth, desiredHeight=500):
    # ScanConvert sector image
    # Inputs:
    #      InIm          Input image
    #      Width         Sector width of input image in degrees 
    #      Tilt          Tilt of sector image in degrees  
    #      StartDepth    Axial depth of first sample in meters 
    #      EndDepth      Axial depth of last sample in meters   
    #      DesiredHeight Desired vertical size of output image in pixels 
    #      (default 500)
    # 
    #    Outputs:
    #      OutIm         Output (scanconverted) image(s)  
    #      HCm,WCm       Height and Width of image in centimeters 

    #Convert to radians
    width = width*np.pi/180
    tilt = tilt*np.pi/180

    frames = 1
    [samples, beams] = inIm.shape
    depthIncrement = (endDepth-startDepth)/(samples - 1)
    startAngle = 3*np.pi/2 + tilt - width/2
    angleIncrement = width/(beams+1)

    outIm = inIm
    transpose = 0
    background = 0
    height = desiredHeight
    width = 0

    # Set size of image if not defined
    stopAngle = startAngle+((beams-1)*angleIncrement)
    stopDepth = startDepth+((samples-1)*depthIncrement)
    angleRange = np.arange(startAngle, stopAngle+angleIncrement, angleIncrement)

    xmin = -1*max(np.cos((startAngle%np.pi))*np.array([startDepth, stopDepth]))
    xmax = -1*min(np.cos((stopAngle%np.pi))*np.array([startDepth, stopDepth]))
    ymin = min(np.sin((angleRange%np.pi))*startDepth)
    ymax = max(np.sin((angleRange%np.pi))*stopDepth)
    widthScale = abs((xmax-xmin)/(ymax-ymin))

    if not width:
        width = int(np.ceil(height*widthScale))
    
    # Interpolate Image
    radI = 1
    latI = 1
    radSize = samples
    latSize = beams
    if radI > 1 or latI > 1:
        # WARNING: this code has not been tested and may not work. It's not needed for current project
        x = np.array(list(range(radSize)))
        y = np.array(list(range(latSize)))
        xi = np.array(list(range(0, radSize, 1/radI)))
        yi = np.array(list(range(0, latSize, 1/latI)))

        if transpose:
            nyIm = np.zeros((len(yi), len(xi), frames))
        else:
            nyIm = np.zeros((len(xi), len(yi), frames))

        for i in range(frames):
            if transpose:
                nyIm[:,:,i] = RectBivariateSpline(x, y, np.double(outIm[:,:,i])).ev(xi, yi)
            else:
                nyIm[:,:,i] = RectBivariateSpline(y, x, np.double(outIm[:,:,i])).ev(yi, xi)

        outIm = nyIm
    
    nr = (samples+((samples-1)*(radI-1)))
    nb = (beams+((beams-1)*(latI-1)))
    t0 = startAngle
    dt = angleIncrement*(beams)/(nb)
    r0 = startDepth
    dr = depthIncrement*(samples)/(nr)
    nbF = nb
    nrF = nr
    t0F = t0
    dtF = dt
    r0F = r0
    drF = dr

    # Subtract 180 degrees to get transudcer in top of image if startAngle > pi
    t0 = t0 % np.pi
    t0F = t0F % np.pi

    # Define physical limits of image
    stopAngle = t0 + (nb*dt)
    stopDepth = r0 + (nr*dr)
    angleRange = np.arange(t0, stopAngle+dt, dt)
    y0 = min(r0*np.sin(angleRange))
    ymax = max(stopDepth*np.sin(angleRange))
    x0 = min([-1*stopDepth*np.cos(t0), -1*startDepth*np.cos(t0)])
    xmax = max(-1*startDepth*np.cos(stopAngle), -1*stopDepth*np.cos(stopAngle))

    heightCm = (ymax-y0)*100
    widthCm = (xmax-x0)*100

    # Make (x,y)-plane representation of physical image
    xmat = (np.transpose(np.ones((1, height)))*np.arange(0, width, 1))/(width-1)
    ymat = (np.transpose(np.arange(0, height, 1).reshape((1, height)))*np.ones((1, width)))/(height-1)
    xmat = (xmat*(xmax-x0)) + x0
    ymat = (ymat*(ymax-y0)) + y0

    # Transform into polar coordinates (angle, range)
    anglemat = np.arctan2(ymat, -1*xmat)
    rmat = np.sqrt((xmat**2) + (ymat**2))

    # Convert phys. angle and range into beam and sample
    anglemat = np.ceil((anglemat - t0F)/dtF)
    rmat = np.ceil((rmat - r0F)/drF)

    # Find pixels outside active sector
    backgr = np.argwhere((rmat<1))
    backgr = np.concatenate((backgr, np.argwhere(rmat>=nrF)), axis=0)
    backgr = np.concatenate((backgr, np.argwhere(anglemat<1)), axis=0)
    backgr = np.concatenate((backgr, np.argwhere(anglemat>nbF)), axis=0)
    if transpose:
        scMap = (rmat-1)*nbF + anglemat
    else:
        scMap = (anglemat-1)*nrF + rmat

    # Mapping system added to Matlab by Ahmed El Kaffas - April 1st, 2019
    for i in range(backgr.shape[0]):
        scMap[backgr[i,0],backgr[i,1]] = (nbF*nrF)+1
    if np.amax(scMap)<((nbF*nrF)+1):
        scMap[0] = (nbF*nrF)+1
    # inIm_indy = np.zeros(outIm.shape)
    inIm_indx = repmat(np.arange(0, outIm.shape[1]), int(outIm.shape[0]), 1) # <-- maps (y,x) in Iin to indt in Iin
    inIm_indy = np.transpose(repmat(np.arange(0, outIm.shape[0]), int(outIm.shape[1]), 1)) # <-- maps (y,x) in Iout to indr in Iin

    if frames > 1:
        # WARNING: Not tested yet
        scIm = np.zeros((height, width, frames))
        for i in range(frames):
            out = outIm[:,:,i]
            out = np.append(out, background) #?
            scIm[:,:,i] = out[scMap]
        outIm = scIm
    else:
        outIm = np.append(np.transpose(outIm), background)
        inIm_indy = np.append(np.transpose(inIm_indy), background)
        inIm_indx = np.append(np.transpose(inIm_indx), background)

        scMap = np.array(scMap).astype(np.uint64) - 1
        outIm = outIm[scMap]
        inIm_indy = inIm_indy[scMap]
        inIm_indx = inIm_indx[scMap]

        outIm = np.reshape(outIm, (height, width))
        inIm_indy = np.reshape(inIm_indy, (height, width))
        inIm_indx = np.reshape(inIm_indx, (height, width))
    
    hCm = heightCm
    wCm = widthCm
    
    OutIm = OutImStruct()
    OutIm.data = outIm
    OutIm.orig = inIm
    OutIm.ymap = inIm_indy
    OutIm.xmap = inIm_indx
    return outIm, hCm, wCm, OutIm

def iqToRf(iqData, rxFrequency, decimationFactor, carrierFrequency):
    import scipy.signal as ssg    
    iqData = ssg.resample_poly(iqData, decimationFactor, 1) # up-sample by decimation factor
    rfData = np.zeros(iqData.shape)
    t = [i*(1/rxFrequency) for i in range(iqData.shape[0])]
    for i in range(iqData.shape[1]):
        rfData[:,i] = np.real(np.multiply(iqData[:,i], np.exp(1j*(2*np.pi*carrierFrequency*np.transpose(t)))))
    return rfData

def findPreset(filename):
    headersize = 16

    file_obj = open(filename, 'rb')
    hdr = [int.from_bytes(file_obj.read(2), byteorder='little', signed=False) for i in range(2)]
    numAcquiredRxBeams = hdr[0]

    hdr = [int.from_bytes(file_obj.read(2), byteorder='little', signed=False) for i in range(2)]
    numParallelAcquisitions = hdr[1]

    hdr = [int.from_bytes(file_obj.read(2), byteorder='little', signed=False) for i in range(2)]
    numSamplesDrOut = hdr[0]
    file_obj.close()

    return numSamplesDrOut

def readIQ(filename):
    headersize = 16

    file_obj = open(filename, 'rb')
    hdr = [int.from_bytes(file_obj.read(2), byteorder='little', signed=False) for i in range(2)]
    numAcquiredRxBeams = hdr[0]

    hdr = [int.from_bytes(file_obj.read(2), byteorder='little', signed=False) for i in range(2)]
    numParallelAcquisitions = hdr[1]

    hdr = [int.from_bytes(file_obj.read(2), byteorder='little', signed=False) for i in range(2)]
    numSamplesDrOut = hdr[0]
    numSamplesRbfOut = hdr[1]

    hdr = [int.from_bytes(file_obj.read(1), byteorder='little', signed=False) for i in range(4)]
    isPhaseInvertEn = hdr[0]

    hdr = [struct.unpack('f', file_obj.read(4))[0] for i in range(5)]
    decimationFactor = hdr[0]
    rbfDecimationFactor = hdr[1]
    rbfBeMixerFrequency = hdr[2]
    propagationVelCmPerSec = hdr[3]
    digitizingRateHz = hdr[4] 

    # read IQ data
    file_obj.seek(0)
    numSamplesIQAcq = numSamplesDrOut*2
    dataA = np.zeros((numSamplesDrOut*2, numAcquiredRxBeams))
    dataB = np.zeros((numSamplesDrOut*2, numAcquiredRxBeams))
    allData = np.zeros((numSamplesDrOut*2, numAcquiredRxBeams*(1+isPhaseInvertEn)))

    # IQ Acquisition, following parameter always zero
    isPhaseInvertEn = 0
    isRxFreqCompoundEn = 0
    isDiffplusEn = 0

    for ii in range(int(numAcquiredRxBeams/numParallelAcquisitions)):
        for jj in range(numParallelAcquisitions):
            hdr = [int.from_bytes(file_obj.read(4), byteorder='little', signed=False) for i in range(headersize)]
            allData[:headersize, (ii*numParallelAcquisitions) + jj] = hdr

            dat = np.array([int.from_bytes(file_obj.read(4), byteorder='little', signed=False) for i in range(numSamplesIQAcq)])
            dat[dat >= (2**23)] -= (2**24)

            dataA[:,ii*numParallelAcquisitions+jj] = dat[:numSamplesDrOut*2]

            allData[headersize:headersize+(numSamplesDrOut*2)+1, \
                    ii*numParallelAcquisitions+jj] = dat[:min(numSamplesDrOut*2, allData.shape[0]-headersize)]
            
            

    iq = dataA[np.arange(0, numSamplesDrOut*2, 2)] + 1j*dataA[np.arange(1,numSamplesDrOut*2,2)]
    bmode = 20*np.log10(abs(iq))

    return bmode, iq, digitizingRateHz, numSamplesDrOut, decimationFactor

class FileStruct():
    def __init__(self, filedirectory, filename):
        self.name = filename
        self.directory = filedirectory

class DataOutputStruct():
    def __init__(self):
        self.scRF = None
        self.scBmode = None
        self.rf = None
        self.bMode = None

class InfoStruct():
    def __init__(self):
        # US System Configuration
        # US system: Canon Aplio i800 (V4.6SP0008)
        # Transducer: PVI-475BX (i8CX1)
        # self.minFrequency = 1800000 #Hz
        # self.maxFrequency = 6200000 #Hz
        self.minFrequency = 0
        self.maxFrequency = 8000000
        self.lowBandFreq = 2000000 #Hz
        self.upBandFreq = 6000000 #Hz
        self.centerFrequency = 4000000 #Hz

        self.studyMode = None
        self.filename = None
        self.filepath = None
        self.probe = None
        self.system = None
        self.studyID = None
        self.studyEXT = None
        self.width = None
        self.rxFrequency = None
        self.samplingFrequency = None
        self.lateralRes = None
        self.axialRes = None
        self.maxval = None
        self.numSamplesDrOut = None

        # Scan Conversion Params
        self.tilt1 = None
        self.width1 = None
        self.startDepth1 = None
        self.endDepth1 = None

        # One if preSC, the other is postSC resolutions
        self.yResRF = None 
        self.xResRF = None
        self.yRes = None
        self.xRes = None

        # Quad 2 or accounting for change in line density
        self.quad2x = None



def getImage(filename, filedirectory, refname, refdirectory):
    Files = FileStruct(filedirectory, filename)
    RefFiles = FileStruct(refdirectory, refname)

    [ImgInfo, RefInfo, ImgData, RefData] = getData(Files, RefFiles)
    
    return ImgData, ImgInfo, RefData, RefInfo



def getData(Files, RefFiles):
    ImgInfo = readFileInfo(Files.name, Files.directory)
    [ImgData, ImgInfo] = readFileImg(ImgInfo, str(Files.directory + Files.name))

    RefInfo = readFileInfo(RefFiles.name, RefFiles.directory)
    [RefData, RefInfo] = readFileImg(RefInfo, str(RefFiles.directory + RefFiles.name))

    return [ImgInfo, RefInfo, ImgData, RefData]

def readFileInfo(filename, filepath):    
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
    Info.rxFrequency = None #20000000
    Info.samplingFrequency = None #20000000

    # Scan Convert Settings
    Info.tilt1 = 0
    Info.width1 = 70 #degrees

    return Info

def readFileImg(Info, filePath):
    bmode, iqData, Info.rxFrequency, Info.numSamplesDrOut, decimationFactor = readIQ(filePath)
    if Info.numSamplesDrOut == 1400: #Preset 1
        Info.depth = 150 #mm
        print("Preset 1 found!")
    elif Info.numSamplesDrOut == 1496: #Preset 2
        Info.depth = 200 #mm
        print("Preset 2 found!")
    else:
        print("ERROR: No preset found!")
        exit()
    Info.samplingFrequency = Info.rxFrequency
    rfData = iqToRf(iqData, Info.rxFrequency, decimationFactor, Info.centerFrequency)
    bmode = np.zeros(rfData.shape)
    for i in range(rfData.shape[1]):
        bmode[:,i] = 20*np.log10(abs(hilbert(rfData[:,i])))           
    ModeIM = rfData

    Info.endDepth1 = Info.depth/1000 #m
    Info.startDepth1 = Info.endDepth1/4 #m

    [scBmode, hCm1, wCm1, _] = scanConvert(bmode, Info.width1, Info.tilt1, Info.startDepth1, Info.endDepth1)
    [_, hCm1, wCm1, scModeIM] = scanConvert(ModeIM, Info.width1, Info.tilt1, Info.startDepth1, Info.endDepth1)

    Info.depth = hCm1*10 #mm
    Info.width = wCm1*10 #mm
    Info.lateralRes = Info.width/scBmode.shape[1]
    Info.axialRes = Info.depth/scBmode.shape[0]
    Info.maxval = np.amax(scBmode)

    # Info.width = Info.depth*1.5
    # Info.lateralRes = Info.width/bmode.shape[1]
    # Info.axialRes = Info.depth/bmode.shape[0]
    # Info.maxval = np.amax(bmode)

    Data = DataOutputStruct()
    Data.scRF = scModeIM
    Data.scBmode = scBmode * (255/Info.maxval)
    Data.rf = ModeIM
    Data.bMode = bmode * (255/np.amax(bmode))
    
    # Data.scRF = ModeIM
    # Data.scBmode = bmode
    # Info.maxval = np.amax(bmode)

    # Info.height = 126.8344
    # Info.width = Info.height*bmode.shape[0]/bmode.shape[1]
    # Info.lateralRes = Info.width/bmode.shape[0]
    # Info.axialRes = Info.height/bmode.shape[1]

    return Data, Info


if __name__ == "__main__":
    getImage("20220112112155_IQ.bin","/Users/davidspector/Home/Stanford/Project_Data/Misc Data/","20220112112155_IQ.bin","/Users/davidspector/Home/Stanford/Project_Data/Misc Data/")


