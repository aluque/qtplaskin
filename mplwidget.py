import numpy as np

# Python Qt4 bindings for GUI objects
from PyQt4 import QtGui

# import the Qt4Agg FigureCanvas object, that binds Figure to
# Qt4Agg backend. It also inherits from QWidget
from matplotlib.backends.backend_qt4agg \
    import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg \
    import NavigationToolbar2QTAgg as NavigationToolbar

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
        
        self.ntb = NavigationToolbar(self.canvas, self)

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


    def add_axes(self, *args, **kwargs):
        """ Adds axes to this widget.  """
        ax = self.fig.add_axes(*args, **kwargs)
        self.axes.append(ax)

        return ax


    def draw(self):
        self.canvas.draw()


    def clear(self):
        for ax in self.axes:
            ax.clear()
            
    def set_scales(self, xscale=None, yscale=None, redraw=False):
        for ax in self.axes:
            if xscale is not None:
                ax.set_xscale(xscale)

            if yscale is not None:
                ax.set_yscale(yscale)

        if redraw:
            self.draw()
            
    def savedata(self, fname):
        xdata = None
        ydata = []
        labels = ['Time']

        for ax in self.axes:
            for line in ax.get_lines():
                # We have to assume that all x data is the same.  Else,
                # everything gets much more complicated
                if xdata is None:
                    xdata = np.array(line.get_xdata())[:, np.newaxis]
        
                ydata.append(np.array(line.get_ydata())[:, np.newaxis])
                labels.append(line.get_label())

        d = np.concatenate(tuple([xdata,] + ydata), axis=1)
        
        with open(fname, "w") as fout:
            fout.write("# Columns:\n")
            for c, label in enumerate(labels):
                fout.write("# %-.3d:  %s\n" % (c, label))
                
            np.savetxt(fout, d)
        
        
class ConditionsPlotWidget(MplWidget):
    def init_axes(self):
        self.add_axes([0.1, 0.1, 0.85, 0.85])
    

class DensityPlotWidget(MplWidget):
    def init_axes(self):
        self.add_axes([0.1, 0.1, 0.7, 0.85])


class SourcePlotWidget(MplWidget):
    def init_axes(self):
        self.removalAx = self.add_axes([0.1, 0.1, 0.65, 0.4])
        self.creationAx = self.add_axes([0.1, 0.58, 0.65, 0.4])

class RatePlotWidget(MplWidget):
    def init_axes(self):
        self.add_axes([0.1, 0.1, 0.65, 0.85])
    
