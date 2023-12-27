from UtcTool2d.editImageDisplay_ui import Ui_editBmode

from PyQt5.QtWidgets import QWidget


class EditImageDisplayGUI(Ui_editBmode, QWidget):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.contrastValDisplay.setTextVisible(False)
        self.brightnessValDisplay.setTextVisible(False)
        self.sharpnessValDisplay.setTextVisible(False)

