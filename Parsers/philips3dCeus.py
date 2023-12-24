import numpy as np
import os
import math
import nibabel as nib
import scipy.interpolate

class ScParams():
    def __init__(self):
        self.NUM_PLANES = None
        self.pixPerMm = None
        self.VDB_2D_ECHO_APEX_TO_SKINLINE = None
        self.VDB_2D_ECHO_START_WIDTH_GC = None
        self.VDB_2D_ECHO_STOP_WIDTH_GC = None
        self.VDB_THREED_START_ELEVATION_ACTUAL = None
        self.VDB_THREED_STOP_ELEVATION_ACTUAL = None
        self.VDB_2D_ECHO_STOP_DEPTH_SIP = None
        self.VDB_2D_ECHO_START_DEPTH_SIP = None
        self.VDB_2D_ECHO_SLACK_TIME_MM = None

class SipVolParams():
    def __init__(self):
        self.imagePitch = []
        self.numberLines = []
        self.numberAngles = []
        self.elevationIndex = []
        self.numberFocalZone = []
        self.numberLateralMultiline = []
        self.numberElevationMultiline = []

class SipVolDataStruct():
    def __init__(self):
        self.linImage = []
        self.nLinImage = []
        self.linVol = []
        self.nLinVol = []

class OutImStruct():
    def __init__(self):
        self.data = None
        self.orig = None
        self.xmap = None
        self.ymap = None

def readSIPscVDBParams(filename):
    print("Reading SIP scan conversion VDB Params...")
    file = open(filename, "r")
    scParams = ScParams()
    for line in file:
        paramName, paramValue = line.split(" = ")
        paramValue, _ = paramValue.split(" \n")
        paramAr = paramValue.split(" ")
        for i in range(len(paramAr)):
            paramAr[i] = float(paramAr[i])

        if len(paramAr) == 1:
            paramValue = paramAr[0]
        else:
            paramValue = paramAr

        if (paramName == 'NUM_PLANES'):
            scParams.NUM_PLANES = paramValue
        elif (paramName == 'pixPerMm'):
            scParams.pixPerMm = paramValue
        elif (paramName == 'VDB_2D_ECHO_APEX_TO_SKINLINE'):
            scParams.VDB_2D_ECHO_APEX_TO_SKINLINE = paramValue
        elif (paramName == 'VDB_2D_ECHO_START_WIDTH_GC'):
            scParams.VDB_2D_ECHO_START_WIDTH_GC = paramValue
        elif (paramName == 'VDB_2D_ECHO_STOP_WIDTH_GC'):
            scParams.VDB_2D_ECHO_STOP_WIDTH_GC = paramValue
        elif (paramName == 'VDB_THREED_START_ELEVATION_ACTUAL'):
            scParams.VDB_THREED_START_ELEVATION_ACTUAL = paramValue
        elif (paramName == 'VDB_THREED_STOP_ELEVATION_ACTUAL'):
            scParams.VDB_THREED_STOP_ELEVATION_ACTUAL = paramValue
        elif (paramName == 'VDB_2D_ECHO_STOP_DEPTH_SIP'):
            scParams.VDB_2D_ECHO_STOP_DEPTH_SIP = paramValue
        elif (paramName == 'VDB_2D_ECHO_START_DEPTH_SIP'):
            scParams.VDB_2D_ECHO_START_DEPTH_SIP = paramValue
        elif (paramName == 'VDB_2D_ECHO_SLACK_TIME_MM'):
            scParams.VDB_2D_ECHO_SLACK_TIME_MM = paramValue

    file.close()        
    print('Finished reading SIP scan converstion VDB params...')
    return scParams
    
