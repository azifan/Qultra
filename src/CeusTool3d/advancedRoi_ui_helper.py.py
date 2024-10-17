import platform

import numpy as np
import matplotlib.pyplot as plt
from PIL.ImageQt import ImageQt
from matplotlib.widgets import RectangleSelector
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QWidget, QApplication, QHBoxLayout
from PyQt5.QtGui import QPixmap, QPainter, QImage, QCursor, QResizeEvent
from PyQt5.QtCore import QLine, Qt, QPoint, pyqtSlot

from matplotlib.widgets import Slider, Button
import matplotlib as mpl
from matplotlib import pyplot as plt
import scipy.interpolate as inter
import numpy as np

from advancedRoi_ui import Ui_advancedRoi

system = platform.system()

import scipy.interpolate as interpolate
def calculateSpline(xpts, ypts):  # 2D spline interpolation
    cv = []
    for i in range(len(xpts)):
        cv.append([xpts[i], ypts[i]])
    cv = np.array(cv)
    if len(xpts) == 2:
        tck, _ = interpolate.splprep(cv.T, s=0.0, k=1)
    elif len(xpts) == 3:
        tck, _ = interpolate.splprep(cv.T, s=0.0, k=2)
    else:
        tck, _ = interpolate.splprep(cv.T, s=0.0, k=3)
    x, y = np.array(interpolate.splev(np.linspace(0, 1, 1000), tck))
    return x, y


class TicAnalysisGUI(Ui_advancedRoi, QWidget):
    def __init__(self):
        super().__init__()
        self.setupUi(self)


        self.setLayout(self.fullScreenLayout)

        self.fig = plt.figure()
        self.canvas = FigureCanvas(self.fig)
        self.horizLayout = QHBoxLayout(self.imFrame)
        self.horizLayout.addWidget(self.canvas)
        self.canvas.draw()
        self.ax = self.fig.add_subplot(111)



        #get a list of points to fit a spline to as well
        self.N = 10
        self.xmin = 0 
        self.xmax = 10 
        self.x = [5, 0, -5, 0, 5]
        self.y = [0, 5, 0, -5, 0]
        self.xvals, self.yvals = calculateSpline(self.x, self.y)
        mpl.rcParams['figure.subplot.right'] = 0.8
        self.pind = None #active point
        self.epsilon = 5 #max pixel distance
        self.ax.plot(self.xvals, self.yvals, 'k--', label='original')
        self.l = self.ax.scatter(self.x, self.y,color='k',marker='o', zorder=10)
        self.m, = self.ax.plot (self.xvals, self.yvals, 'r-', label='spline')
        self.ax.set_yscale('linear')
        self.ax.set_xlim(-10, 10)
        self.ax.set_ylim(-10, 10)
        self.ax.set_xlabel('x')
        self.ax.set_ylabel('y')
        self.ax.grid(True)
        self.ax.yaxis.grid(True,which='minor',linestyle='--')
        self.ax.legend(loc=2,prop={'size':22})
        self.fig.canvas.mpl_connect('button_press_event', self.button_press_callback)
        self.fig.canvas.mpl_connect('button_release_event', self.button_release_callback)
        self.fig.canvas.mpl_connect('motion_notify_event', self.motion_notify_callback)


    def updatePlot(self):
        self.l.remove()
        self.l = self.ax.scatter(self.x, self.y, color='k', marker='o', zorder=10)
        self.xvals, self.yvals = calculateSpline(self.x, self.y)
        self.m.set_xdata(self.xvals)
        self.m.set_ydata(self.yvals)
        # redraw canvas while idle
        self.fig.canvas.draw_idle()

    def button_press_callback(self, event):
        'whenever a mouse button is pressed'
        if event.inaxes is None:
            return
        if event.button != 1:
            return
        self.pind = self.get_ind_under_point(event)    

    def button_release_callback(self, event):
        'whenever a mouse button is released'
        if event.button != 1:
            return
        self.pind = None

    def get_ind_under_point(self, event):
        'get the index of the vertex under point if within epsilon tolerance'

        # display coords
        #print('display x is: {0}; display y is: {1}'.format(event.x,event.y))
        t = self.ax.transData.inverted()
        tinv = self.ax.transData 
        xy = t.transform([event.x,event.y])
        #print('data x is: {0}; data y is: {1}'.format(xy[0],xy[1]))
        xr = np.reshape(self.x,(np.shape(self.x)[0],1))
        yr = np.reshape(self.y,(np.shape(self.y)[0],1))
        xy_vals = np.append(xr,yr,1)
        xyt = tinv.transform(xy_vals)
        xt, yt = xyt[:, 0], xyt[:, 1]
        d = np.hypot(xt - event.x, yt - event.y)
        indseq, = np.nonzero(d == d.min())
        ind = indseq[0]

        #print(d[ind])
        if d[ind] >= self.epsilon:
            ind = None
        
        #print(ind)
        return ind

    def motion_notify_callback(self, event):
        'on mouse movement'
        if self.pind is None:
            return
        if event.inaxes is None:
            return
        if event.button != 1:
            return
        self.x[self.pind] = event.xdata
        self.y[self.pind] = event.ydata
        if not self.pind:
            self.x[-1] = event.xdata
            self.y[-1] = event.ydata
        if self.pind == len(self.x) - 1:
            self.x[0] = event.xdata
            self.y[0] = event.ydata
        self.updatePlot()
        self.fig.canvas.draw_idle()


    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self.canvas.draw()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    ui = TicAnalysisGUI()
    ui.show()
    sys.exit(app.exec_())
