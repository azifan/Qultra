import matplotlib.pyplot as plt
import numpy as np
import pickle
from os.path import join, exists, isdir
from os import listdir
from scipy.optimize import curve_fit
import math
from scipy import interpolate

# Global vars
source_dir = "/Volumes/CREST Data/David_S_Data/MC_Sample_Code/outputs/pickle_outputs_withoutROImargin_fullFrameRate"
patients = sorted([x for x in listdir(source_dir) if isdir(join(source_dir, x))])


def load_pickle(pickle_path):
    with open(pickle_path, "rb") as f:
        data = pickle.load(f)
    # print(data.shape)
    return data


def interpolate_linear(array):
    x = np.arange(0, array.shape[1])
    y = np.arange(0, array.shape[0])
    # mask invalid values
    array = np.ma.masked_invalid(array)
    xx, yy = np.meshgrid(x, y)
    # get only the valid values
    x1 = xx[~array.mask]
    y1 = yy[~array.mask]
    newarr = array[~array.mask]

    inter = interpolate.griddata((x1, y1), newarr.ravel(), (xx, yy), method="linear")

    # print(inter.shape)

    return inter


def interpolate_nearest(array):
    x = np.arange(0, array.shape[1])
    y = np.arange(0, array.shape[0])
    # mask invalid values
    array = np.ma.masked_invalid(array)
    xx, yy = np.meshgrid(x, y)
    # get only the valid values
    x1 = xx[~array.mask]
    y1 = yy[~array.mask]
    newarr = array[~array.mask]

    inter = interpolate.griddata((x1, y1), newarr.ravel(), (xx, yy), method="nearest")

    return inter


def bolus_lognormal(x, auc, mu, sigma, t0):
    curve_fit = (auc / (2.5066 * sigma * (x - t0))) * np.exp(
        -1 * (((np.log(x - t0) - mu) ** 2) / (2 * sigma * sigma))
    )
    return np.nan_to_num(curve_fit)


def pixel_level_TIC_parameters(intensities, mode, available_frames=None):
    global patient_code_inj

    n_frames = intensities.shape[0]

    if mode == "ori":
        available_frames = np.arange(n_frames)
        available_intensities = intensities[:]
    elif mode == "MC":
        available_intensities = intensities[available_frames]

    TIC = np.concatenate(
        [available_frames[:, np.newaxis], available_intensities[:, np.newaxis]], axis=1
    )
    plt.cla()
    plt.plot(TIC[:, 0], TIC[:, 1])
    plt.show()

    try:
        # fit first round to find t0
        # popt, _ = curve_fit(bolus_lognormal, TIC[:,0], TIC[:,1], p0=(750.,7.5,1.5,100.),
        #                       bounds=([0., 0., 0., 0.], [np.inf, np.inf, np.inf, np.max(TIC[:,0])]),method='trf')
        popt, _ = curve_fit(
            bolus_lognormal,
            TIC[:, 0],
            TIC[:, 1],
            p0=(750.0, 7.5, 1.5, 100.0),
            bounds=([0.0, 0.0, 0.0, 0.0], [5000.0, 20.0, 5.0, np.max(TIC[:, 0])]),
            method="trf",
        )

        # special cases
        ##########################
        if patient_code_inj == "P_005_012_inj2":
            popt[3] = 277.0
        ##########################

        # trim x before t0, and fit again
        t0 = math.floor(popt[3])
        TIC = TIC[TIC[:, 0] >= t0]
        # popt, _ = curve_fit(bolus_lognormal, TIC[:,0], TIC[:,1], p0=(750.,7.5,1.5,100.),
        #                       bounds=([0., 0., 0., 0.], [np.inf, np.inf, np.inf, np.max(TIC[:,0])]),method='trf')
        popt, _ = curve_fit(
            bolus_lognormal,
            TIC[:, 0],
            TIC[:, 1],
            p0=(750.0, 7.5, 1.5, 100.0),
            bounds=([0.0, 0.0, 0.0, 0.0], [5000.0, 20.0, 5.0, np.max(TIC[:, 0])]),
            method="trf",
        )

        t0 = math.floor(popt[3])
        xs = np.arange(t0, n_frames)

        # construct TIC curve
        wholecurve = bolus_lognormal(xs, popt[0], popt[1], popt[2], popt[3])

        fitted_TIC = np.concatenate(
            [xs[:, np.newaxis], wholecurve[:, np.newaxis]], axis=1
        )
        plt.plot(fitted_TIC[:, 0], fitted_TIC[:, 1])

        ##################

        """
        compute the following (sort by index of the output numpy array):
        0: peak intensity
        1: peak time
        2: appearance time
        3: wash-in time
        4: wash-in rate
        """

        out = np.zeros(5)

        out[0] = fitted_TIC[:, 1].max()
        out[1] = fitted_TIC[fitted_TIC[:, 1].argmax(), 0]
        peak_10_percent = 0.1 * out[0]
        appearance_time = fitted_TIC[
            (np.argwhere(fitted_TIC[:, 1] >= peak_10_percent)).min(), 0
        ]
        out[2] = appearance_time
        out[3] = out[1] - out[2]
        out[4] = out[0] / out[1]

    except Exception:
        # print(e)
        # out = np.zeros(5)
        out = np.empty(5)
        out[:] = np.nan

    return out