def readSIP3dInterleavedV5(filename, numberOfPlanes=32, numberOfParams=5):
    print('Reading interleaved SIP volume data...')
    file = open(filename, "rb")
    param = SipVolParams()
    img = SipVolDataStruct()
    while (True):
        tmpLine = np.fromfile(file, count=numberOfParams, dtype='<u4')
        
        if numberOfParams == 7:
            # Legacy
            param.imagePitch.append(tmpLine[0])
            param.numberLines.append(tmpLine[1])
            param.numberAngles.append(tmpLine[2])
            param.elevationIndex.append(tmpLine[3])
            param.numberFocalZone.append(tmpLine[4])
            param.numberLateralMultiline.append(tmpLine[5])
            param.numberElevationMultiline.append(tmpLine[6])
        elif numberOfParams == 5:
            # New
            param.imagePitch.append(tmpLine[0])
            param.numberLines.append(tmpLine[1])
            param.numberFocalZone.append(tmpLine[2])
            param.numberLateralMultiline.append(tmpLine[3])
            param.numberElevationMultiline.append(tmpLine[4])
        else:
            print("Unexpected number of header parameters")
            break

        # Read in enough to account for 2 frames (1 linear and 1 non-linear)
        lineBuf = np.fromfile(file, count=int(param.imagePitch[-1]/2)*param.numberLines[-1], dtype='<u2')
        lineBuf = lineBuf.reshape((int(param.imagePitch[-1]/2), param.numberLines[-1]), order='F')

        img.linImage.append(lineBuf[np.arange(0, lineBuf.shape[0], 2)])
        img.nLinImage.append(lineBuf[np.arange(1, lineBuf.shape[0], 2)])

        if file.tell() >= os.fstat(file.fileno()).st_size:
            break

    file.close()

    totalNumFrames = len(img.linImage)
    totalNumFramesFullVol = totalNumFrames - (totalNumFrames % numberOfPlanes)
    numVolumes = int(totalNumFramesFullVol/numberOfPlanes)

    # Reshape data into volumes
    tmpLin = np.zeros((img.linImage[0].shape[0], img.linImage[0].shape[1], numberOfPlanes))
    tmpNLin = np.zeros((img.nLinImage[0].shape[0], img.nLinImage[0].shape[1], numberOfPlanes))

    img.linImage = np.array(img.linImage)
    img.nLinImage = np.array(img.nLinImage)
    img.linVol = np.zeros(([numVolumes] + list(tmpLin.shape)), dtype=np.uint16)
    img.nLinVol = np.zeros(([numVolumes] + list(tmpNLin.shape)), dtype=np.uint16)

    for n in range(numVolumes):
        for m in range(numberOfPlanes):
            ind = n*numberOfPlanes + m
            tmpLin[:,:,m] = img.linImage[ind]
            tmpNLin[:,:,m] = img.nLinImage[ind]
        img.linVol[n] = tmpLin
        img.nLinVol[n] = tmpNLin

    print("Finished reading interleaved SIP volume data...")
    return img

