from CeusMcTool2d.genParamap_ui import Ui_genParamap
from Utils.ceusParamap2d import get_paramap2d

import os
import re
from PyQt5.QtWidgets import QWidget, QFileDialog

class ParamapInputs():
    def __init__(self):
        self.image = None
        self.seg_mask = None
        self.res0 = None
        self.res1 = None
        self.timeConst = None
        self.mc = None

class GenParamapGUI(Ui_genParamap, QWidget):
    def __init__(self, inputs: ParamapInputs):
        super().__init__()
        self.setupUi(self)
        self.fileNameErrorLabel.setHidden(True)
        self.dataSavedSuccessfullyLabel.setHidden(True)

        self.image = inputs.image
        self.seg_mask = inputs.seg_mask
        self.res0 = inputs.res0
        self.res1 = inputs.res1
        self.windowHeightValue = None
        self.windowWidthValue = None
        self.res0, self.res1 = inputs.res0, inputs.res1
        self.timeConst = inputs.timeConst
        self.mc = inputs.mc

        self.chooseFolderButton.clicked.connect(self.chooseFolder)
        self.clearFolderButton.clicked.connect(self.clearFolder)
        self.generateParamapButton.clicked.connect(self.gen_paramap)

    def chooseFolder(self):
        folderName = QFileDialog.getExistingDirectory(None, "Select Directory")
        if folderName != "":
            self.newFolderPathInput.setText(folderName)

    def clearFolder(self):
        self.newFolderPathInput.clear()


    def gen_paramap(self):
        if os.path.exists(self.newFolderPathInput.text()):
            if not (
                self.newFileNameInput.text().endswith(".nii.gz")
                and (not bool(re.search(r"\s", self.newFileNameInput.text())))
            ):
                self.fileNameWarningLabel.setHidden(True)
                self.fileNameErrorLabel.setHidden(False)
                return
            out = get_paramap2d(self.image, self.seg_mask, self.axWinSizeVal.value(), self.latWinSizeVal.value(), 
                          os.path.join(self.newFolderPathInput.text(), self.newFileNameInput.text()), self.timeConst, 
                          self.res0, self.res1, self.axOverlapVal.value(), self.latOverlapVal.value(), self.mc)
            if out:
                return # Voxel dims too small
            
            self.dataSavedSuccessfullyLabel.setHidden(False)
            self.newFileNameInput.setHidden(True)
            self.newFileNameLabel.setHidden(True)
            self.newFolderPathInput.setHidden(True)
            self.saveRoiLabel.setHidden(True)
            self.newFileNameLabel.setHidden(True)
            self.fileNameErrorLabel.setHidden(True)
            self.roiFolderPathLabel.setHidden(True)
            self.fileNameWarningLabel.setHidden(True)
            self.generateParamapButton.setHidden(True)
            self.clearFolderButton.setHidden(True)
            self.chooseFolderButton.setHidden(True)
            self.axOverlapLabel.setHidden(True)
            self.axOverlapVal.setHidden(True)
            self.latOverlapVal.setHidden(True)
            self.latOverlapLabel.setHidden(True)
            self.latOverlapLabel_2.setHidden(True)
            self.latWinSizeLabel.setHidden(True)
            self.latWinSizeVal.setHidden(True)
            self.axWinSizeLabel.setHidden(True)
            self.axWinSizeVal.setHidden(True)
            self.imageDepthLabel.setHidden(True)
            self.imageDepthVal.setHidden(True)
            self.imageWidthLabel.setHidden(True)
            self.imageWidthVal.setHidden(True)
