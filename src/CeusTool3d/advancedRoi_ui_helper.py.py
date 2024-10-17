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



        self.func = lambda x: 0.1*x**2
        #get a list of points to fit a spline to as well
        self.N = 10
        self.xmin = 0 
        self.xmax = 10 
        self.x = np.linspace(self.xmin, self.xmax, self.N)
        #spline fit
        self.yvals = self.func(self.x)
        self.spline = inter.InterpolatedUnivariateSpline(self.x, self.yvals)
        #figure.subplot.right
        mpl.rcParams['figure.subplot.right'] = 0.8
        self.pind = None #active point
        self.epsilon = 5 #max pixel distance
        self.X = np.arange(0,self.xmax+1,0.1)
        self.ax.plot(self.X, self.func(self.X), 'k--', label='original')
        self.l, = self.ax.plot (self.x, self.yvals,color='k',linestyle='none',marker='o',markersize=8)
        self.m, = self.ax.plot (self.X, self.spline(self.X), 'r-', label='spline')
        self.ax.set_yscale('linear')
        self.ax.set_xlim(0, self.xmax)
        self.ax.set_ylim(0, self.xmax)
        self.ax.set_xlabel('x')
        self.ax.set_ylabel('y')
        self.ax.grid(True)
        self.ax.yaxis.grid(True,which='minor',linestyle='--')
        self.ax.legend(loc=2,prop={'size':22})
        self.fig.canvas.mpl_connect('button_press_event', self.button_press_callback)
        self.fig.canvas.mpl_connect('button_release_event', self.button_release_callback)
        self.fig.canvas.mpl_connect('motion_notify_event', self.motion_notify_callback)


    def updatePlot(self):
        self.l.set_xdata(self.x)
        self.l.set_ydata(self.yvals)
        spline = inter.InterpolatedUnivariateSpline (self.x, self.yvals)
        self.m.set_ydata(spline(self.X))
        # redraw canvas while idle
        self.fig.canvas.draw_idle()

    def reset(self, event):
        #reset the values
        yvals = self.func(self.x)
        spline = inter.InterpolatedUnivariateSpline (self.x, yvals)
        self.l.set_ydata(yvals)
        self.m.set_ydata(spline(self.X))
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
        yr = np.reshape(self.yvals,(np.shape(self.yvals)[0],1))
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
        self.yvals[self.pind] = event.ydata 
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
