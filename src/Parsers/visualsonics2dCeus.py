import os
from pathlib import Path
from dataclasses import dataclass
from typing import Any

import numpy as np
import xml.etree.ElementTree as ET
from tqdm import tqdm

@dataclass
class VisualSonicsInfo:
    filename: int = 0; uuid: int = 0; frames: int = 0; scanRange: int = 0
    satuOffset: int = 0; satuSize: int = 0; roiOffset: int = 0; roiSize: int = 0; scanlines: int = 0
    samples: int = 0; acqOffset: int = 0; acq: int = 0; acqSize: int = 0; lines: int = 0
    numberOfSlice: int = 0; volumeInfo: int = 0; focus: int = 0; sectorY: int = 0; sectorX: int = 0
    targetFov: int = 0; frameSize: int = 0; bmodeFocalZonePos1: int = 0; bmodeFocalZonePos2: int = 0
    bmodeFocalZonePos3: int = 0; defaultFov: int = 0; yRes: int = 0; xRes: int = 0; stepSize: int = 0
    scanDistance: int = 0; colorSize: int = 0; colorOffset: int = 0; imageSize: int = 0
    imageOffset: int = 0; studyMode: int = 0; acqMode: int = 0; file: int = 0; studyId: int = 0
    system: int = 0; rois: int = 0; bmodeNumSamples: int = 0; bmodeNumLines: int = 0
    bmodeDepthOffset: int = 0; bmodeDepth: int = 0; bmodeWidth: int = 0; bmodeRxFrequency: int = 0
    bmodeTxFrequency: int = 0; bmodeQuad2x: int = 0; bmodeNumFocalZones: int = 1; acqs: int = 0
    powerNumLines: int = 0; bmodeDepthAxis: int = 0; bmodeWidthAxis: int = 0; bmodeDynRange: int = 0; 
    bmodeYOffset: int = 0; bmodeVOffset: int = 0; powerCentre: int = 0; powerNumSamples: int = 0; 
    powerDepthOffset: int = 0; powerDepth: int = 0; powerWidth: int = 0; powerDepthAxis: int = 0; 
    powerWidthAxis: int = 0; ensembleN: int = 0; width: int = 0; height: int = 0; focalZone: int = 0; 
    bmodeRxGain: int = 0; bmodeTxPower: int = 0; prf: int = 0; transducerNm: int = 0; studyNm: int = 0; 
    acqDate: int = 0; acqTime: int = 0; analysisParams: Any = None; displayParams: Any = None; 
    windowParams: Any = None; contrastCentre: float = 0; contrastNumSamples: int = 0; contrastNumLines: int = 0
    contrastDepthOffset: float = 0; contrastDepth: float = 0; contrastWidth: float = 0; 
    contrastDepthAxis: Any = None; contrastWidthAxis: Any = None
    
keyParamPairs = {
    'studyMode': 'Mode-Name', 'bmodeNumSamples': 'B-Mode/Samples', 'bmodeNumLines': 'B-Mode/Lines',
    'bmodeDepthOffset': 'B-Mode/Depth-Offset', 'bmodeDepth': 'B-Mode/Depth', 'bmodeWidth': 'B-Mode/Width',
    'bmodeRxFrequency': 'B-Mode/RX-Frequency', 'bmodeTxFrequency': 'B-Mode/TX-Frequency',
    'bmodeQuad2x': 'B-Mode/Quad-2X', 'bmodeNumFocalZones': 'B-Mode/Focal-Zones-Count', 'scanDistance': '3D-Scan-Distance',
    'stepSize': '3D-Step-Size', 'contrastNumSamples': 'Nonlinear-Contrast-Mode/Samples',
    'contrastNumLines': 'Nonlinear-Contrast-Mode/Lines', 'contrastDepthOffset': 'Nonlinear-Contrast-Mode/Depth-Offset',
    'contrastDepth': 'Nonlinear-Contrast-Mode/Depth', 'contrastWidth': 'Nonlinear-Contrast-Mode/Width',
    'contrastCentre': 'Nonlinear-Contrast-Mode/Centre', 'bmodeRxGain': 'B-Mode/RX-Gain',
    'bmodeTxPower': 'B-Mode/TX-Power', 'transducerNm': 'Transducer-Name',
    'studyNm': 'Study-Name', 'acqDate': 'Acquired-Date', 'acqTime': 'Acquired-Time', 'system': 'Onc/Type'
}

def parse_xml(filepath: Path) -> ET.Element:
    tree = ET.parse(filepath)
    root = tree.getroot()
    return root

