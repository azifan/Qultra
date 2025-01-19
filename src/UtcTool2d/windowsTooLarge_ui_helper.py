from pathlib import Path

from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QMovie
from PyQt6.QtCore import QSize

from src.UtcTool2d.windowsTooLarge_ui import Ui_WindowsTooLarge

class WindowsTooLargeGUI(Ui_WindowsTooLarge, QWidget):
    def __init__(self):
        super().__init__()
        self.setupUi(self)