def scanConvert3Va(rxLines, lineAngles, planeAngles, beamDist, imgSize, fovSize, z0):
    # Convert image from polar to Cartesian coordinates using reverse
    # interpolation
    #
    # Usage:
    #   dt = 1/(params.fs*params.upSamp/params.dnSamp);
    #   rxAngAz = computeRxAnglesAz(params);
    #   [img, x, z] = scanConversion(img, rxAngsAz, dt, [512 512], [0.15 0.15], params.c);
    #
    # Inputs:
    #       rxLines      - array with scan line data (samples, lines)
    #       lineAngles   - steering angles [degrees]
    #       dt           - sample period [s]
    #       imgSize      - size in samples of output image [x z]
    #       fovSize      - size in meters of output image [x z]
    #       c            - sound speed in the medium [m/s]
    #       z0           - z offset [m]
    #
    # Outputs:
    #       img         - Image in cartesion coordinates
    #       xLoc        - vector with x coordinates (lateral) [m]
    #       zLoc        - vector with z coordinates (depth) [m]
    #
    # Author: F. Quivira
    # S. Wang (04/2020): created based on scanConvert.m to support 3D/4D volume data (with virtual apex, e.g. X6-1)
    pixSizeX = 1/(imgSize[0]-1)
    pixSizeY = 1/(imgSize[1]-1)
    pixSizeZ = 1/(imgSize[2]-1)

    # Create Cartesian grid and convert to polar coordinates
    xLoc = (np.arange(0,1+(pixSizeX/2),pixSizeX)-0.5)*fovSize[0]
    yLoc = (np.arange(0,1+(pixSizeY/2),pixSizeY)-0.5)*fovSize[1]
    zLoc = np.arange(0,1+(pixSizeZ/2),pixSizeZ)*fovSize[2]
    Z, X, Y = np.meshgrid(zLoc, xLoc, yLoc, indexing='ij')

    # S. Wang: geometry for 3D virtual apex
    # vaElType = 3
    # if (vaElType == 1): # Elevation: no virtual apex (by Shiying)
    #     PHI = np.arctan2(Y, Z)
    #     TH = np.arctan2(X, np.sqrt(np.square(Y) + np.square(np.sqrt(np.square(Y) + np.square(Z)) + z0)))
    #     R = np.sqrt(np.square(X) + np.square(np.sqrt(np.square(Y)+np.square(Z)) + z0))*np.sqrt(np.square(Y)+np.square(Z))/(np.sqrt(np.square(Y)+np.square(Z))+z0)
    """ From original MATLAB code:
    % S. Wang: geometry for 3D virtual apex
vaElType = 3;
switch vaElType
    case 1 % Elevation: no virtual apex (by Shiying)
        PHI = atan2(Y, Z);
        TH = atan2(X, sqrt(Y.^2 + (sqrt(Y.^2 + Z.^2) + z0).^2));
        R = sqrt(X.^2 + (sqrt(Y.^2 + Z.^2) + z0).^2).*sqrt(Y.^2 + Z.^2)./(sqrt(Y.^2 + Z.^2) + z0);
    case 2 % Elevation: flat array (by Shiying)
        PHI = atan2(Y, Z + z0);
        TH = atan2(X, sqrt(Y.^2 + (Z + z0).^2));
        R = sqrt(X.^2 + Y.^2 + (Z + z0).^2).*Z./(Z + z0);
    case 3 % Elevation: curved array, lens radius = distToApex (by Shiying)
        PHI = atan2(Y, Z + z0);
        TH = atan2(X, sqrt(Y.^2 + (Z + z0).^2));
        R = sqrt(X.^2 + Y.^2 + (Z + z0).^2).*(1 - z0/sqrt(Y.^2 + (Z + z0).^2));
    case 4 % 3D Tangent Coordinate System to Cartesian (by Man)
        PHI = atan2(Y, Z + z0);
        TH = atan2(X, Z + z0);
        R = sqrt(X.^2 + Y.^2 + (Z + z0).^2);
    case 5 % 3D Cylindrical Coordinate System to Cartesian (by Shiying)
        PHI = atan2(Y, Z + z0);
        TH = atan2(X, sqrt(Y.^2 + (Z + z0).^2));
        R = sqrt(X.^2 + Y.^2 + (Z + z0).^2);
end
     """
    PHI = np.arctan2(Y, Z+z0)
    TH = np.arctan2(X, np.sqrt(np.square(Y)+np.square(Z+z0)))
    R = np.sqrt(np.square(X)+np.square(Y)+np.square(Z+z0))*(1-z0/np.sqrt(np.square(Y)+np.square(Z+z0)))

    img = scipy.interpolate.interpn((beamDist, np.pi*lineAngles/180, np.pi*planeAngles/180), rxLines, (R, TH, PHI), bounds_error=False, method='linear', fill_value=0)
    img /= np.amax(img)
    img *= 255

    print("Finished scan converting volume data...")

    return img


