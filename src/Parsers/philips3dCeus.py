import os
from pathlib import Path
import pickle

import numpy as np
import nibabel as nib

def formatTimeSeries(destFolder: str, dataName: str, bmode: bool) -> str:
    if bmode:
        print("Combining B-Mode volumes...")
    else:
        print("Combining CEUS volumes...")

    resFile = open(Path(destFolder) / Path("bmode_volume_dims.pkl"), mode='rb')
    orgres = pickle.load(resFile)
    resFile.close()
    
    frameNum = 0
    timeSeriesVols = []
    while True:
        try:
            if bmode:
                f = open(Path(destFolder) / Path(f"bmode_frame_{frameNum}.pkl"), mode='rb')
            else:
                f = open(Path(destFolder) / Path(f"ceus_frame_{frameNum}.pkl"), mode='rb')
        except FileNotFoundError:
            break
        timeSeriesVols.append(pickle.load(f))
        f.close()
        frameNum += 1
    
    dataNibImg = np.transpose(timeSeriesVols).astype(np.float16)
    clippedFact = 0.95; dynRange = 70
    clippedMax = clippedFact*np.amax(dataNibImg)
    dataNibImg = np.clip(dataNibImg, clippedMax - dynRange, clippedMax)
    dataNibImg -= np.amin(dataNibImg)
    dataNibImg *= 255/np.amax(dataNibImg)
    print(dataNibImg.shape)
    
    affine = np.eye(4)
    niiarray = nib.Nifti1Image(dataNibImg.astype('uint8'), affine)
    niiarray.header['pixdim'] = orgres
    if bmode:
        outputPath = os.path.join(destFolder, str(dataName+'_BMODE.nii.gz'))
    else:
        outputPath = os.path.join(destFolder, str(dataName+'_CEUS.nii.gz'))
    nib.save(niiarray, outputPath)

    return outputPath

def makeNifti(destFolder, dataName):
    print("Combining individual volumes...")
    return formatTimeSeries(destFolder, dataName, bmode=False), formatTimeSeries(destFolder, dataName, bmode=True)

if __name__ == "__main__":
    pathToData = "/Volumes/CREST Data/David_S_Data/David_Duncan 4D_SIP_to_SC_Volume/Data"
    file = "13.56.19_mf_sip_capture_50_2_1_0.raw"
    numberOfPlanes = 20
    # image4dCeusPostXbr(pathToData, file)
    makeNifti(str(pathToData + '/' + file), "hi")