def readInfo(filepath: Path) -> VisualSonicsInfo:
    info = VisualSonicsInfo()
    studyID = filepath.stem
    studyEXT = filepath.suffix
    assert studyEXT == '.xml', f"Expected .xml file, got {studyEXT}"
    
    xRoot = parse_xml(filepath)
    info.studyId = studyID
    
    for attr, xmlKey in keyParamPairs.items():
        element = xRoot.find(f".//*[@name='{xmlKey}']")
        if element is not None and 'value' in element.attrib:
            value = element.attrib['value']
            
            # Convert value based on expected type
            if 'NumSamples' in attr or 'NumLines' in attr or 'Quad2x' in attr or 'NumFocalZones' in attr:
                setattr(info, attr, int(value))
            elif 'Depth' in attr or 'Width' in attr or 'Frequency' in attr or 'Gain' in attr or 'Power' in attr or 'stepSize' in attr or 'scanDistance' in attr or 'Centre' in attr:
                setattr(info, attr, float(value))
            else:
                setattr(info, attr, value)

    info.bmodeDepthAxis = np.linspace(info.bmodeDepthOffset, info.bmodeDepth, info.bmodeNumSamples).tolist()
    info.bmodeWidthAxis = np.linspace(0, info.bmodeWidth, info.bmodeNumLines).tolist()
    info.contrastDepthAxis = np.linspace(info.contrastDepthOffset, info.contrastDepth, info.contrastNumSamples).tolist()
    info.contrastWidthAxis = np.linspace(0, info.contrastWidth, info.contrastNumLines).tolist()
    info.yRes = info.bmodeDepth / info.bmodeNumSamples
    info.xRes = info.bmodeWidth / info.bmodeNumLines
    info.height = info.bmodeDepth - info.bmodeDepthOffset
    info.width = info.bmodeWidth
    info.frameSize = info.xRes * info.yRes
    info.targetFov = info.bmodeDepth    
    
    return info

def readImg(info: VisualSonicsInfo, filepath: Path) -> np.ndarray:
    """
    Reads an .rdb or .raw file (VisualSonics; vevo770 or vevo2100) and outputs cine loops of 
    the bmode image and power Doppler color (modeIm). Assumes VEVO 2100
    system with scan taken using Advanced Contrast Mode.
    
    Args:
        info (VisualSonicsInfo): VisualSonicsInfo object
    """
    # Process contrast mode
    fname = filepath.parent / f'{info.studyId}.3d.contrast'
    contrastNumSamples = info.contrastNumSamples
    contrastNumLines = info.contrastNumLines
    
    fileHeader = 40     # bytes
    frameHeader = 72    # bytes
    sz = 2
    
    fileSize = os.path.getsize(fname)
    bytesPerFrame = (sz * contrastNumSamples * contrastNumLines + frameHeader)
    numOfFrames = (fileSize - fileHeader) // bytesPerFrame
    
    rawData = np.zeros((numOfFrames, contrastNumSamples, contrastNumLines))
    
    with open(fname, 'rb') as fid:
        for frame in tqdm(range(numOfFrames)):
            header = fileHeader + frameHeader * (frame+1) + (sz * contrastNumSamples * contrastNumLines) * frame
            for i in range(contrastNumLines):
                fid.seek(header + (sz * contrastNumSamples) * i, 0)
                rawData[frame, :, i] = np.fromfile(fid, dtype=np.uint16, count=contrastNumSamples)
    
    rawData *= (256 / 100)
    modeIm = np.log(np.abs(rawData))
    modeIm[np.isinf(modeIm)] = 0
    
    # Process B-mode
    fname = filepath.parent / f'{info.studyId}.3d.bmode'
    bmodeNumSamples = info.bmodeNumSamples // 2
    bmodeNumLines = info.bmodeNumLines
    
    fileSize = os.path.getsize(fname)
    sz = 1
    frameHeader = 56 # bytes
    bytesPerFrame = (sz * bmodeNumSamples * bmodeNumLines + frameHeader)
    numOfFrames = (fileSize - fileHeader) // bytesPerFrame
    
    bmode = np.zeros((numOfFrames, bmodeNumSamples, bmodeNumLines))
    
    with open(fname, 'rb') as fid:
        for frame in tqdm(range(numOfFrames)):
            header = fileHeader + frameHeader * (frame+1) + (sz * bmodeNumSamples * bmodeNumLines) * frame
            for i in range(bmodeNumLines):
                fid.seek(header + (sz * bmodeNumSamples) * i, 0)
                bmode[frame, :, i] = np.fromfile(fid, dtype=np.uint8, count=bmodeNumSamples)
    
    bmode *= (256 / 100)
    bmode[np.isinf(bmode)] = 0
        
    return bmode, modeIm

def visualsonics2dCeusParser(filepath: Path) -> np.ndarray:
    info = readInfo(filepath)
    bmode, modeIm = readImg(info, filepath)
    return bmode, modeIm, info