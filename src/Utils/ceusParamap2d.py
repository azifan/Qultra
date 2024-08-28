import time
import numpy as np
from scipy.optimize import curve_fit
from sklearn.metrics import mean_squared_error
from math import exp
import os
import nibabel as nib
import cv2
from tqdm import tqdm

import warnings
warnings.filterwarnings("ignore", message="divide by zero encountered in divide")
warnings.filterwarnings("ignore", message="invalid value encountered in log")
warnings.filterwarnings("ignore", message="invalid value encountered in multiply")
warnings.filterwarnings("ignore", message="divide by zero encountered in log")
warnings.filterwarnings("ignore", message="invalid value encountered in divide")
warnings.filterwarnings("ignore", message="overflow encountered in divide")
warnings.filterwarnings("ignore", message="overflow encountered in exp")

def data_fit(TIC, normalizer, timeconst):
    #Fitting function
    #Returns the parameters scaled by normalizer
    #Beware - all fitting - minimization is done with data normalized 0 to 1.
    #kwargs = {"max_nfev":5000}
    popt, pcov = curve_fit(bolus_lognormal, TIC[:,0], TIC[:,1], p0=(1.0,3.0,0.5,0.1),bounds=([0., 0., 0., -1.], [np.inf, np.inf, np.inf, 10.]),method='trf')#p0=(1.0,3.0,0.5,0.1) ,**kwargs
    popt = np.around(popt, decimals=1);
    auc = popt[0]; rauc=normalizer*popt[0]; mu=popt[1]; sigma=popt[2]; t0=popt[3]; mtt=timeconst*np.exp(mu+sigma*sigma/2);
    tp = timeconst*exp(mu-sigma*sigma); wholecurve = bolus_lognormal(TIC[:,0], popt[0], popt[1], popt[2], popt[3]); pe = np.max(wholecurve); # took out pe normalization
    rt0 = t0;# + tp;

    # Get error parameters
    residuals = TIC[:,1] - bolus_lognormal(TIC[:,0], popt[0], mu, sigma, t0);
    ss_res = np.sum(residuals[~np.isnan(residuals)]**2);# Residual sum of squares
    ss_tot = np.sum((TIC[:,1]-np.mean(TIC[:,1]))**2);# Total sum of squares
    r_squared = 1 - (ss_res / ss_tot);# R squared
    RMSE = (np.sum(residuals[~np.isnan(residuals)]**2)/(residuals[~np.isnan(residuals)].size-2))**0.5;#print('RMSE 1');print(RMSE);# RMSE
    rMSE = mean_squared_error(TIC[:,1], bolus_lognormal(TIC[:,0], popt[0], mu, sigma, t0))**0.5;#print('RMSE 2');print(rMSE);

    # Filters to block any absurb numbers based on really bad fits.
    if tp > TIC[-1,0]: tp = TIC[-1,0]
    if mtt > TIC[-1,0]*2: mtt = TIC[-1,0]*2
    if rt0 > TIC[-1,0]: rt0 = TIC[-1,0]
    # if tp > 220: tp = 220; #pe = 0.1; rauc = 0.1; rt0 = 0.1; mtt = 0.1;
    # if rt0 > 160: rt0 = 160; #pe = 0.1; rauc = 0.1; tp = 0.1; mtt = 0.1;
    # if mtt > 2000: mtt = 2000; #pe = 0.1; rauc = 0.1; tp = 0.1; rt0 = 0.1;
    if pe > 2: pe = 2;
    if auc > 10*max(TIC[:,1]): auc = 2.5*max(TIC[:,1]);

    if RMSE > 0.3: raise RuntimeError

    params = np.array([auc, pe, tp, mtt, rt0]);

    return params, popt, RMSE;

def bolus_lognormal(x, auc, mu, sigma, t0):
   curve_fit=(auc/(2.5066*sigma*(x-t0)))*np.exp(-1*(((np.log(x-t0)-mu)**2)/(2*sigma*sigma)))
   return np.nan_to_num(curve_fit)

