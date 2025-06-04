
import sys
from PyQt6.QtWidgets import QApplication, QWidget
from welcome_ui import Ui_WelcomePage

# Attempt to import helper pages; disable buttons if unavailable
try:
    from src.CeusTool3d.selectImage_ui_helper import SelectImageGUI_CeusTool3d
except ImportError:
    SelectImageGUI_CeusTool3d = None

try:
    from src.CeusMcTool2d.selectImage_ui_helper import SelectImageGUI_CeusMcTool2d
except ImportError:
    SelectImageGUI_CeusMcTool2d = None

try:
    from src.UtcTool2d.selectImage_ui_helper import SelectImageGUI_UtcTool2dIQ
except ImportError:
    SelectImageGUI_UtcTool2dIQ = None

class WelcomeGui(Ui_WelcomePage, QWidget):
    """
    Main welcome GUI that allows navigation to different tools.
    """
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Connect buttons only if the corresponding class is available; else disable
        if SelectImageGUI_UtcTool2dIQ:
            self.utc2dButton.clicked.connect(lambda: self.open_page(SelectImageGUI_UtcTool2dIQ))
        else:
            self.utc2dButton.setEnabled(False)

        if SelectImageGUI_CeusTool3d:
            self.dceus3dButton.clicked.connect(lambda: self.open_page(SelectImageGUI_CeusTool3d))
        else:
            self.dceus3dButton.setEnabled(False)

        if SelectImageGUI_CeusMcTool2d:
            self.dceus2dButton.clicked.connect(lambda: self.open_page(SelectImageGUI_CeusMcTool2d))
        else:
            self.dceus2dButton.setEnabled(False)

        self.nextPage = None
        self.setLayout(self.verticalLayout)

    def open_page(self, PageClass):
        """
        Open the next page GUI by instantiating the given PageClass.
        """
        try:
            self.nextPage = PageClass()
            self.nextPage.resize(self.size())
            self.nextPage.welcomeGui = self
            self.nextPage.show()
            self.hide()
        except Exception as e:
            print(f"Error opening page: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = WelcomeGui()
    ui.show()
    sys.exit(app.exec())
