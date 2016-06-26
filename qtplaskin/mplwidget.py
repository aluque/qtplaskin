import sys
import os
import time
import numpy as np


# Python Qt4 bindings for GUI objects
from PyQt4 import QtGui

# import the Qt4Agg FigureCanvas object, that binds Figure to
# Qt4Agg backend. It also inherits from QWidget
from matplotlib.backends.backend_qt4agg \
    import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg \
    import NavigationToolbar2QT as NavigationToolbar

# Matplotlib Figure object
from matplotlib.figure import Figure


class MplCanvas(FigureCanvas):
    """Class to represent the FigureCanvas widget"""
    def __init__(self, widget):
        # setup Matplotlib Figure and Axis
        self.fig = Figure()
        self.axes = []

        # initialization of the canvas
        FigureCanvas.__init__(self, self.fig)

        # we define the widget as expandable
        FigureCanvas.setSizePolicy(self,
                                   QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)

        # notify the system of updated policy
        FigureCanvas.updateGeometry(self)

# Thanks Laurent
# http://groups.google.com/group/pyinstaller/browse_thread/thread/834bea87c7afcdff?pli=1
class VMToolbar(NavigationToolbar): 
    def __init__(self, plotCanvas, parent): 
        NavigationToolbar.__init__(self, plotCanvas, parent) 

    def _icon(self, name): 
        # dirty hack to use exclusively .png and thus avoid .svg usage 
        # because .exe generation is problematic with .svg 
        name = name.replace('.svg','.png') 
        return QtGui.QIcon(os.path.join(self.basedir, name)) 



class MplWidget(QtGui.QWidget):
    """Widget defined in Qt Designer"""
    def __init__(self, parent = None):
        # initialization of Qt MainWindow widget
        QtGui.QWidget.__init__(self, parent)

        
        # set the canvas to the Matplotlib widget
        self.canvas = MplCanvas(self)

        # Inherit fig and axes from the canvas to avoid indirections
        self.axes = self.canvas.axes
        self.fig = self.canvas.fig

        # When we pack the application with py2exe or py2app .svg graphics
        # do not work because the require qt4 plugins that are not properly
        # packaged.  So we use this woraround, effective at all times in windows
        # and macosx.  
        if not sys.platform in ["win32", "win64", "darwin"]:
            self.ntb = NavigationToolbar(self.canvas, self)
        else:
            self.ntb = VMToolbar(self.canvas, self)
            
        # create a vertical box layout
        self.vbl = QtGui.QVBoxLayout()

        # add mpl widget and toolbar to vertical box
        self.vbl.addWidget(self.canvas)
        self.vbl.addWidget(self.ntb)

        palette = self.ntb.palette()
        self.canvas.fig.set_facecolor([x / 255. for x in
                                       palette.window().color().getRgb()])

        # set the layout to th vertical box
        self.setLayout(self.vbl)

        self.clear_data()
        
        self.cursorlines = None  # use to store lines to display cursors

    def clear_data(self):
        # This is for the correct export of data.
        self.xdata = None
        self.ydata = []
        self.labels = []

    def add_axes(self, *args, **kwargs):
        """ Adds axes to this widget.  """
        ax = self.fig.add_axes(*args, **kwargs)
        self.axes.append(ax)

        return ax

    def grid(self):
        for ax in self.axes:
            ax.grid(ls='-', lw=0.5, c='#cccccc', zorder=-10)


    def draw(self):
        self.canvas.draw()


    def clear(self):
        for ax in self.axes:
            ax.clear()

        self.grid()
        self.draw()
        self.clear_data()
        
    def set_scales(self, xscale=None, yscale=None, redraw=False):
        for ax in self.axes:
            if xscale is not None:
                ax.set_xscale(xscale)

            if yscale is not None:
                ax.set_yscale(yscale)

        if redraw:
            self.draw()

    def add_data(self, x, y, label):
        if self.xdata is None:
            self.xdata = x
            self.labels.append('Time')

        self.ydata.append(y)
        self.labels.append(label)

    def savedata(self, fname, location):
        d = np.c_[tuple([self.xdata,] + self.ydata)]
        
        with open(fname, "w") as fout:
            fout.write("# Input: %s\n" % location)
            fout.write("# Date: %s\n" % time.ctime())
            fout.write("# Columns:\n")
            for c, label in enumerate(self.labels):
                fout.write("#    %-.3d:  %s\n" % (c, label))
                
            np.savetxt(fout, d)
        

class ConditionsPlotWidget(MplWidget):
    def init_axes(self):
        self.add_axes([0.1, 0.1, 0.85, 0.85])
        self.grid()

class DensityPlotWidget(MplWidget):
    def init_axes(self):
        self.add_axes([0.085, 0.1, 0.7, 0.85])
        self.grid()


class SourcePlotWidget(MplWidget):
    ''' sensitivity analysis '''
    
    def init_axes(self):
        self.removalAx = self.add_axes([0.085, 0.1, 0.65, 0.4])
        self.creationAx = self.add_axes([0.085, 0.58, 0.65, 0.4],sharex=self.removalAx)
        self.grid()

class RatePlotWidget(MplWidget):
    def init_axes(self):
        self.add_axes([0.085, 0.1, 0.65, 0.85])
        self.grid()
    
