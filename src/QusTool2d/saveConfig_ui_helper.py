import os
import re
import pickle

from PyQt5.QtWidgets import QWidget, QFileDialog

from src.QusTool2d.saveConfig_ui import Ui_saveConfig
from pyQus.analysisObjects import Config


class SaveConfigGUI(Ui_saveConfig, QWidget):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.fileNameErrorLabel.setHidden(True)
        self.dataSavedSuccessfullyLabel.setHidden(True)
        
        self.imName: str
        self.phantomName: str
        self.config: Config

        self.chooseFolderButton.clicked.connect(self.chooseFolder)
        self.clearFolderButton.clicked.connect(self.clearFolder)
        self.saveConfigButton.clicked.connect(self.saveConfig)

    def chooseFolder(self):
        folderName = QFileDialog.getExistingDirectory(None, "Select Directory")
        if folderName != "":
            self.newFolderPathInput.setText(folderName)

    def clearFolder(self):
        self.newFolderPathInput.clear()

    def saveConfig(self):
        if os.path.exists(self.newFolderPathInput.text()):
            if not (
                self.newFileNameInput.text().endswith(".pkl")
                and (not bool(re.search(r"\s", self.newFileNameInput.text())))
            ):
                self.fileNameWarningLabel.setHidden(True)
                self.fileNameErrorLabel.setHidden(False)
                return
            
            output = {"Image Name": self.imName, "Phantom Name": self.phantomName,
                      "Config": self.config}
            
            with open(os.path.join(
                    self.newFolderPathInput.text(), self.newFileNameInput.text()
                ),mode="wb") as pklfile:
                pickle.dump(output, pklfile, protocol=pickle.HIGHEST_PROTOCOL)
              
            self.dataSavedSuccessfullyLabel.setHidden(False)
            self.newFileNameInput.setHidden(True)
            self.newFileNameLabel.setHidden(True)
            self.newFolderPathInput.setHidden(True)
            self.saveConfigLabel.setHidden(True)
            self.newFileNameLabel.setHidden(True)
            self.fileNameErrorLabel.setHidden(True)
            self.configFolderPathLabel.setHidden(True)
            self.fileNameWarningLabel.setHidden(True)
            self.saveConfigButton.setHidden(True)
            self.clearFolderButton.setHidden(True)
            self.chooseFolderButton.setHidden(True)