def generate_TIC_2d(window, mask, times, compression, voxelscale):
    TICtime=times;TIC=[]; 
    bool_mask = np.array(mask, dtype=bool)
    for t in range(0,window.shape[2]):
        tmpwin = window[:,:,t];      
        TIC.append(np.around(np.exp(tmpwin[bool_mask]/compression).mean()/voxelscale, decimals=1));
        # TIC.append(np.exp(tmpwin[bool_mask]/compression).mean()*voxelscale);
        # TIC.append(np.around((tmpwin[bool_mask]/compression).mean()*voxelscale, decimals=1)); 
    TICz = np.array([TICtime,TIC]).astype('float64'); TICz = TICz.transpose();
    TICz[:,1]=TICz[:,1]-np.mean(TICz[0:2,1]);#Substract noise in TIC before contrast.
    if TICz[np.nan_to_num(TICz)<0].any():#make the smallest number in the TIC 0.
        TICz[:,1]=TICz[:,1]+np.abs(np.min(TICz[:,1]));
    else:
        TICz[:,1]=TICz[:,1]-np.min(TICz[:,1]);
    return TICz;


def generate_TIC_2d_MC(window, mask, times, compression):
    TICtime = []
    TIC = []
    areas = []
    summed_window = np.transpose(np.sum(np.squeeze(window), axis=3))
    for t in range(0, mask.shape[2]):
        tmpwin = summed_window[t]
        bool_mask = np.array(mask[t]).astype(bool)
        numPoints = len(np.where(bool_mask > 0)[0])
        if numPoints == 0:
            continue
        TIC.append(np.exp(tmpwin[bool_mask] / compression).mean())
        TICtime.append(times[t])
        areas.append(numPoints)

    TICz = np.array([TICtime, TIC]).astype("float64")
    TICz = TICz.transpose()
    TICz[:, 1] = TICz[:, 1] - np.mean(
        TICz[0:2, 1]
    )  # Subtract noise in TIC before contrast
    if TICz[np.nan_to_num(TICz) < 0].any():  # make the smallest number in TIC 0
        TICz[:, 1] = TICz[:, 1] + np.abs(np.min(TICz[:, 1]))
    else:
        TICz[:, 1] = TICz[:, 1] - np.min(TICz[:, 1])
    return TICz

def get_bbox(x_coords: np.array, y_coords: np.array, windSize_x: int, windSize_y: int) -> np.array:
    x0 = np.min(x_coords)
    y0 = np.min(y_coords)
    w = np.max(x_coords)-x0
    h = np.max(y_coords)-y0

    pix_x0s = np.arange(x0, x0+w, windSize_x)[:-1]
    pix_y0s = np.arange(y0, y0+h, windSize_y)[:-1]
    pix_bboxes = np.transpose(np.meshgrid(pix_x0s, pix_y0s))
    pix_bboxes = np.pad(pix_bboxes, [(0,0), (0,0), (0,2)], mode='constant', constant_values=0)
    pix_bboxes[:,:,2] = windSize_x
    pix_bboxes[:,:,3] = windSize_y
    return pix_bboxes

