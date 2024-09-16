import os
import shutil
import platform

import nibabel as nib
from PyQt5.QtWidgets import QWidget, QApplication, QFileDialog

from src.CeusTool3d.selectImage_ui import Ui_selectImage
from src.CeusTool3d.voiSelection_ui_helper import VoiSelectionGUI
import src.Parsers.philips3dCeus as phil
import src.Utils.utils as ut
from src.Parsers.philipsSipVolumeParser import sipParser

system = platform.system()

class SelectImageGUI_CeusTool3d(Ui_selectImage, QWidget):
    def __init__(self):
        # self.selectImage = QWidget()
        super().__init__()
        self.setupUi(self)

        if system == "Windows":
            self.imageSelectionLabelSidebar.setStyleSheet(
                """QLabel {
                font-size: 18px;
                color: rgb(255, 255, 255);
                background-color: rgba(255, 255, 255, 0);
                border: 0px;
                font-weight: bold;
            }"""
            )
            self.imageLabel.setStyleSheet(
                """QLabel {
                font-size: 13px;
                color: rgb(255, 255, 255);
                background-color: rgba(255, 255, 255, 0);
                border: 0px;
                font-weight: bold;
            }"""
            )
            self.imageFilenameDisplay.setStyleSheet(
                """QLabel {
                font-size: 11px;
                color: rgb(255, 255, 255);
                background-color: rgba(255, 255, 255, 0);
                border: 0px;
            }"""
            )
            self.roiSidebarLabel.setStyleSheet(
                """QLabel {
                font-size: 18px;
                color: rgb(255, 255, 255);
                background-color: rgba(255, 255, 255, 0);
                border: 0px;
                font-weight: bold;
            }"""
            )
            self.analysisParamsLabel.setStyleSheet(
                """QLabel {
                font-size: 18px;
                color: rgb(255, 255, 255);
                background-color: rgba(255, 255, 255, 0);
                border: 0px;
                font-weight:bold;
            }"""
            )
            self.ticAnalysisLabel.setStyleSheet(
                """QLabel {
                font-size: 18px;
                color: rgb(255, 255, 255);
                background-color: rgba(255, 255, 255, 0);
                border: 0px;
                font-weight: bold;
            }"""
            )
            self.rfAnalysisLabel.setStyleSheet(
                """QLabel {
                font-size: 18px;
                color: rgb(255, 255, 255);
                background-color: rgba(255, 255, 255, 0);
                border: 0px;
                font-weight: bold;
            }"""
            )

        self.setLayout(self.fullScreenLayout)
        self.fullScreenLayout.removeItem(self.niftiLayout)
        self.hideNiftiLayout()
        self.fullScreenLayout.removeItem(self.philipsLayout)
        self.hidePhilipsLayout()
        self.fullScreenLayout.removeItem(self.xmlLayout)
        self.hideXmlLayout()

        self.voiSelectionGui: VoiSelectionGUI | None = None
        self.welcomeGui = None
        self.imagePath = ""
        self.bmodePath = ""
        self.timeconst = None
        self.backButton.clicked.connect(self.backToWelcomeScreen)

        self.philipsOptionButton.clicked.connect(self.selectPhilipsImageOption)
        self.philipsBackButton.clicked.connect(self.backFromPhilips)
        self.choosePhilipsImageFileButton.clicked.connect(self.getPhilipsFilePath)
        self.clearPhilipsImageFileButton.clicked.connect(self.clearPhilipsFilePath)
        self.philipsImageDestinationButton.clicked.connect(self.getPhilipsImageDestinationPath)
        self.clearPhilipsImageDestinationButton.clicked.connect(self.philipsImageDestinationPath.clear)
        self.generateImageButtonPhilips.clicked.connect(self.generateImagePhilips)
        
        self.xmlOptionButton.clicked.connect(self.selectXmlImageOption)
        self.xmlBackButton.clicked.connect(self.backFromXml)
        self.chooseXmlImageFolderButton.clicked.connect(self.getXmlFolderPath)
        self.clearXmlImageFolderButton.clicked.connect(self.clearXmlFolderPath)
        self.niftiImageDestinationButton.clicked.connect(self.getNiftiImageDestinationPath)
        self.clearNiftiImageDestinationButton.clicked.connect(self.niftiImageDestinationPath.clear)
        self.generateImageButtonXml.clicked.connect(self.generateImageXml)

        self.niftiOptionButton.clicked.connect(self.selectNiftiImageOption)
        self.niftiBackButton.clicked.connect(self.backFromNifti)
        self.chooseNiftiImageFileButton.clicked.connect(self.getNiftiImagePath)
        self.clearNiftiImageFileButton.clicked.connect(self.clearNiftiImagePath)
        self.chooseNiftiBmodeFileButton.clicked.connect(self.getNiftiBmodePath)
        self.clearNiftiBmodeFileButton.clicked.connect(self.clearNiftiBmodePath)
        self.generateImageButtonNifti.clicked.connect(self.generateImageNifti)

    def hideNiftiLayout(self):
        self.chooseNiftiImageFileButton.hide()
        self.clearNiftiImageFileButton.hide()
        self.niftiImagePathInput.hide()
        self.selectNiftiImageLabel.hide()
        self.chooseNiftiBmodeFileButton.hide()
        self.clearNiftiBmodeFileButton.hide()
        self.niftiBmodePathInput.hide()
        self.selectNiftiBmodeLabel.hide()
        self.frameRateLabelNifti.hide()
        self.frameRateValueNifti.hide()
        self.generateImageButtonNifti.hide()
        self.niftiBackButton.hide()
        self.selectDataLabelNifti.hide()
        self.selectImageErrorMsgNifti.hide()

    def showNiftiLayout(self):
        self.chooseNiftiImageFileButton.show()
        self.clearNiftiImageFileButton.show()
        self.niftiImagePathInput.show()
        self.selectNiftiImageLabel.show()
        self.chooseNiftiBmodeFileButton.show()
        self.clearNiftiBmodeFileButton.show()
        self.niftiBmodePathInput.show()
        self.selectNiftiBmodeLabel.show()
        self.frameRateLabelNifti.show()
        self.frameRateValueNifti.show()
        self.generateImageButtonNifti.show()
        self.niftiBackButton.show()
        self.selectDataLabelNifti.show()
        self.selectImageErrorMsgNifti.show()

    def hidePhilipsLayout(self):
        self.choosePhilipsImageFileButton.hide()
        self.clearPhilipsImageFileButton.hide()
        self.philipsImagePathInput.hide()
        self.selectPhilipsFileLabel.hide()
        self.philipsImageDestinationButton.hide()
        self.clearPhilipsImageDestinationButton.hide()
        self.philipsDestinationImageLabel.hide()
        self.philipsImageDestinationPath.hide()
        self.nProcLabel.hide()
        self.nProcSpinBox.hide()
        self.pixPerMmLabel.hide()
        self.pixPerMmSpinBox.hide()
        self.frameRateLabelPhilips.hide()
        self.frameRateValuePhilips.hide()
        self.philipsBackButton.hide()
        self.generateImageButtonPhilips.hide()
        self.selectDataLabelPhilips.hide()
        self.selectImageErrorMsgPhilips.hide()

    def showPhilipsLayout(self):
        self.choosePhilipsImageFileButton.show()
        self.clearPhilipsImageFileButton.show()
        self.philipsImagePathInput.show()
        self.selectPhilipsFileLabel.show()
        self.philipsImageDestinationButton.show()
        self.clearPhilipsImageDestinationButton.show()
        self.philipsDestinationImageLabel.show()
        self.philipsImageDestinationPath.show()
        self.nProcLabel.show()
        self.nProcSpinBox.show()
        self.pixPerMmLabel.show()
        self.pixPerMmSpinBox.show()
        self.frameRateLabelPhilips.show()
        self.frameRateValuePhilips.show()
        self.philipsBackButton.show()
        self.generateImageButtonPhilips.show()
        self.selectDataLabelPhilips.show()
        self.selectImageErrorMsgPhilips.show()

    def hideFormatLayout(self):
        self.philipsOptionButton.hide()
        self.selectDataLabel.hide()
        self.niftiOptionButton.hide()
        self.xmlOptionButton.hide()

    def showFormatLayout(self):
        self.philipsOptionButton.show()
        self.selectDataLabel.show()
        self.niftiOptionButton.show()
        self.xmlOptionButton.show()

    def hideXmlLayout(self):
        self.chooseXmlImageFolderButton.hide()
        self.clearXmlImageFolderButton.hide()
        self.selectXmlFolderImageLabel.hide()
        self.xmlImagePathInput.hide()
        self.clearNiftiImageDestinationButton.hide()
        self.niftiImageDestinationButton.hide()
        self.niftiDestinationImageLabel.hide()
        self.niftiImageDestinationPath.hide()
        self.frameRateLabelXml.hide()
        self.frameRateValueXml.hide()
        self.generateImageButtonXml.hide()
        self.selectDataLabelXml.hide()
        self.selectImageErrorMsgXml.hide()
        self.xmlBackButton.hide()

    def showXmlLayout(self):
        self.chooseXmlImageFolderButton.show()
        self.clearXmlImageFolderButton.show()
        self.selectXmlFolderImageLabel.show()
        self.xmlImagePathInput.show()
        self.clearNiftiImageDestinationButton.show()
        self.niftiImageDestinationButton.show()
        self.niftiDestinationImageLabel.show()
        self.niftiImageDestinationPath.show()
        self.frameRateLabelXml.show()
        self.frameRateValueXml.show()
        self.generateImageButtonXml.show()
        self.selectDataLabelXml.show()
        self.selectImageErrorMsgXml.show()
        self.xmlBackButton.show()

    def backToWelcomeScreen(self):
        self.welcomeGui.show()
        self.hide()

    def getNiftiImagePath(self):
        fileName, _ = QFileDialog.getOpenFileName(
            None, "Open File", filter="*.nii *.nii.gz"
        )
        if fileName != "":
            self.niftiImagePathInput.setText(fileName)

    def clearNiftiImagePath(self):
        self.niftiImagePathInput.clear()
        self.imagePath = ""

    def getNiftiBmodePath(self):
        fileName, _ = QFileDialog.getOpenFileName(
            None, "Open File", filter="*.nii *.nii.gz"
        )
        if fileName != "":
            self.niftiBmodePathInput.setText(fileName)

    def clearNiftiBmodePath(self):
        self.niftiBmodePathInput.clear()
        self.bmodePath = ""

    def getXmlFolderPath(self):
        fileName = QFileDialog.getExistingDirectory(None, "Select Directory")
        if fileName != "":
            self.xmlImagePathInput.setText(fileName)

    def clearXmlFolderPath(self):
        self.xmlImagePathInput.clear()
        self.imagePath = ""

    def getNiftiImageDestinationPath(self):
        fileName = QFileDialog.getExistingDirectory(None, "Select Directory")
        if fileName != "":
            self.niftiImageDestinationPath.setText(fileName)

    def getPhilipsFilePath(self):
        fileName, _ = QFileDialog.getOpenFileName(None, "Open File", filter="*.raw")
        if fileName != "":
            self.philipsImagePathInput.setText(fileName)

    def clearPhilipsFilePath(self):
        self.philipsImagePathInput.clear()
        self.imagePath = ""
        self.bmodePath = ""

    def getPhilipsImageDestinationPath(self):
        fileName = QFileDialog.getExistingDirectory(None, "Select Directory")
        if fileName != "":
            self.philipsImageDestinationPath.setText(fileName)

    def backFromPhilips(self):
        self.hidePhilipsLayout()
        self.fullScreenLayout.removeItem(self.philipsLayout)
        self.showFormatLayout()
        self.fullScreenLayout.addItem(self.formatLayout)
        self.frameRateValuePhilips.setValue(0)
        self.timeconst = None

    def backFromXml(self):
        self.hideXmlLayout()
        self.fullScreenLayout.removeItem(self.xmlLayout)
        self.showFormatLayout()
        self.fullScreenLayout.addItem(self.formatLayout)
        self.frameRateValueXml.setValue(0)
        self.timeconst = None

    def backFromNifti(self):
        self.hideNiftiLayout()
        self.fullScreenLayout.removeItem(self.niftiLayout)
        self.showFormatLayout()
        self.fullScreenLayout.addItem(self.formatLayout)
        self.frameRateValueNifti.setValue(0)
        self.timeconst = None

    def selectNiftiImageOption(self):
        self.hideFormatLayout()
        self.fullScreenLayout.removeItem(self.formatLayout)
        self.showNiftiLayout()
        self.selectImageErrorMsgNifti.hide()
        self.frameRateLabelNifti.hide()
        self.frameRateValueNifti.hide()
        self.frameRateValueNifti.setValue(0)
        self.fullScreenLayout.addItem(self.niftiLayout)

    def selectXmlImageOption(self):
        self.hideFormatLayout()
        self.fullScreenLayout.removeItem(self.formatLayout)
        self.showXmlLayout()
        self.selectImageErrorMsgXml.hide()
        self.frameRateLabelXml.hide()
        self.frameRateValueXml.hide()
        self.frameRateValueXml.setValue(0)
        self.fullScreenLayout.addItem(self.xmlLayout)

    def selectPhilipsImageOption(self):
        self.hideFormatLayout()
        self.fullScreenLayout.removeItem(self.formatLayout)
        self.showPhilipsLayout()
        self.selectImageErrorMsgPhilips.hide()
        self.frameRateLabelPhilips.hide()
        self.frameRateValuePhilips.hide()
        self.frameRateValuePhilips.setValue(0)
        self.fullScreenLayout.addItem(self.philipsLayout)

    def generateImagePhilips(self):
        if self.imagePath != "":
            self.imagePath = ""
            self.bmodePath = ""
            if os.path.exists(self.philipsImageDestinationPath.text()) and \
                os.path.exists(self.philipsImagePathInput.text()):
                # parse each volume individually
                nProcs = int(self.nProcSpinBox.value())
                pixPerMm = self.pixPerMmSpinBox.value()
                sipFilename = os.path.basename(self.philipsImagePathInput.text())
                sipParser(os.path.dirname(self.philipsImagePathInput.text()), self.philipsImageDestinationPath.text(), 
                        sipFilename, nProcs, pixPerMm)
                
                destFolderName = "_".join(sipFilename.split("_")[:2])
                destFolder = os.path.join(self.philipsImageDestinationPath.text(), destFolderName)
                self.imagePath, self.bmodePath = phil.makeNifti(
                    destFolder,
                    sipFilename,
                )
                self.timeconst = nib.load(self.imagePath, mmap=False).header["pixdim"][4]
        if not self.timeconst:
            self.frameRateLabelPhilips.show()
            self.frameRateValuePhilips.show()
            self.timeconst = self.frameRateValuePhilips.value()
        if self.timeconst:
            self.moveToVoiSelection()

    def generateImageXml(self):
        if self.imagePath != "":
            self.imagePath = ""
            self.bmodePath = ""
            if (os.path.exists(self.niftiImageDestinationPath.text())
                    and os.path.isdir(self.niftiImageDestinationPath.text())
                    and os.path.exists(self.xmlImagePathInput.text())
                    and os.path.isdir(self.xmlImagePathInput.text())
                ):
                self.imagePath = ut.xml2nifti(
                    self.xmlImagePathInput.text(),
                    self.niftiImageDestinationPath.text(),
                )
                self.timeconst = nib.load(self.imagePath, mmap=False).header["pixdim"][4]
        if not self.timeconst:
            self.frameRateLabelXml.show()
            self.frameRateValueXml.show()
            self.timeconst = self.frameRateValueXml.value()
        if self.timeconst:
            self.moveToVoiSelection()

    def generateImageNifti(self):
        if self.imagePath != "":
            self.imagePath = ""
            self.bmodePath = ""
            if os.path.exists(self.niftiImagePathInput.text()):
                self.imagePath = self.niftiImagePathInput.text()
                self.timeconst = nib.load(self.imagePath, mmap=False).header["pixdim"][4]
            if len(self.niftiBmodePathInput.text()) and os.path.exists(self.niftiBmodePathInput.text()):
                self.bmodePath = self.niftiBmodePathInput.text()
        if not self.timeconst:
            self.frameRateLabelNifti.show()
            self.frameRateValueNifti.show()
            self.timeconst = self.frameRateValueNifti.value()
        if self.timeconst:
            self.moveToVoiSelection()
            
    def moveToVoiSelection(self):
        del self.voiSelectionGui
        self.voiSelectionGui = VoiSelectionGUI()
        self.voiSelectionGui.timeconst = 1 / self.timeconst
        self.voiSelectionGui.setFilenameDisplays(self.imagePath)
        if self.bmodePath != "":
            self.voiSelectionGui.openImage(self.bmodePath)
        else:
            self.voiSelectionGui.openImage(None)
        self.voiSelectionGui.lastGui = self
        self.voiSelectionGui.show()
        self.hide()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    ui = SelectImageGUI_CeusTool3d()
    ui.show()
    sys.exit(app.exec_())
