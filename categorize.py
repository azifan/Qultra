import os
import struct
import numpy as np
from Parsers.siemensRfdParser import readHeader

def categorize():
    path = os.listdir("/Volumes/CREST Data/David_S_Data/Thyroid_Data_RFD")

    samplesAr = []
    presetNum = 0
    path[3] = path[0]
    path[0] = "Phantom"
    
    for folder in path:
        if os.path.isdir(str("/Volumes/CREST Data/David_S_Data/Thyroid_Data_RFD/" + folder)):
            files = os.listdir(str("/Volumes/CREST Data/David_S_Data/Thyroid_Data_RFD/" + folder))
            for file in files:
                if file.endswith('.rfd') and not file.startswith('._'):
                
                    header = readHeader(str("/Volumes/CREST Data/David_S_Data/Thyroid_Data_RFD/" + folder + '/' + file))

                    header = [header.rfgi.tagName, header.rfgi.dataSize, header.rfgi.headerVersion, header.rfgi.rfAcqGain, header.rfgi.minDataVectorRange, \
                        header.rfgi.numFramesAcquired, header.rfgi.rfAxialMinCm, header.rfgi.rfAxialSpanCm, header.rfgi.isBmodeInfoFrameDep, header.rfgi.isMmodeInfoFrameDep, \
                        header.rfgi.isColorInfoFrameDep, header.rfgi.isDopplerInfoFrameDep, header.rfgi.isSetDepInfoFrameDep, header.rfgi.isBeamDepInfoFrameDep, \
                        header.idx1.tagName, header.idx1.dataSize, len(header.idx1.frame), header.idx1.startOffset, header.rfbd.tagName, \
                        header.rfbd.dataSize, header.rfbd.headerVersion, header.rfbd.numSamplesPerVector, header.rfbd.numVectorsPerFrame, header.rfbd.mode, header.rfbd.set, \
                        header.rfbd.positionX, header.rfbd.positionZ, header.rfbd.thetaRad, header.avih.tagName, header.avih.dataSize, header.avih.dwMicroSecPerFrame, \
                        header.avih.dwMaxBytesPerSec, header.avih.resesrved1, header.avih.dwFlags, header.avih.dwTotalFrames, header.avih.dwInitialFrames, header.avih.dwStreams, \
                        header.avih.dwSuggestedBufferSize, header.avih.dwWidth, header.avih.dwHeight, header.avih.dwReserved, header.sffm.tagName, header.sffm.dataSize, \
                        header.sffm.sffVersion, header.sffm.platformName, header.sffm.platformVersion, header.sffm.operatingSystem, header.sffm.operatingSystemVersion, \
                        header.sffm.cpu, header.strh.tagName, header.strh.dataSize, header.strh.fccType, header.strh.fccHandler, header.strh.dwFlags, header.strh.dwPriority, \
                        header.strh.dwInitialFrames, header.strh.dwScale, header.strh.dwRate, header.strh.dwStart, header.strh.dwLength, header.strh.dwSuggestedBufferSize, \
                        header.strh.quality, header.strh.dwSampleSize, header.strh.rcFrame_bottom, header.strh.rcFrame_left, header.strh.rcFrame_right, header.strh.rcFrame_top, \
                        header.csh0.tagName, header.csh0.dataSize, header.csh0.headerVersion, header.csh0.numFramesInStream, header.csh0.numCustomStreamHeaders, header.csh0.numCustomFrameHeaders, \
                        header.csh0.numVectorsPerStreamFrame, header.rfam.tagName, header.rfam.dataSize, header.rfam.headerVersion, header.rfam.examIndex, header.rfam.probeName, header.rfam.probeRadiusCm, \
                        header.rfam.isTrigger10n, header.rfam.isTrigger20n, header.rfam.trigger1DelaySec, header.rfam.trigger2DelaySec, header.rfam.trigger1WaveCount, header.rfam.trigger2WaveCount, \
                        header.rfbm.tagName, header.rfbm.dataSize, header.rfbm.headerVersion, header.rfbm.numFocalZones, header.rfbm.acousticFrameRateHz, header.rfbm.numParallelAcquisitions, \
                        header.rfbm.fovShape, header.rfbm.apexLateralCm, header.rfbm.apexVerticalCm, header.rfbm.displayedLateralMin, header.rfbm.displayedLateralSpan, header.rfbm.displayedAxialMinCm, \
                        header.rfbm.displayedAxialSpanCm, header.rfbm.steeringAngleRad, header.rfbm.lineDensity, header.rfbm.phaseInvertMode, header.rfmm.tagName, header.rfmm.dataSize, header.rfmm.headerVersion, \
                        header.rfmm.fovShape, header.rfmm.displayedAxialMinCm, header.rfmm.displayedAxialSpanCm, header.rfmm.apexLateralCm, header.rfmm.apexVerticalCm,  header.rfmm.roiLateralMin, \
                        header.rfmm.steeringAngleRad, header.rfdo.tagName, header.rfdo.dataSize, header.rfdo.headerVersion, header.rfdo.fovShape, header.rfdo.gateStartCm, header.rfdo.gateSizeCm, \
                        header.rfdo.apexLateralCm, header.rfdo.apexVerticalCm, header.rfdo.roiLateralMin, header.rfdo.steeringAngleRad, header.rfdo.sampleVolumeWidth, header.rfdo.dopplerType, \
                        header.rfco.tagName, header.rfco.dataSize, header.rfco.headerVersion, header.rfco.acousticFrameRateHz, header.rfco.numParallelAcquisitions, header.rfco.fovShape, \
                        header.rfco.apexLateralCm, header.rfco.apexVerticalCm, header.rfco.displayedLateralMin, header.rfco.displayedLateralSpan, header.rfco.displayedAxialMinCm, header.rfco.displayedAxialSpanCm, \
                        header.rfco.steeringAngleRad, header.rfco.lineDensity, header.rfco.interleaveFactor, header.rfco.alternateInterleaveFactor, header.rfco.isFrameInterleaveEn, header.rfco.ensembleSize, \
                        len(header.rfsd), header.rfsd[0].tagName, header.rfsd[0].dataSize, header.rfsd[0].headerVersion, header.rfsd[0].isDynamicFocusEn, header.rfsd[0].rxFNum, header.rfsd[0].txFocusRangeCm, header.rfsd[0].isAperGrowthEn, \
                        header.rfsd[0].rxApodization, header.rfsd[0].txFocusRangeCm, header.rfsd[0].txFNum, header.rfsd[0].txFrequencyMhz, header.rfsd[0].numTxCycles, header.rfsd[0].txWaveformStyle, header.rfsd[0].prfHz, \
                        header.rfsd[0].txApodization, header.rfsd[0].pulseAmplitude, header.rfsd[0].analogGain, header.strf.tagName, header.strf.dataSize, header.strf.headerVersion, header.strf.samplingRate, \
                        header.strf.bitCountPerSample, header.strf.sampleMask, header.strf.vectorHeaderLengthBytes, header.strf.compression, len(header.frh0), header.frh0[0].tagName, header.frh0[0].dataSize, header.frh0[0].headerVersion, \
                        header.frh0[0].isTriggeredFrame]
                    
                    header = []
             


                    hi = True
                    for i in range(presetNum):
                        # curHeader = np.loadtxt(str("/Volumes/CREST Data/David_S_Data/Thyroid_Data_RFD/Preset_" + str(i+1) + "/header"))
                        curHeader = samplesAr[i]
                        if all(header[i] == curHeader[i] for i in range(len(curHeader))):
                            # os.rename(str("/Volumes/CREST Data/David_S_Data/Thyroid_Data_RFD/" + file), str("/Volumes/CREST Data/David_S_Data/Thyroid_Data_RFD/Preset_" + str(i+1) + "/" + file))
                            hi = False
                            break
                        else:
                            for j in range(len(curHeader)):
                                if header[j] != curHeader[j]:
                                    test = 0

                    if hi:
                        # os.mkdir(str("/Volumes/CREST Data/David_S_Data/Thyroid_Data_RFD/Preset_" + str(presetNum+1)))
                        # np.savetxt(str("/Volumes/CREST Data/David_S_Data/Thyroid_Data_RFD/Preset_" + str(presetNum+1) + "/header"), header)
                        samplesAr.append(header)
                        presetNum += 1

categorize()