def paramap2d(img, mask, res, time, tf, compressfactor, windSize_x, windSize_y, axOverlap, latOverlap, mc):
    # windSize_x = 1; windSize_y = 1; windSize_z = 1
    print('*************************** Starting Parameteric Map *****************************')
    # print('Prep For Loop:');print(str(datetime.now()));
    # start_time = datetime.now()
    #1a. Windowing and image info
    global windSize, voxelscale, compression, imgshape, timeconst, times, xlist, ylist, zlist, typefit;
    windSize = (windSize_x, windSize_y);
    voxelscale = res;
    compression = compressfactor; 
    imgshape = img.shape;
    typefit = tf;
    #img = img - np.mean(img[:,0:4,:,:,:,:],axis=1);img[img < 1]=0;

    # Make expected calculation time

    #1b. Creat time point and position lists
    timeconst = time;#time/(img.shape[1]+1);
    times = [i*time for i in range(1, img.shape[2]+1)];

    if mc:
        bbox_shape_x = 0
        bbox_shape_y = 0
        pixel_bboxes = []
        for t in range(mask.shape[2]):
            xmask, ymask = np.where(mask[:,:,t]>0)
            if len(xmask):
                pixel_bboxes.append(get_bbox(xmask, ymask, windSize_x, windSize_y))
                if not bbox_shape_x:
                    bbox_shape_x = pixel_bboxes[-1].shape[0]
                    bbox_shape_y = pixel_bboxes[-1].shape[1]
            else:
                pixel_bboxes.append(None)

        final_map = np.zeros((img.shape[0], img.shape[1], img.shape[2], 5))
        for x in range(bbox_shape_x):
            for y in range(bbox_shape_y):
                segMask = np.zeros((img.shape[2], img.shape[1], img.shape[0]))
                for t, bbox in enumerate(pixel_bboxes):
                    if bbox is not None:
                        x0, y0, x_len, y_len = bbox[x,y]
                        segMask[t, y0 : y0 + y_len, x0 : x0 + x_len] = 1

                cur_TIC = generate_TIC_2d_MC(img, segMask, times, compression)
                normalizer = np.max(cur_TIC[:,1]);
                cur_TIC[:,1] = cur_TIC[:,1]/normalizer;

                # Bunch of checks
                if np.isnan(np.sum(cur_TIC[:,1])):
                    print('STOPPED:NaNs in the VOI')
                    return;
                if np.isinf(np.sum(cur_TIC[:,1])):
                    print('STOPPED:InFs in the VOI')
                    return;

                # Do the fitting
                try:
                    params, popt, wholecurve = data_fit(cur_TIC,normalizer, timeconst);
                    index_points = np.transpose(np.where(np.transpose(segMask)>0))
                    final_map[index_points] = params
                except RuntimeError:
                    # params = np.array([-1, np.max(cur_TIC[:,1]), -1, -1])
                    pass
                
        print('Paraloop ended:')
        return final_map
    
    try:
        xmask, ymask, _ = np.where(mask>0)
        xlist = np.arange(min(xmask), max(xmask)+windSize_x, max(1,int(windSize_x*(1-(axOverlap/100)))))
        ylist = np.arange(min(ymask), max(ymask)+windSize_y, max(1,int(windSize_y*(1-(latOverlap/100)))))
    except:
        print("Voxel dimensions too small! Try larger values")
        return 1
    final_map = np.zeros([img.shape[0], img.shape[1], 5]).astype(np.double)
    summed_img = np.array(
            [
                cv2.cvtColor(img[i], cv2.COLOR_BGR2GRAY)
                for i in range(img.shape[0])
            ]
        )
    for x_base in tqdm(range(len(xlist))):
        for y_base in range(len(ylist)):
            cur_mask = np.zeros([img.shape[0], img.shape[1]])
            indices = []
            for x in range(windSize[0]):
                cur_index = []
                cur_index.append(xlist[x_base]+x)
                for y in range(windSize[1]):
                    cur_index.append(ylist[y_base]+y)
                    indices.append(cur_index.copy())
                    cur_index.pop()
                cur_index.pop()
            sig_indices = False
            for i in indices:
                if max(summed_img[i[0],i[1]]) != 0:
                    cur_mask[i[0],i[1]] = 1
                    sig_indices = True
            if not sig_indices:
                continue
            cur_TIC = generate_TIC_2d(summed_img, cur_mask, times, 24.9,  voxelscale)
            normalizer = np.max(cur_TIC[:,1]);
            if not normalizer:
                continue
            cur_TIC[:,1] = cur_TIC[:,1]/normalizer;

            # Bunch of checks
            if np.isnan(np.sum(cur_TIC[:,1])):
                print('STOPPED:NaNs in the VOI')
                return;
            if np.isinf(np.sum(cur_TIC[:,1])):
                print('STOPPED:InFs in the VOI')
                return;

            # Do the fitting
            try:
                params, popt, wholecurve = data_fit(cur_TIC,normalizer, timeconst);
                for i in indices:
                    final_map[i[0],i[1]] = params
            except RuntimeError:
                # params = np.array([-1, np.max(cur_TIC[:,1]), -1, -1])
                pass

    print('Paraloop ended:')#;print(str(datetime.now()));
    return final_map;

def get_paramap2d(image, mask, windowHeightValue, windowWidthValue, destinationPath, timeConst, res0, res1, axOverlap, latOverlap, mc):
    start = time.time()

    compressValue = 24.9 # hardcoded for now

    masterParamap = paramap2d(image, mask, res0*res1, timeConst, 'BolusLognormal', compressValue, int(windowHeightValue/res0), int(windowWidthValue/res1), axOverlap, latOverlap, mc)
    if type(masterParamap) == int:
        return 1

    affine = np.eye(4)
    niiarray = nib.Nifti1Image(masterParamap, affine, dtype=np.double)
    if os.path.exists(destinationPath):
        os.remove(destinationPath)
    nib.save(niiarray, destinationPath)
    print("Total time taken (sec):", time.time() - start)
    return 0
