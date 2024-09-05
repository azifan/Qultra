from PyQt5.QtWidgets import QWidget

from src.UtcTool2d.editImageDisplay_ui import Ui_editBmode

class EditImageDisplayGUI(Ui_editBmode, QWidget):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.contrastValDisplay.setTextVisible(False)
        self.brightnessValDisplay.setTextVisible(False)
        self.sharpnessValDisplay.setTextVisible(False)

