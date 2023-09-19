from CeusMcTool2d.roiSelection_ui import *
from CeusMcTool2d.ticAnalysis_ui_helper import *
from CeusMcTool2d.saveRoi_ui_helper import *


import nibabel as nib
import numpy as np
from scipy.ndimage import binary_fill_holes

from itertools import chain
import os
import scipy.interpolate as interpolate
import numpy as np
import nibabel as nib
from scipy.spatial import ConvexHull
import pyvista as pv
import Utils.motionCorrection as mc
import cv2
import pydicom as dicom

from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPixmap, QPainter, QImage
from PyQt5.QtCore import QLine, Qt

import platform
system = platform.system()


class RoiSelectionGUI(Ui_constructRoi, QWidget):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        if system == 'Windows':
            self.imageSelectionLabelSidebar.setStyleSheet("""QLabel {
                font-size: 18px;
                color: rgb(255, 255, 255);
                background-color: rgba(255, 255, 255, 0);
                border: 0px;
                font-weight: bold;
            }""")
            self.imageLabel.setStyleSheet("""QLabel {
                font-size: 13px;
                color: rgb(255, 255, 255);
                background-color: rgba(255, 255, 255, 0);
                border: 0px;
                font-weight: bold;
            }""")
            self.imagePathInput.setStyleSheet("""QLabel {
                font-size: 11px;
                color: rgb(255, 255, 255);
                background-color: rgba(255, 255, 255, 0);
                border: 0px;
            }""")
            self.roiSidebarLabel.setStyleSheet("""QLabel {
                font-size: 18px;
                color: rgb(255, 255, 255);
                background-color: rgba(255, 255, 255, 0);
                border: 0px;
                font-weight: bold;
            }""")
            self.analysisParamsLabel.setStyleSheet("""QLabel {
                font-size: 18px;
                color: rgb(255, 255, 255);
                background-color: rgba(255, 255, 255, 0);
                border: 0px;
                font-weight:bold;
            }""")
            self.ticAnalysisLabel.setStyleSheet("""QLabel {
                font-size: 18px;
                color: rgb(255, 255, 255);
                background-color: rgba(255, 255, 255, 0);
                border: 0px;
                font-weight: bold;
            }""")
            self.rfAnalysisLabel.setStyleSheet("""QLabel {
                font-size: 18px;
                color: rgb(255, 255, 255);
                background-color: rgba(255, 255, 255, 0);
                border: 0px;
                font-weight: bold;
            }""")

        self.acceptGeneratedRoiButton.setHidden(True)
        self.undoRoiButton.setHidden(True)
        self.roiFitNoteLabel.setHidden(True)
        self.drawRoiButton.setHidden(True)
        self.undoLastPtButton.setHidden(True)
        self.redrawRoiButton.setHidden(True)
        self.fitToRoiButton.setHidden(True)
        self.roiFitNoteLabel.setHidden(True)
        self.closeRoiButton.setHidden(True)
        self.preLoadedRoiButton.setHidden(True)
        self.chooseRoiButton.setHidden(True)
        self.backFromLoadButton.setHidden(True)
        self.saveRoiButton.setHidden(True)
        self.df = None
        self.dataFrame = None
        self.niftiSegPath = None

        self.curFrameIndex= 0
        self.curAlpha = 255
        self.curPointsPlottedX = []
        self.curPointsPlottedY = []
        self.pointsPlotted = []
        self.xCur = 0
        self.yCur = 0
        self.lastGui = None
        self.spline = None
        self.oldSpline = []
        self.mcResultsArray = []
        self.ticAnalysisGui = TicAnalysisGUI()
        self.saveRoiGUI = SaveRoiGUI()
        self.index = None
        self.bboxes = None
        self.ref_frames = None
        self.xcelIndices = None

        self.bmodeCoverPixmap = QPixmap(381, 351)
        self.bmodeCoverPixmap.fill(Qt.transparent)
        self.bmodeCoverLabel.setPixmap(self.bmodeCoverPixmap)

        self.ceCoverPixmap = QPixmap(381, 351)
        self.ceCoverPixmap.fill(Qt.transparent)
        self.ceCoverLabel.setPixmap(self.ceCoverPixmap)

        self.setMouseTracking(True)

        self.backButton.clicked.connect(self.backToLastScreen)
        self.newRoiButton.clicked.connect(self.drawNewRoi)
        self.loadRoiButton.clicked.connect(self.startLoadRoi)
        self.saveRoiButton.clicked.connect(self.startSaveRoi)

    def startSaveRoi(self):
        self.saveRoiGUI.roiSelectionGUI = self
        self.saveRoiGUI.show()

    def saveRoi(self, fileDestination, name, frame):
        segMask = np.zeros([self.numSlices, self.y, self.x])
        self.pointsPlotted = [*set(self.pointsPlotted)]
        for point in self.pointsPlotted:
            segMask[frame, point[0]+self.y0_bmode, point[1]+self.x0_bmode] = 1
        segMask = binary_fill_holes(segMask)

        affine = np.eye(4)
        niiarray = nib.Nifti1Image(np.transpose(segMask).astype('uint8'), affine)
        niiarray.header['descrip'] = self.imagePathInput.text()
        outputPath = os.path.join(fileDestination, name)
        nib.save(niiarray, outputPath)

    def startLoadRoi(self):
        self.newRoiButton.setHidden(True)
        self.loadRoiButton.setHidden(True)
        self.preLoadedRoiButton.setHidden(False)
        self.chooseRoiButton.setHidden(False)
        self.backFromLoadButton.setHidden(False)

        self.backFromLoadButton.clicked.connect(self.restartRoi)
        self.preLoadedRoiButton.clicked.connect(self.loadPreloadedRoi)
        self.chooseRoiButton.clicked.connect(self.loadChosenRoi)

    def loadChosenRoi(self):
        fileName, _ = QFileDialog.getOpenFileName(None, 'Open File', filter = '*.nii.gz')
        if fileName != '':
            nibIm = nib.load(fileName)
            if self.imagePathInput.text().replace("'", '"') == str(nibIm.header['descrip'])[2:-1]:
                self.loadRoi(nibIm.get_fdata().astype(np.uint8))

    def loadPreloadedRoi(self):  
        try:      
            self.niftiSegPath = self.df.loc[self.index, 'nifti_segmentation_path']
        except:
            return
        mask = nib.load(os.path.join(self.xcel_dir, self.niftiSegPath), mmap=False).get_fdata().astype(np.uint8)
        self.loadRoi(mask)
        
    def loadRoi(self, mask):
        mask = np.transpose(mask)
        maskPoints = np.where(mask > 0)
        maskPoints = np.transpose(maskPoints)
        # self.maskCoverImg[maskPoints] = [0,0,255,255]
        for point in maskPoints:
            self.maskCoverImg[point[1], point[2]] = [0,0,255,255]
            self.pointsPlotted.append((point[1], point[2]))
        self.curFrameIndex = maskPoints[0,0]
        self.curSliceSlider.setValue(self.curFrameIndex)
        self.curSecondLabel.setText(str(self.sliceArray[self.curFrameIndex]))
        self.curSliceSpinBox.setValue(self.curFrameIndex)
        self.perform_MC()

        self.backFromLoadButton.setHidden(True)
        self.preLoadedRoiButton.setHidden(True)
        self.chooseRoiButton.setHidden(True)
        self.undoRoiButton.setHidden(False)
        self.acceptGeneratedRoiButton.setHidden(False)

    def drawNewRoi(self):
        self.newRoiButton.setHidden(True)
        self.loadRoiButton.setHidden(True)
        self.undoLastPtButton.setHidden(True)
        self.saveRoiButton.setHidden(True)
        self.drawRoiButton.setHidden(False)
        self.undoLastPtButton.setHidden(False)
        self.redrawRoiButton.setHidden(False)
        self.fitToRoiButton.setHidden(False)
        self.closeRoiButton.setHidden(False)
        self.saveRoiButton.setHidden(True)

    def backToLastScreen(self):
        self.lastGui.dataFrame = self.dataFrame
        self.lastGui.show()
        self.hide()


    def setFilenameDisplays(self, imageName):
        self.imagePathInput.setHidden(False)
        
        imFile = imageName.split('/')[-1]

        self.imagePathInput.setText(imFile)
        self.inputTextPath = imageName

    def perform_MC(self):
        # Credit Thodsawit Tiyarattanachai, MD. See Utils/motionCorrection.py for full citation
        self.segMask = np.zeros([self.numSlices, self.y, self.x])
        self.pointsPlotted = [*set(self.pointsPlotted)]
        for point in self.pointsPlotted:
            self.segMask[self.curFrameIndex,point[0]+self.y0_bmode, point[1]+self.x0_bmode] = 1
        self.segMask[self.curFrameIndex] = binary_fill_holes(self.segMask[self.curFrameIndex])
        

        set_quantile = 0.50
        step = 1 # fullFrameRate. step=2 for halfFrameRate
        threshold_decrease_per_step = 0.02

        # get ref frame
        search_margin = int((0.5/15)*self.fullArray.shape[1])
        ref_frames = [self.curFrameIndex]
        mask = self.segMask[self.curFrameIndex]
        pos_coor = np.argwhere(mask > 0)
        x_values = pos_coor[:,1]
        y_values = pos_coor[:,0]
        x0 = x_values.min()
        x1 = x_values.max()
        w = x1 - x0 +1
        y0 = y_values.min()
        y1 = y_values.max()
        h = y1 - y0 + 1
        bboxes = [(x0, y0, w, h)]
        masks = [mask]

        ###################################################
        # find initial correlation in the first run
        min_x0 = min([e[0] for e in bboxes]) - search_margin
        max_x1 = max([e[0]+e[2] for e in bboxes]) + search_margin
        min_y0 = min([e[1] for e in bboxes]) - search_margin
        max_y1 = max([e[1]+e[3] for e in bboxes])
        bmode = self.fullArray[:, min_y0:max_y1, min_x0:max_x1]
        ref_f = ref_frames[0]
        ref_b = bboxes[0]
        ref_bmodes = [self.fullArray[ref_f, \
                                      ref_b[1]:ref_b[1]+ref_b[3], \
                                      ref_b[0]:ref_b[0]+ref_b[2]]]
        
        corr_initial_run, threshold = mc.find_correlation(bmode, ref_bmodes, set_quantile)
        ###################################################

        ref_patches = ref_bmodes[:]

        previous_all_lesion_bboxes = [None]*self.fullArray.shape[0]
        iteration = 1

        while True:

            out_array = np.zeros(list(self.fullArray.shape) + [3], dtype=np.uint8)

            all_search_bboxes = [None]*self.fullArray.shape[0]
            all_lesion_bboxes = [None]*self.fullArray.shape[0]
            corr_with_ref = [None]*self.fullArray.shape[0]

            for ref_idx in range(len(ref_frames)):
                ref_frame = ref_frames[ref_idx]
                ref_bbox = bboxes[ref_idx]

                if ref_idx == 0:
                    if ref_idx == len(ref_frames) - 1:
                        #There is only 1 ref_frame
                        ref_begin = 0
                        ref_end = self.fullArray.shape[0]
                    else:
                        #This is the first ref_frame. There are >1 ref frames.
                        ref_begin = 0
                        ref_end = int((ref_frames[ref_idx]+ref_frames[ref_idx+1])/2)
                else:
                    if ref_idx == len(ref_frames) - 1:
                        #This is the last ref frame. There are >1 ref frames.
                        ref_begin = int((ref_frames[ref_idx-1]+ref_frames[ref_idx])/2)
                        ref_end = self.fullArray.shape[0]
                    else:
                        #These are ref frames in the middle. There are >1 ref frames.
                        ref_begin = int((ref_frames[ref_idx-1]+ref_frames[ref_idx])/2)
                        ref_end = int((ref_frames[ref_idx]+ref_frames[ref_idx+1])/2)

                #######################

                #forward tracking
                ##############################################################
                if ref_frame < ref_end-1:  #can forward track only if there are frames after the ref_frame
                    #print('forward tracking')

                    previous_bbox = ref_bbox

                    valid = True

                    for frame in range(ref_frame, ref_end, step):

                        full_frame = self.fullArray[frame]

                        if valid:
                            search_w = int(previous_bbox[2]+(2*search_margin))
                            search_h = int(previous_bbox[3]+(2*search_margin))
                            search_x0 = int(previous_bbox[0] - ((search_w - previous_bbox[2])/2))
                            search_y0 = int(previous_bbox[1] - ((search_h - previous_bbox[3])/2))
                            search_bbox = (search_x0, search_y0, search_w, search_h)
                            search_region = full_frame[search_y0:search_y0+search_h,
                                                    search_x0:search_x0+search_w]

                            all_search_bboxes[frame] = search_bbox

                        else:

                            all_search_x0 = [b[0] for b in all_search_bboxes[ref_frame+1:ref_end] if not(b is None)]
                            median_x0 = np.median(all_search_x0)
                            IQR_x0 = np.quantile(all_search_x0, 0.75) - np.quantile(all_search_x0, 0.25)
                            all_search_x0 = [x for x in all_search_x0 if (x>=median_x0-(1.5*IQR_x0)) and (x<=median_x0+(1.5*IQR_x0))]
                            min_search_x0 = min(all_search_x0)
                            max_search_x0 = max(all_search_x0)

                            all_search_y0 = [b[1] for b in all_search_bboxes[ref_frame+1:ref_end] if not(b is None)]
                            median_y0 = np.median(all_search_y0)
                            IQR_y0 = np.quantile(all_search_y0, 0.75) - np.quantile(all_search_y0, 0.25)
                            all_search_y0 = [y for y in all_search_y0 if (y>=median_y0-(1.5*IQR_y0)) and (y<=median_y0+(1.5*IQR_y0))]
                            min_search_y0 = min(all_search_y0)
                            max_search_y0 = max(all_search_y0)

                            search_x0 = min_search_x0
                            search_y0 = min_search_y0
                            search_w = (max_search_x0-min_search_x0) + int(ref_bbox[2]+(2*search_margin))
                            search_h = (max_search_y0-min_search_y0) + int(previous_bbox[3]+(2*search_margin))
                            search_bbox = (search_x0, search_y0, search_w, search_h)
                            search_region = full_frame[search_y0:search_y0+search_h,
                                                        search_x0:search_x0+search_w]    

                            
                        mean_corr, max_loc = mc.compute_similarity_map(search_region, ref_patches, ref_idx)
                        corr_with_ref[frame] = mean_corr
                        

                        if mean_corr >= threshold:
                            valid = True
                            current_w = ref_bbox[2]
                            current_h = ref_bbox[3]
                            current_x0 = search_x0 + max_loc[0]
                            current_y0 = search_y0 + max_loc[1]
                            current_bbox = (current_x0, current_y0, current_w, current_h)

                            img_bbox = cv2.rectangle(cv2.cvtColor(full_frame, cv2.COLOR_GRAY2BGR),
                                                        (search_x0, search_y0),
                                                        (search_x0+search_w, search_y0+search_h),
                                                        (255, 255, 255), 2)
                            img_bbox = cv2.rectangle(img_bbox,
                                                        (current_bbox[0], current_bbox[1]),
                                                        (current_bbox[0] + current_bbox[2], current_bbox[1] + current_bbox[3]),
                                                        (0, 255, 0), 2)
                            # img_bbox = cv2.putText(img_bbox, 'frame: '+str(frame), (25,25), cv2.FONT_HERSHEY_SIMPLEX,  
                            #             1, (0,255,0), 2, cv2.LINE_AA) 
                            # img_bbox = cv2.putText(img_bbox, 'corr: '+str(mean_corr), (25,50), cv2.FONT_HERSHEY_SIMPLEX,  
                            #             1, (0,255,0), 2, cv2.LINE_AA) 

                            out_array[frame] = img_bbox

                            #####################################
                            all_lesion_bboxes[frame] = current_bbox[:]
                            previous_bbox = current_bbox[:]
                            

                        else:
                            valid = False
                            img_bbox = cv2.rectangle(cv2.cvtColor(full_frame, cv2.COLOR_GRAY2BGR),
                                                        (search_x0, search_y0),
                                                        (search_x0+search_w, search_y0+search_h),
                                                        (255, 0, 0), 2)
                            # img_bbox = cv2.putText(img_bbox, 'frame: '+str(frame), (25,25), cv2.FONT_HERSHEY_SIMPLEX,  
                            #             1, (255,0,0), 2, cv2.LINE_AA) 
                            # img_bbox = cv2.putText(img_bbox, 'corr: '+str(mean_corr), (25,50), cv2.FONT_HERSHEY_SIMPLEX,  
                            #             1, (255,0,0), 2, cv2.LINE_AA) 

                            out_array[frame] = img_bbox
                    #########################################################
                    
                    
                    #backward tracking
                    ##############################################################
                    if ref_frame > ref_begin:  
                        #print('backward tracking')

                        previous_bbox = ref_bbox

                        valid = True

                        for frame in range(ref_frame-1, ref_begin-1, -step):

                            full_frame = self.fullArray[frame]

                            if valid:
                                search_w = int(previous_bbox[2]+(2*search_margin))
                                search_h = int(previous_bbox[3]+(2*search_margin))
                                search_x0 = int(previous_bbox[0] - ((search_w - previous_bbox[2])/2))
                                search_y0 = int(previous_bbox[1] - ((search_h - previous_bbox[3])/2))
                                search_bbox = (search_x0, search_y0, search_w, search_h)
                                search_region = full_frame[search_y0:search_y0+search_h,
                                                        search_x0:search_x0+search_w]

                                all_search_bboxes[frame] = search_bbox

                            else:

                                all_search_x0 = [b[0] for b in all_search_bboxes[ref_begin:ref_frame] if not(b is None)]
                                median_x0 = np.median(all_search_x0)
                                IQR_x0 = np.quantile(all_search_x0, 0.75) - np.quantile(all_search_x0, 0.25)
                                all_search_x0 = [x for x in all_search_x0 if (x>=median_x0-(1.5*IQR_x0)) and (x<=median_x0+(1.5*IQR_x0))]
                                min_search_x0 = min(all_search_x0)
                                max_search_x0 = max(all_search_x0)

                                all_search_y0 = [b[1] for b in all_search_bboxes[ref_begin:ref_frame] if not(b is None)]
                                median_y0 = np.median(all_search_y0)
                                IQR_y0 = np.quantile(all_search_y0, 0.75) - np.quantile(all_search_y0, 0.25)
                                all_search_y0 = [y for y in all_search_y0 if (y>=median_y0-(1.5*IQR_y0)) and (y<=median_y0+(1.5*IQR_y0))]
                                min_search_y0 = min(all_search_y0)
                                max_search_y0 = max(all_search_y0)

                                search_x0 = min_search_x0
                                search_y0 = min_search_y0
                                search_w = (max_search_x0-min_search_x0) + int(ref_bbox[2]+(2*search_margin))
                                search_h = (max_search_y0-min_search_y0) + int(previous_bbox[3]+(2*search_margin))
                                search_bbox = (search_x0, search_y0, search_w, search_h)
                                search_region = full_frame[search_y0:search_y0+search_h,
                                                            search_x0:search_x0+search_w]    

                                
                            mean_corr, max_loc = mc.compute_similarity_map(search_region, ref_patches, ref_idx)
                            corr_with_ref[frame] = mean_corr
                            

                            if mean_corr >= threshold:
                                valid = True
                                current_w = ref_bbox[2]
                                current_h = ref_bbox[3]
                                current_x0 = search_x0 + max_loc[0]
                                current_y0 = search_y0 + max_loc[1]
                                current_bbox = (current_x0, current_y0, current_w, current_h)

                                img_bbox = cv2.rectangle(cv2.cvtColor(full_frame, cv2.COLOR_GRAY2BGR),
                                                            (search_x0, search_y0),
                                                            (search_x0+search_w, search_y0+search_h),
                                                            (255, 255, 255), 2)
                                img_bbox = cv2.rectangle(img_bbox,
                                                            (current_bbox[0], current_bbox[1]),
                                                            (current_bbox[0] + current_bbox[2], current_bbox[1] + current_bbox[3]),
                                                            (0, 255, 0), 2)
                                # img_bbox = cv2.putText(img_bbox, 'frame: '+str(frame), (25,25), cv2.FONT_HERSHEY_SIMPLEX,  
                                #             1, (0,255,0), 2, cv2.LINE_AA) 
                                # img_bbox = cv2.putText(img_bbox, 'corr: '+str(mean_corr), (25,50), cv2.FONT_HERSHEY_SIMPLEX,  
                                #             1, (0,255,0), 2, cv2.LINE_AA) 

                                out_array[frame] = img_bbox

                                #####################################
                                all_lesion_bboxes[frame] = current_bbox[:]
                                previous_bbox = current_bbox[:]
                                

                            else:
                                valid = False
                                img_bbox = cv2.rectangle(cv2.cvtColor(full_frame, cv2.COLOR_GRAY2BGR),
                                                            (search_x0, search_y0),
                                                            (search_x0+search_w, search_y0+search_h),
                                                            (255, 0, 0), 2)
                                # img_bbox = cv2.putText(img_bbox, 'frame: '+str(frame), (25,25), cv2.FONT_HERSHEY_SIMPLEX,  
                                #             1, (255,0,0), 2, cv2.LINE_AA) 
                                # img_bbox = cv2.putText(img_bbox, 'corr: '+str(mean_corr), (25,50), cv2.FONT_HERSHEY_SIMPLEX,  
                                #             1, (255,0,0), 2, cv2.LINE_AA) 

                                out_array[frame] = img_bbox
                    #########################################################
                    

            #check if lesion bbox in any frame move in this iteration
            #####################
            bbox_move = mc.check_bbox_move(previous_all_lesion_bboxes, all_lesion_bboxes)
            if bbox_move or (threshold < min([e for e in corr_with_ref if not(e is None)])):
                break
            #####################

            previous_all_lesion_bboxes = all_lesion_bboxes[:]
            previous_out_array = out_array.copy()
            threshold -= threshold_decrease_per_step
            iteration += 1

        self.mcResultsArray = previous_out_array
        self.mcResultsBmode = self.mcResultsArray[:, \
                                                  self.y0_bmode:self.y0_bmode+self.y,\
                                                  self.x0_bmode:self.x0_bmode+self.x]
        self.mcResultsCE = self.mcResultsArray[:, \
                                               self.y0_CE:self.y0_CE+self.y, \
                                               self.x0_CE:self.x0_CE+self.x]
        
        self.bboxes = previous_all_lesion_bboxes
        self.ref_frames = ref_frames

        self.updateBmode()
        self.updateCE()
        self.acceptGeneratedRoiButton.setHidden(False)
        self.drawRoiButton.setHidden(True)
        self.undoRoiButton.setHidden(False)
        self.undoLastPtButton.setHidden(True)
        self.redrawRoiButton.setHidden(True)
        self.fitToRoiButton.setHidden(True)
        self.roiFitNoteLabel.setHidden(True)
        self.saveRoiButton.setHidden(True)
        self.acceptGeneratedRoiButton.setCheckable(False)
        self.undoRoiButton.setCheckable(False)
        self.acceptGeneratedRoiButton.clicked.connect(self.moveToTic)
        self.undoRoiButton.clicked.connect(self.restartRoi)
        self.update()

    def restartRoi(self):
        if self.niftiSegPath is None:
            self.mcResultsArray = []
            self.mcResultsBmode = []
            self.mcResultsCE = []
            self.mcBmodeDisplayLabel.clear()
            self.mcCeDisplayLabel.clear()
            self.drawRoiButton.setHidden(False)
            self.undoLastPtButton.setHidden(False)
            self.redrawRoiButton.setHidden(False)
            self.fitToRoiButton.setHidden(False)
            self.acceptGeneratedRoiButton.setHidden(True)
            self.undoRoiButton.setHidden(True)
            self.roiFitNoteLabel.setHidden(False)
        else:
            self.acceptGeneratedRoiButton.setHidden(True)
            self.undoRoiButton.setHidden(True)
            self.loadRoiButton.setHidden(False)
            self.newRoiButton.setHidden(False)
            self.maskCoverImg.fill(0)
        self.updateBmode()
        self.updateCE()
        self.update()

    def curSliceSpinBoxValueChanged(self):
        self.curFrameIndex = int(self.curSliceSpinBox.value())
        self.curSliceSlider.setValue(self.curFrameIndex)
        self.curSecondLabel.setText(str(self.sliceArray[self.curFrameIndex]))
        self.updateBmode()
        self.updateCE()
        self.update()

    def curSliceSliderValueChanged(self):
        self.curFrameIndex = int(self.curSliceSlider.value())
        self.curSliceSpinBox.setValue(self.curFrameIndex)
        self.curSecondLabel.setText(str(self.sliceArray[self.curFrameIndex]))
        self.updateBmode()
        self.updateCE()
        self.update()

    def openNiftiImage(self, bmodePath, cePath):
        bmodeFile = nib.load(bmodePath)
        ceFile = nib.load(cePath)

        bmodePixDims = bmodeFile.header['pixdim']
        cePixDims = ceFile.header['pixdim']
        self.pixelScale = bmodePixDims[0]*bmodePixDims[1]*bmodePixDims[2] # mm^3

        self.bmode = bmodeFile.get_fdata(caching='unchanged')
        self.contrastEnhanced = ceFile.get_fdata(caching='unchanged')
        print(self.bmode.shape)
        print(self.contrastEnhanced.shape)
        self.bmode = self.bmode.reshape((self.bmode.shape[0], self.bmode.shape[1], self.bmode.shape[2], self.bmode.shape[4]))
        self.contrastEnhanced = self.contrastEnhnaced.reshape((self.contrastEnhanced.shape[0], self.contrastEnhanced.shape[1], self.contrastEnhanced.shape[2], self.contrastEnhanced.shape[4]))

        self.bmode = np.mean(self.bmode, axis=3)
        self.contrastEnhanced = np.mean(self.contrastEnhanced, axis=3)

    def openDicomImage(self, index, xcel_dir):  

        self.x0_bmode = int(self.df.loc[index, 'x0_bmode'])     
        self.y0_bmode = int(self.df.loc[index, 'y0_bmode']) 
        self.x = int(self.df.loc[index, 'x'])
        self.y = int(self.df.loc[index, 'y'])
        self.x0_CE = int(self.df.loc[index, 'x0_CE'])
        self.y0_CE = int(self.df.loc[index, 'y0_CE'])
        self.x = int(self.df.loc[index, 'x'])
        self.y = int(self.df.loc[index, 'y'])
        self.CE_side = self.df.loc[index, 'CE_window_left(l)_or_right(r)']
        self.cineRate = self.df.loc[self.xcelIndices[index], 'CineRate']
        self.index = index
        self.xcel_dir = xcel_dir
        
        # pickle_full_path = os.path.join(xcel_dir, self.df.loc[index, 'pickle_bmode_CE_gray_path'])
        fullPath = os.path.join(xcel_dir, self.df.loc[self.xcelIndices[index], 'cleaned_path'])
        self.fullArray = dicom.dcmread(fullPath).pixel_array[:,:,:,0]

        self.bmode = self.full_array[:,self.y0_bmode:self.y0_bmode+self.h_bmode, \
                                     self.x0_bmode:self.x0_bmode+self.w_bmode]
        
        self.contrastEnhanced = self.full_array[:, self.y0_CE:self.y0_CE+self.h_CE, \
                                                self.x0_CE:self.x0_CE+self.w_CE]

        # ceSide = self.df.loc[self.xcelIndices[index], 'CE_window_left(l)_or_right(r)']
        # if ceSide == 'r':
        #     self.bmode = self.fullArray[:,:,:int(self.fullArray.shape[2]/2)]
        #     self.contrastEnhanced = self.fullArray[:,:,int(self.fullArray.shape[2]/2):]
        #     self.x0_bmode = 0
        #     self.x0_CE = int(self.fullArray.shape[2]/2)
        # else:
        #     self.bmode = self.fullArray[:,:,int(self.fullArray.shape[2]/2):]
        #     self.contrastEnhanced = self.fullArray[:,:,:int(self.fullArray.shape[2]/2)]
        #     self.x0_bmode = int(self.fullArray.shape[2]/2)
        #     self.x0_CE = 0
        # self.numSlices = self.bmode.shape[0]
        # self.x = self.bmode.shape[2]
        # self.y = self.bmode.shape[1]
        # self.y0_bmode = 0
        # self.y0_CE = 0

        self.maskCoverImg = np.zeros([self.y, self.x, 4])
        self.pixelScale = (self.df.loc[self.xcelIndices[self.index], "height"]/self.y)*(self.df.loc[self.xcelIndices[self.index], "width"]/self.x)

        self.curSliceSlider.setMaximum(self.numSlices - 1)
        self.curSliceSpinBox.setMaximum(self.numSlices - 1)

        self.sliceArray = np.round([i*(1/self.cineRate) for i in range(self.numSlices)], decimals=2)
        self.totalSecondsLabel.setText(str(self.sliceArray[-1]))

        self.curSliceTotal.setText(str(self.numSlices-1))

        self.curSliceSpinBox.setValue(self.sliceArray[self.curFrameIndex])
        self.curSliceSlider.setValue(self.curFrameIndex)
        self.curSliceSlider.valueChanged.connect(self.curSliceSliderValueChanged)
        self.curSliceSpinBox.valueChanged.connect(self.curSliceSpinBoxValueChanged)

        self.drawRoiButton.setCheckable(True)

        #getting initial image data for bmode and CE
        self.dataBmode = self.bmode[self.curFrameIndex]
        self.dataBmode = np.require(self.dataBmode, np.uint8, 'C')
        self.dataCE = self.contrastEnhanced[self.curFrameIndex]
        self.dataCE = np.require(self.dataCE, np.uint8, 'C')
        self.maskCoverImg = np.require(self.maskCoverImg, np.uint8, 'C')
        
        self.bytesLineMask, _ = self.maskCoverImg[:,:,0].strides
        self.bytesLineBmode, _ = self.dataBmode.strides #in order to create proper QImage, need to know bytes/line
        self.bytesLineCE, _ = self.dataCE.strides

        self.qImgBmode = QImage(self.dataBmode, self.x, self.y, self.bytesLineBmode, QImage.Format_Grayscale8) #creating QImage
        self.qImgCE = QImage(self.dataCE, self.x, self.y, self.bytesLineCE, QImage.Format_Grayscale8)
        self.qImgMask = QImage(self.maskCoverImg, self.x, self.y, self.bytesLineMask, QImage.Format_ARGB32)
        self.qImgMask.mirrored().save(os.path.join("Junk", "bModeImRaw.png")) # Save as .png file

        self.bmodePlane.setPixmap(QPixmap.fromImage(self.qImgBmode).scaled(381, 351))
        self.cePlane.setPixmap(QPixmap.fromImage(self.qImgCE).scaled(381, 351))
        self.bmodeMaskLayer.setPixmap(QPixmap.fromImage(self.qImgMask).scaled(381, 351))
        self.ceMaskLayer.setPixmap(QPixmap.fromImage(self.qImgMask).scaled(381, 351))

        self.closeRoiButton.clicked.connect(self.acceptPolygon) #called to exit the paint function
        self.undoLastPtButton.clicked.connect(self.undoLastPoint) #deletes last drawn rectangle if on sag or cor slices

        self.redrawRoiButton.clicked.connect(self.undoLastRoi)
        self.drawRoiButton.clicked.connect(self.startRoiDraw)

    def updateBmode(self):
        if len(self.mcResultsArray):
            self.mcDataBmode = np.require(self.mcResultsBmode[self.curFrameIndex], np.uint8, 'C')
            self.bytesLineMc, _ = self.mcDataBmode[:,:,0].strides
            self.qImgMcBmode = QImage(self.mcDataBmode, self.x, self.y, self.bytesLineMc, QImage.Format_RGB888)
            self.mcBmodeDisplayLabel.setPixmap(QPixmap.fromImage(self.qImgMcBmode).scaled(381, 351))
        else:
            self.dataBmode = self.bmode[self.curFrameIndex]
            self.dataBmode = np.require(self.dataBmode, np.uint8, 'C')
            self.maskCoverImg = np.require(self.maskCoverImg, np.uint8, 'C')

            self.bytesLineBmode, _ = self.dataBmode.strides
            self.bytesLineMask, _ = self.maskCoverImg[:,:,0].strides
            self.qImgBmode = QImage(self.dataBmode, self.x, self.y, self.bytesLineBmode, QImage.Format_Grayscale8)
            self.qImgMask = QImage(self.maskCoverImg, self.x, self.y, self.bytesLineMask, QImage.Format_ARGB32)

            self.bmodePlane.setPixmap(QPixmap.fromImage(self.qImgBmode).scaled(381, 351))
            self.bmodeMaskLayer.setPixmap(QPixmap.fromImage(self.qImgMask).scaled(381, 351))

    def updateCE(self):
        if len(self.mcResultsArray):
            self.mcDataCE = np.require(self.mcResultsCE[self.curFrameIndex], np.uint8, 'C')
            self.bytesLineMc, _ = self.mcDataCE[:,:,0].strides
            self.qImgMcCE = QImage(self.mcDataCE, self.x, self.y, self.bytesLineMc, QImage.Format_RGB888)
            self.mcCeDisplayLabel.setPixmap(QPixmap.fromImage(self.qImgMcCE).scaled(381, 351))
        else:
            self.dataCE = self.contrastEnhanced[self.curFrameIndex]
            self.dataCE = np.require(self.dataCE, np.uint8, 'C')
            self.maskCoverImg = np.require(self.maskCoverImg, np.uint8, 'C')

            self.bytesLineCE, _ = self.dataCE.strides
            self.bytesLineMask, _ = self.maskCoverImg[:,:,0].strides
            self.qImgCE = QImage(self.dataCE, self.x, self.y, self.bytesLineCE, QImage.Format_Grayscale8)
            self.qImgMask = QImage(self.maskCoverImg, self.x, self.y, self.bytesLineMask, QImage.Format_ARGB32)


            self.cePlane.setPixmap(QPixmap.fromImage(self.qImgCE).scaled(381, 351))
            self.ceMaskLayer.setPixmap(QPixmap.fromImage(self.qImgMask).scaled(381, 351))

    def updateCrosshair(self):
        if self.xCur < 741 and self.xCur > 360 and self.yCur < 501 and self.yCur > 150:
            self.actualX = int((self.xCur - 361)*(self.y-1)/381)
            self.actualY = int((self.yCur - 151)*(self.x-1)/351)
            plotX = self.xCur - 361
        elif self.xCur < 1151 and self.xCur > 770 and self.yCur < 501 and self.yCur > 150:
            self.actualX = int((self.xCur-771)*(self.y-1)/381)
            self.actualY = int((self.yCur-151)*(self.x-1)/351)
            plotX = self.xCur - 771
        else:
            return
        
        plotY = self.yCur - 151

        self.bmodeCoverLabel.pixmap().fill(Qt.transparent)
        painter = QPainter(self.bmodeCoverLabel.pixmap())
        painter.setPen(Qt.yellow)
        bmodeVertLine = QLine(plotX, 0, plotX, 351)
        bmodeLatLine = QLine(0, plotY, 381, plotY)
        painter.drawLines([bmodeVertLine, bmodeLatLine])
        painter.end()
            
        self.ceCoverLabel.pixmap().fill(Qt.transparent)
        painter = QPainter(self.ceCoverLabel.pixmap())
        painter.setPen(Qt.yellow)
        ceVertLine = QLine(plotX, 0, plotX, 351)
        ceLatLine = QLine(0, plotY, 381, plotY)
        painter.drawLines([ceVertLine, ceLatLine])
        painter.end()
        self.update()

    def updateSpline(self):
        if len(self.curPointsPlottedX) > 0:
            if self.spline != None:
                self.spline.remove()
            
            if len(self.curPointsPlottedX) > 1:
                xSpline, ySpline = calculateSpline(self.curPointsPlottedX, self.curPointsPlottedY)
                spline = [(int(xSpline[i]), int(ySpline[i])) for i in range(len(xSpline))]
                spline = np.array([*set(spline)])
                xSpline, ySpline = np.transpose(spline)
                xSpline = np.clip(xSpline, a_min=0, a_max=self.x-1)
                ySpline = np.clip(ySpline, a_min=0, a_max=self.y-1)
                self.maskCoverImg[self.oldSpline] = [0,0,0,0]
                self.oldSpline = []
                for i in range(len(xSpline)):
                    self.maskCoverImg[xSpline[i]-1:xSpline[i]+2, ySpline[i]-1:ySpline[i]+2] = [255, 255, 0, 255]
                    for j in range(3):
                        for k in range(3):
                            self.oldSpline.append([xSpline[i]-j-1, ySpline[i]-k-1])
            else:
                self.maskCoverImg.fill(0)
                self.oldSpline = []
            for i in range(len(self.curPointsPlottedX)):
                self.maskCoverImg[self.curPointsPlottedX[i]-2:self.curPointsPlottedX[i]+3, \
                                    self.curPointsPlottedY[i]-2:self.curPointsPlottedY[i]+3] = [0,0,255, 255]
        else:
            self.maskCoverImg.fill(0)
            self.oldSpline = []

        self.updateBmode()
        self.updateCE()
        self.updateCrosshair()

    def mousePressEvent(self,event):
        self.xCur = event.x()
        self.yCur = event.y()
        if self.drawRoiButton.isChecked():
            # Plot ROI points
            if self.xCur < 741 and self.xCur > 360 and self.yCur < 501 and self.yCur > 150:
                self.actualY = int((self.xCur - 361)*(self.x-1)/381)
                self.actualX = int((self.yCur - 151)*(self.y-1)/351)
            elif self.xCur < 1151 and self.xCur > 770 and self.yCur < 501 and self.yCur > 150:
                self.actualY = int((self.xCur-771)*(self.x-1)/381)
                self.actualX = int((self.yCur-151)*(self.y-1)/351)
            else:
                return
            self.curPointsPlottedX.append(self.actualX)
            self.curPointsPlottedY.append(self.actualY)
            self.updateSpline()

    def mouseMoveEvent(self, event):
        self.xCur = event.x()
        self.yCur = event.y()
        self.updateCrosshair()

    
    def acceptPolygon(self):
        # 2d interpolation
        if len(self.curPointsPlottedX) > 2:
            self.drawRoiButton.setChecked(False)

            # remove duplicate points
            points = np.transpose(np.array([self.curPointsPlottedX, self.curPointsPlottedY]))
            points = removeDuplicates(points)
            [self.curPointsPlottedX, self.curPointsPlottedY] = np.transpose(points)
            self.curPointsPlottedX = list(self.curPointsPlottedX)
            self.curPointsPlottedY = list(self.curPointsPlottedY)
            self.curPointsPlottedX.append(self.curPointsPlottedX[0])
            self.curPointsPlottedY.append(self.curPointsPlottedY[0])
            self.maskCoverImg.fill(0)

            xSpline, ySpline = calculateSpline(self.curPointsPlottedX, self.curPointsPlottedY)
            spline = [(int(xSpline[i]), int(ySpline[i])) for i in range(len(xSpline))]
            spline = np.array([*set(spline)])
            xSpline, ySpline = np.transpose(spline)
            xSpline = np.clip(xSpline, a_min=0, a_max=self.x-1)
            ySpline = np.clip(ySpline, a_min=0, a_max=self.y-1)
            self.oldSpline = []
            for i in range(len(xSpline)):
                self.maskCoverImg[xSpline[i]-1:xSpline[i]+2, ySpline[i]-1:ySpline[i]+2] = [0, 0, 255, 255]
                for j in range(3):
                    self.pointsPlotted.append((xSpline[i]-j, ySpline[i]-j))
                    if not j:
                        self.pointsPlotted.append((xSpline[i]+j, ySpline[i]+j))
            self.curPointsPlottedX = []
            self.curPointsPlottedY = []
            self.redrawRoiButton.setHidden(False)
            self.closeRoiButton.setHidden(True)
            self.undoLastPtButton.setHidden(True)
            self.saveRoiButton.setHidden(False)
            self.roiFitNoteLabel.setHidden(False)
            self.drawRoiButton.setChecked(False)
            self.drawRoiButton.setCheckable(False)
            self.fitToRoiButton.clicked.connect(self.perform_MC)
            self.updateBmode()
            self.updateCE()
            self.updateCrosshair()

            

    def undoLastPoint(self):
        if len(self.curPointsPlottedX) and (not len(self.pointsPlotted)):
            self.maskCoverImg[self.curPointsPlottedX[-1]-2:self.curPointsPlottedX[-1]+3, \
                              self.curPointsPlottedY[-1]-2:self.curPointsPlottedY[-1]+3] = [0,0,0,0]
            self.curPointsPlottedX.pop()
            self.curPointsPlottedY.pop()
            self.updateSpline()


    def startRoiDraw(self):
        if self.drawRoiButton.isChecked():
            self.closeRoiButton.setHidden(False)
            self.redrawRoiButton.setHidden(True)
        elif not len(self.curPointsPlottedX):
            self.closeRoiButton.setHidden(True)
            self.redrawRoiButton.setHidden(False)

    def undoLastRoi(self):
        if len(self.pointsPlotted) > 0:
            self.pointsPlotted = []
            self.maskCoverImg.fill(0)
            self.redrawRoiButton.setHidden(True)
            self.closeRoiButton.setHidden(False)
            self.roiFitNoteLabel.setHidden(True)
            self.drawRoiButton.setCheckable(True)
            self.saveRoiButton.setHidden(True)
            self.undoLastPtButton.setHidden(False)
            self.fitToRoiButton.clicked.disconnect()
            self.updateBmode()
            self.updateCE()
            self.update()

    def computeTic(self):
        times = np.array([i*(1/self.cineRate) for i in range(self.numSlices)])
        TIC, self.ticAnalysisGui.roiArea = mc.generate_TIC(self.mcResultsCE, self.bboxes, times, 24.09, self.pixelScale, self.ref_frames[0])
        # # Compute TICs

        # # resize all MC bboxes to same size
        # self.bboxes = mc.resize_mc_bboxes(self.bboxes)

        # # remove outlier bboxes
        # self.bboxes = mc.remove_outlier_bboxes(self.bboxes)

        # self.ceMcBboxes = mc.create_ce_mc_bboxes(self.bboxes, self.x0_bmode, self.x0_CE, self.CE_side)

        # self.ceMcRoi = mc.cut_ROI200(self.fullArray, self.ceMcBboxes, (self.x0_CE, self.y0_CE, self.x, self.y))

        # self.ticArray = mc.getAllTICs(self.ceMcRoi, self.pixelScale, times)
        

        # Bunch of checks
        if np.isnan(np.sum(TIC[:,1])):
            print("STOPPED: NaNs in the ROI")
            return
        if np.isinf(np.sum(TIC[:,1])):
            print("STOPPED: Infs in the ROI")
            return
        
        # self.meanTIC = np.mean(self.ticArray.reshape((self.ticArray.shape[0]*self.ticArray.shape[1], \
        #                                               self.ticArray.shape[2], self.ticArray.shape[3])), axis=0)

        # self.ticX = np.array([[self.meanTIC[i,0],i] for i in range(len(self.meanTIC[:,0]))])
        # self.ticY = self.meanTIC[:,1]
        self.ticX = np.array([[TIC[i,0],i] for i in range(len(TIC[:,0]))])
        self.ticY = TIC[:,1]
        self.ticAnalysisGui.ax.clear()
        self.ticAnalysisGui.ticX = []
        self.ticAnalysisGui.ticY = []
        self.ticAnalysisGui.pixelScale = self.pixelScale
        self.ticAnalysisGui.removedPointsX = []
        self.ticAnalysisGui.removedPointsY = []
        self.ticAnalysisGui.selectedPoints = []
        self.ticAnalysisGui.t0Index = -1
        self.ticAnalysisGui.graph(self.ticX, self.ticY)
        self.ticAnalysisGui.ticArray = TIC

    def moveToTic(self):
        self.ticAnalysisGui.timeLine = None
        self.computeTic()
        self.ticAnalysisGui.dataFrame = self.dataFrame
        self.ticAnalysisGui.curFrameIndex = self.curFrameIndex
        self.ticAnalysisGui.mcResultsBmode = self.mcResultsBmode
        self.ticAnalysisGui.mcResultsCE = self.mcResultsCE
        self.ticAnalysisGui.x = self.x
        self.ticAnalysisGui.y = self.y
        self.ticAnalysisGui.sliceArray = self.sliceArray
        self.ticAnalysisGui.lastGui = self
        self.ticAnalysisGui.x0_bmode = self.x0_bmode
        self.ticAnalysisGui.y0_bmode = self.y0_bmode
        self.ticAnalysisGui.x = self.x
        self.ticAnalysisGui.y = self.y
        self.ticAnalysisGui.x0_CE = self.x0_CE
        self.ticAnalysisGui.y0_CE = self.y0_CE
        self.ticAnalysisGui.x = self.x
        self.ticAnalysisGui.y = self.y
        self.ticAnalysisGui.setFilenameDisplays(self.imagePathInput.text())
        self.ticAnalysisGui.deSelectLastPointButton.setHidden(True)
        self.ticAnalysisGui.removeSelectedPointsButton.setHidden(True)
        self.ticAnalysisGui.restoreLastPointsButton.setHidden(True)
        self.ticAnalysisGui.acceptTicButton.setHidden(True)
        self.ticAnalysisGui.acceptT0Button.setHidden(True)
        self.ticAnalysisGui.t0Slider.setHidden(True)
        self.ticAnalysisGui.selectT0Button.setHidden(False)
        self.ticAnalysisGui.updateBmode()
        self.ticAnalysisGui.updateCE()
        self.ticAnalysisGui.show()
        self.hide()