def scanConvert3dVolumeSeries(dbEnvDatFullVolSeries, scParams):
    print("Scan converting volume data...")

    #Scan conversion parameter computation -- ported from Shiying's implementation
    if len(dbEnvDatFullVolSeries.shape) != 4:
        numVolumes = 1
        nz, nx, ny = dbEnvDatFullVolSeries.shape
    else:
        numVolumes = dbEnvDatFullVolSeries.shape[0]
        nz, nx, ny = dbEnvDatFullVolSeries[0].shape
    apexDist = scParams.VDB_2D_ECHO_APEX_TO_SKINLINE # Distance of virtual apex to probe surface in mm
    azimSteerAngleStart = scParams.VDB_2D_ECHO_START_WIDTH_GC*180/np.pi # Azimuth steering angle (start) in degree
    azimSteerAngleEnd = scParams.VDB_2D_ECHO_STOP_WIDTH_GC*180/np.pi # Azimuth steering angle (end) in degree
    rxAngAz = np.linspace(azimSteerAngleStart, azimSteerAngleEnd, nx) # Steering angles in degree
    elevSteerAngleStart = scParams.VDB_THREED_START_ELEVATION_ACTUAL*180/np.pi # Elevation steering angle (start) in degree
    elevSteerAngleEnd = scParams.VDB_THREED_STOP_ELEVATION_ACTUAL*180/np.pi # Elevation steering angle (end) in degree
    rxAngEl = np.linspace(elevSteerAngleStart, elevSteerAngleEnd, ny) # Steering angles in degree
    DepthMm=scParams.VDB_2D_ECHO_STOP_DEPTH_SIP
    imgDpth = np.linspace(0, DepthMm, nz) # Axial distance in mm
    volDepth = scParams.VDB_2D_ECHO_STOP_DEPTH_SIP *(abs(math.sin(math.radians(elevSteerAngleStart))) + abs(math.sin(math.radians(elevSteerAngleEnd)))) # Elevation (needs validation)
    volWidth = scParams.VDB_2D_ECHO_STOP_DEPTH_SIP *(abs(math.sin(math.radians(azimSteerAngleStart))) + abs(math.sin(math.radians(azimSteerAngleEnd))))   # Lateral (needs validation)
    volHeight = scParams.VDB_2D_ECHO_STOP_DEPTH_SIP - scParams.VDB_2D_ECHO_START_DEPTH_SIP # Axial (needs validation)
    fovSize   = [volWidth, volDepth, volHeight] # [Lateral, Elevation, Axial]
    imgSize = np.array(np.round(np.array([volWidth, volDepth, volHeight])*scParams.pixPerMm), dtype=np.uint32) # [Lateral, Elevation, Axial]

    # Generate image
    imgOut = []
    if numVolumes > 1:
        for k in range(numVolumes):
            rxAngsAzVec = np.linspace(rxAngAz[0],rxAngAz[-1],dbEnvDatFullVolSeries[k].shape[1])
            rxAngsElVec = np.einsum('ikj->ijk', np.linspace(rxAngEl[0],rxAngEl[-1],dbEnvDatFullVolSeries[k].shape[2]))
            curImgOut = scanConvert3Va(dbEnvDatFullVolSeries[k], rxAngsAzVec, rxAngsElVec, imgDpth,imgSize,fovSize, apexDist)
            imgOut.append(curImgOut)
        imgOut = np.array(imgOut)
    else:
        rxAngsAzVec = np.linspace(rxAngAz[0],rxAngAz[-1],dbEnvDatFullVolSeries.shape[1])
        rxAngsElVec = np.linspace(rxAngEl[0],rxAngEl[-1],dbEnvDatFullVolSeries.shape[2])
        curImgOut = scanConvert3Va(dbEnvDatFullVolSeries, rxAngsAzVec, rxAngsElVec, imgDpth,imgSize,fovSize, apexDist)
        imgOut = curImgOut
    
    return imgOut, fovSize

