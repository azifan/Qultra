import os
from pathlib import Path
import pickle

import numpy as np
import nibabel as nib
from tqdm import tqdm

def formatTimeSeries(destFolder: str, dataName: str, bmode: bool) -> str:
    if bmode:
        print("Combining B-Mode volumes...")
    else:
        print("Combining CEUS volumes...")

    resFile = open(Path(destFolder) / Path("bmode_volume_dims.pkl"), mode='rb')
    orgres = pickle.load(resFile)
    resFile.close()
    
    numFrames = 0
    for file in Path(destFolder).iterdir():
        if file.name.startswith("bmode_frame") and file.name.endswith(".pkl"):
            numFrames += 1
    
    timeSeriesVols = []
    for frameNum in tqdm(range(numFrames)):
        if bmode:
            f = open(Path(destFolder) / Path(f"bmode_frame_{frameNum}.pkl"), mode='rb')
        else:
            f = open(Path(destFolder) / Path(f"ceus_frame_{frameNum}.pkl"), mode='rb')
        timeSeriesVols.append(pickle.load(f))
        f.close()
    
    dataNibImg = np.transpose(timeSeriesVols).astype(np.float32)
    dataNibImg = np.clip(dataNibImg, a_min=0, a_max=255).astype(np.uint8)
    
    affine = np.eye(4)
    niiarray = nib.Nifti1Image(dataNibImg, affine)
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
    destFolder = Path('/Volumes/CREST Data/David_S_Data/Cori_Data/TJU-001/TJU-P01-V2-CEUS_12.32.11')
    dataName = 'TJU-P01-V2-CEUS_12.32.11_mf_sip_capture_50_2_1_0.raw'
    makeNifti(destFolder, dataName)
    