def calculateSpline(xpts, ypts): # 2D spline interpolation
    cv = []
    for i in range(len(xpts)):
        cv.append([xpts[i], ypts[i]])
    cv = np.array(cv)
    if len(xpts) == 2:
        tck, u_ = interpolate.splprep(cv.T, s=0.0, k=1)
    elif len(xpts) == 3:
        tck, u_ = interpolate.splprep(cv.T, s=0.0, k=2)
    else:
        tck, u_ = interpolate.splprep(cv.T, s=0.0, k=3)
    x,y = np.array(interpolate.splev(np.linspace(0, 1, 1000), tck))
    return x, y

def removeDuplicates(ar):
        # Credit: https://stackoverflow.com/questions/480214/how-do-i-remove-duplicates-from-a-list-while-preserving-order
        seen = set()
        seen_add = seen.add
        return [x for x in ar if not (tuple(x) in seen or seen_add(tuple(x)))]
         



if __name__ == "__main__":
    pickle_full_path = "/Users/davidspector/Home/Stanford/MC_Sample_Code/data/P_005_021/pickle_bmode_CE_gray/ceus_inj1_wi_000000.000000.pkl"
    x0_bmode = 0
    x0_CE = 721
    y0_bmode = 40
    y0_CE = 40
    x = 721
    y = 697
    x = 721
    y = 697

    import sys
    app = QApplication(sys.argv)
    # selectWindow = QWidget()
    ui = RoiSelectionGUI()
    # ui.selectImage.show()
    ui.show()
    sys.exit(app.exec_())