import io

from PyQt6.QtCore import QBuffer, QEvent, QObject, QPoint, pyqtSignal
from PyQt6.QtGui import QImage
from PIL import Image

def qImToPIL(qIm: QImage) -> Image:
    buffer = QBuffer()
    buffer.open(QBuffer.OpenModeFlag.ReadWrite)
    qIm.save(buffer, "PNG")
    return Image.open(io.BytesIO(buffer.data()))

class MouseTracker(QObject):
    positionChanged = pyqtSignal(QPoint)
    positionClicked = pyqtSignal(QPoint)

    def __init__(self, widget):
        super().__init__(widget)
        self._widget = widget
        self.widget.setMouseTracking(True)
        self.widget.installEventFilter(self)

    @property
    def widget(self):
        return self._widget

    def eventFilter(self, o, e):
        if o is self.widget and e.type() == QEvent.Type.MouseMove:
            self.positionChanged.emit(e.pos())
        elif o is self.widget and e.type() == QEvent.Type.MouseButtonPress:
            self.positionClicked.emit(e.pos())
        return super().eventFilter(o, e)