if __name__ == "__main__":
    parametric_map_names = [
        "peak intensity",
        "peak time",
        "appearance time",
        "wash-in time",
        "wash-in rate",
    ]

    # for patient_code_inj in included_patients:
    for patient_code_inj in patients:
        print(patient_code_inj)
        if not exists(join(source_dir, patient_code_inj, "CE_MC_ROI.pkl")):
            print("Skip due to missing CE_MC_ROI file")
            continue
        if not exists(join(source_dir, patient_code_inj, "CE_ori_ROI.pkl")):
            print("Skip due to missing CE_ori_ROI file")
            continue
        if not exists(join(source_dir, patient_code_inj, "seg_masks.pkl")):
            print("Skip due to missing seg_masks file")
            continue

        # bmode_ori_ROI = load_pickle(join(source_dir, patient_code_inj, 'bmode_ori_ROI.pkl'))
        CE_ori_ROI = load_pickle(join(source_dir, patient_code_inj, "CE_ori_ROI.pkl"))
        # bmode_MC_ROI = load_pickle(join(source_dir, patient_code_inj, 'bmode_MC_ROI.pkl'))
        CE_MC_ROI = load_pickle(join(source_dir, patient_code_inj, "CE_MC_ROI.pkl"))
        seg_masks = load_pickle(join(source_dir, patient_code_inj, "seg_masks.pkl"))

        CE_ori_ROI = CE_ori_ROI / 255.0
        CE_MC_ROI = CE_MC_ROI / 255.0

        available_frames = np.argwhere(np.sum(CE_MC_ROI, axis=(1, 2)) > 0).flatten()

        # maps_ori = np.apply_along_axis(pixel_level_TIC_parameters,
        #                             0, #axis
        #                             CE_ori_ROI,
        #                             'ori')
        maps_MC = np.apply_along_axis(
            pixel_level_TIC_parameters,
            0,  # axis
            CE_MC_ROI,
            "MC",
            available_frames=available_frames,
        )

        for i, name in enumerate(parametric_map_names):
            print(name)

            # fix maps of peak intensity and wash-in rate
            try:
                if name == "peak intensity":
                    # peak intensity
                    # maps_ori[i] = np.clip(maps_ori[i], None, 1.0)
                    maps_MC[i] = np.clip(maps_MC[i], None, 1.0)
                    # wash-in rate
                    # maps_ori[4] = maps_ori[0] / maps_ori[1]
                    maps_MC[4] = maps_MC[0] / maps_MC[1]
            except Exception as e:
                print("failed to fix peak intensity and wash-in rate map")
                print(e)

            # original map
            try:
                plt.figure(figsize=(16, 5))
                # plt.imshow(np.concatenate([maps_ori[i],
                #                         np.ones_like(maps_ori[i]) * np.mean(maps_ori[i]),
                #                         maps_MC[i]],
                #                         axis=1),
                #         cmap='jet')
                plt.axis("off")
                plt.colorbar()
                plt.show()
                plt.clf()
            except Exception as e:
                print("failed to plot original map")
                print(e)

            # interpolated map
            # if np.sum(np.isnan(maps_ori[i]))>0 or np.sum(np.isnan(maps_MC[i]))>0:
            #     print('interpolated', name)
            #     try:
            #         plt.figure(figsize=(16,5))
            #         # plt.imshow(np.concatenate([interpolate_nearest(interpolate_linear(maps_ori[i])),
            #         #                         np.ones_like(maps_ori[i]) * np.mean(maps_ori[i]),
            #         #                         interpolate_nearest(interpolate_linear(maps_MC[i]))],
            #         #                         axis=1),
            #                 # cmap='jet')
            #         plt.axis('off')
            #         plt.colorbar()
            #         plt.show()
            #         plt.clf()
            #     except Exception as e:
            #         print('failed to plot interpolated map')
            #         print(e)