def image4dCeusPostXbr(pathToData, sipFilename):
    # Input paths/filenames
    vdbFilename = str(sipFilename.split("_")[0] + "_vdbDump.xml")
    scParamFilename = str(vdbFilename+"_Extras.txt")
    
    # Read in Parameter data (primarily for scan conversion)
    scParams = readSIPscVDBParams(os.path.join(pathToData, scParamFilename))
    scParams.NUM_PLANES = 20
    scParams.pixPerMm = 2.5

    # Read in the interleaved SIP volume data time series (both linear/non-linear parts)
    sipVolDat = readSIP3dInterleavedV5(os.path.join(pathToData, sipFilename),  scParams.NUM_PLANES)
    
    # Scan Conversion of 3D volume time series (Only doing 1 volume here)
    scSipVolDat = SipVolDataStruct()
    scSipVolDat.linVol, imgDims = scanConvert3dVolumeSeries(sipVolDat.linVol[0], scParams)
    scSipVolDat.nLinVol, nLineImgDims = scanConvert3dVolumeSeries(sipVolDat.nLinVol[0], scParams)

    upperLim = 255
    lowerLim = 145 # trial and error
    scSipVolDat.nLinVol = np.clip(scSipVolDat.nLinVol, a_min=lowerLim, a_max=upperLim)
    scSipVolDat.nLinVol -= np.amin(scSipVolDat.nLinVol)
    scSipVolDat.nLinVol *= int(255/np.amax(scSipVolDat.nLinVol))
    scSipVolDat.linVol = np.clip(scSipVolDat.linVol, a_min=lowerLim, a_max=upperLim)
    scSipVolDat.linVol -= np.amin(scSipVolDat.linVol)
    scSipVolDat.linVol *= int(255/np.amax(scSipVolDat.linVol))

    return scSipVolDat.linVol, scSipVolDat.nLinVol, imgDims # assume linear and non-linear images have same dims

def makeNifti(dataFolder, destinationPath):
    imarray_org, imarray_bmode_org, imgDims = image4dCeusPostXbr(os.path.dirname(dataFolder), os.path.basename(dataFolder))
    timeconst = 0 # no framerate for now
    orgres = [imgDims[0]/imarray_org.shape[2], imgDims[1]/imarray_org.shape[1], imgDims[0]/imarray_org.shape[2]]

    if len(imarray_org.shape) <= 3:
        imarray_org = np.reshape(imarray_org, (1, imarray_org.shape[0], imarray_org.shape[1], imarray_org.shape[2]))
        imarray_bmode_org = np.reshape(imarray_bmode_org, (1, imarray_bmode_org.shape[0], imarray_bmode_org.shape[1], imarray_bmode_org.shape[2]))

    imarray_org = imarray_org.astype('uint8')
    imarray_org = imarray_org.swapaxes(1, 2)
    imarray_org = np.transpose(imarray_org)
    imarray_org = imarray_org.swapaxes(0, 2)
    imarray_bmode_org = imarray_bmode_org.astype('uint8')
    imarray_bmode_org = imarray_bmode_org.swapaxes(1, 2)
    imarray_bmode_org = np.transpose(imarray_bmode_org)
    imarray_bmode_org = imarray_bmode_org.swapaxes(0, 2)
    
    affine = np.eye(4)
    niiarray = nib.Nifti1Image(imarray_org.astype('uint8'), affine)
    niiarray.header['pixdim'] = [4., orgres[0], orgres[1], orgres[2], timeconst, 0., 0., 0.]
    outputPath = os.path.join(destinationPath, str(os.path.basename(dataFolder)+'.nii.gz'))
    nib.save(niiarray, outputPath)

    niiarray = nib.Nifti1Image(imarray_bmode_org.astype('uint8'), affine)
    niiarray.header['pixdim'] = [4., orgres[0], orgres[1], orgres[2], timeconst, 0., 0., 0.]
    outputPathBmode = os.path.join(destinationPath, str(os.path.basename(dataFolder)+ '_BMODE_.nii.gz'))
    nib.save(niiarray, outputPathBmode)
    return outputPath, outputPathBmode

if __name__ == "__main__":
    pathToData = "/Volumes/CREST Data/David_S_Data/David_Duncan 4D_SIP_to_SC_Volume/Data"
    file = "13.56.19_mf_sip_capture_50_2_1_0.raw"
    numberOfPlanes = 20
    # image4dCeusPostXbr(pathToData, file)
    makeNifti(str(pathToData + '/' + file), "hi")