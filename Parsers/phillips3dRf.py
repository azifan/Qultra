import numpy as np
import os
import math
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
    
def readSIP3dInterleavedV5(filename, numberOfPlanes=32, numberOfParams=5, numberOfFrames=1e10):
    print('Reading interleaved SIP volume data...')
    file = open(filename, "rb")
    endianness = 'little'
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
    xLoc = (np.arange(0,1,1/pixSizeX)-0.5)*fovSize[0]
    yLoc = (np.arange(0,1,1/pixSizeY)-0.5)*fovSize[1]
    zLoc = (np.arange(0,1,1/pixSizeZ)-0.5)*fovSize[2]

    Z, X, Y = np.meshgrid(zLoc, xLoc, yLoc)

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

    # Interpolate using cubic interpolation
    img = scipy.interpolate.griddata(beamDist, np.pi*lineAngles/180, np.pi*planeAngles/180, rxLines, R, TH, PHI, method='cubic')

    return img, xLoc, yLoc, zLoc


def scanConvert3dVolumeSeries(dbEnvDatFullVolSeries, scParams):
    print("Scan converting volume data...")

    #Scan conversion parameter computation -- ported from Shiying's implementation
    nz, nx, ny = dbEnvDatFullVolSeries[0].shape
    apexDist = scParams.VDB_2D_ECHO_APEX_TO_SKINLINE # Distance of virtual apex to probe surface in mm
    azimSteerAngleStart = scParams.VDB_2D_ECHO_START_WIDTH_GC*180/np.pi # Azimuth steering angle (start) in degree
    azimSteerAngleEnd = scParams.VDB_2D_ECHO_STOP_WIDTH_GC*180/np.pi # Azimuth steering angle (end) in degree
    rxAngAz = np.linspace(azimSteerAngleStart, azimSteerAngleEnd, nx) # Steering angles in degree
    elevSteeerAngleStart = scParams.VDB_THREED_START_ELEVATION_ACTUAL*180/np.pi # Elevation steering angle (start) in degree
    elevSteeerAngleEnd = scParams.VDB_THREED_STOP_ELEVATION_ACTUAL*180/np.pi # Elevation steering angle (end) in degree
    rxAngEl = np.linspace(elevSteeerAngleStart, elevSteeerAngleEnd, ny) # Steering angles in degree
    DepthMm=scParams.VDB_2D_ECHO_STOP_DEPTH_SIP
    imgDpth = np.linspace(0, DepthMm, nz) # Axial distance in mm
    volDepth = scParams.VDB_2D_ECHO_STOP_DEPTH_SIP *(abs(math.sin(math.radians(elevSteeerAngleStart))) + abs(math.sin(math.radians(elevSteeerAngleEnd)))) # Elevation (needs validation)
    volWidth = scParams.VDB_2D_ECHO_STOP_DEPTH_SIP *(abs(math.sin(math.radians(azimSteerAngleStart))) + abs(math.sin(math.radians(azimSteerAngleEnd))))   # Lateral (needs validation)
    volHeight = scParams.VDB_2D_ECHO_STOP_DEPTH_SIP - scParams.VDB_2D_ECHO_START_DEPTH_SIP # Axial (needs validation)
    fovSize   = [volWidth, volDepth, volHeight] # [Lateral, Elevation, Axial]
    imgSize = round(scParams.PixPerMm*[volWidth, volDepth, volHeight]) # [Lateral, Elevation, Axial]

    # Generate image
    imgOut = []
    for k in range(dbEnvDatFullVolSeries.shape[0]):
        rxAngsAzVec = np.linspace(rxAngAz[0],rxAngAz[-1],dbEnvDatFullVolSeries[k].shape[1])
        rxAngsElVec = np.einsum('ikj->ijk', np.linspace(rxAngEl[0],rxAngEl[-1],dbEnvDatFullVolSeries[k].shape[23]))
        curImgOut, x, y, z = scanConvert3Va(dbEnvDatFullVolSeries[k], rxAngsAzVec, rxAngsElVec, imgDpth,imgSize,fovSize, apexDist)
        imgOut.append(curImgOut)
    
    return imgOut


filename = "/Volumes/CREST Data/David_S_Data/David_Duncan 4D_SIP_to_SC_Volume/Data/13.56.19_mf_sip_capture_50_2_1_0.raw"
pathToData = "/Volumes/CREST Data/David_S_Data/David_Duncan 4D_SIP_to_SC_Volume/Data"
file = "13.56.19_mf_sip_capture_50_2_1_0.raw"
numberOfPlanes = 20
readSIPscVDBParams("/Volumes/CREST Data/David_S_Data/David_Duncan 4D_SIP_to_SC_Volume/Data/13.56.19_vdbDump.xml_Extras.txt")
readSIP3dInterleavedV5(filename, numberOfPlanes)