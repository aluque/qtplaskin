import sys
import os
import time
import numpy as np


# Python Qt5 bindings for GUI objects
try:
    from PyQt5 import QtGui, QtWidgets
except ImportError:  # conda install pyqt
    from pyqt import QtGui, QtWidgets

# import the Qt5Agg FigureCanvas object, that binds Figure to
# Qt5Agg backend. It also inherits from QWidget
from matplotlib.backends.backend_qt5agg \
    import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg \
    import NavigationToolbar2QT as NavigationToolbar

# Matplotlib Figure object
import matplotlib.pyplot as plt
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
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)

        # notify the system of updated policy
        FigureCanvas.updateGeometry(self)
#
# class QtToolbar(NavigationToolbar):
#
#    def __init__(self, plotCanvas, parent):
#        NavigationToolbar.__init__(self, plotCanvas, parent)
#        self._home = self.home
#        self.home = self.new_home
#
#    def new_home(self, *args, **kwargs):
#        ''' New navigation home button with forced reset
#        http://stackoverflow.com/questions/14896580/matplotlib-hooking-in-to-home-back-forward-button-events'''
#        widget = self.parent
#        #print('home!')
#        #widget.update(rescale=True)
#        widget.reset_lims()
#        raise
#        self._home(self, *args, **kwargs)

# Thanks Laurent
# http://groups.google.com/group/pyinstaller/browse_thread/thread/834bea87c7afcdff?pli=1


class VMToolbar(NavigationToolbar):

    def __init__(self, plotCanvas, parent):
        NavigationToolbar.__init__(self, plotCanvas, parent)

    def _icon(self, name, *args, **kwargs):
        # dirty hack to use exclusively .png and thus avoid .svg usage
        # because .exe generation is problematic with .svg
        name = name.replace('.svg', '.png')
        return QtGui.QIcon(os.path.join(self.basedir, name))


class MplWidget(QtWidgets.QWidget):
    """Widget defined in Qt Designer"""

    def handle_home(self, event):
        self.reset_lims()
        self.draw()

    def __init__(self, parent=None):
        # initialization of Qt MainWindow widget
        QtWidgets.QWidget.__init__(self, parent)

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
        self.vbl = QtWidgets.QVBoxLayout()

        # add mpl widget and toolbar to vertical box
        self.vbl.addWidget(self.canvas)
        self.vbl.addWidget(self.ntb)

        palette = self.ntb.palette()
        self.canvas.fig.set_facecolor([x / 255. for x in
                                       palette.window().color().getRgb()])

#        self.canvas.mpl_connect('home_event', self.handle_home)

        # Connect Home Button with New Home functions
        self.ntb.actions()[0].triggered.connect(self.handle_home)

        # set the layout to th vertical box
        self.setLayout(self.vbl)

        self.clear_data()

    def get_gui(self):
        gui = self.parent().parent().parent().parent().parent()
        return gui


#    def get_npoints_on_screen(self, line_index=0):
#        '''
#        Input
#        -----
#        ax: matplotlib axe
#        l: line number
#        '''
#
#        if ax is None:
#            ax=plt.gca()
#        line = ax.get_lines()[line_index]
#
#
#        xmin, xmax = ax.xaxis.get_view_interval()
#        ymin, ymax = ax.yaxis.get_view_interval()
#
#        xdata = line.get_xdata()
#        ydata = line.get_ydata()
#
#        return sum((xdata>=xmin) & (xdata<=xmax) & (ydata>=ymin) & (ydata<=ymax))

    def reset_lims(self):
        #    ax = plt.gca()

        #        print('called reset_lims()')

        for ax in self.axes:
            lines = ax.get_lines()

            xmin = min([min(l.get_xdata(), default=None)
                       for l in lines], default=None)
            xmax = max([max(l.get_xdata(), default=None)
                       for l in lines], default=None)
            ymin = min([min(l.get_ydata(), default=None)
                       for l in lines], default=None)
            ymax = max([max(l.get_ydata(), default=None)
                       for l in lines], default=None)

#            print('Reset xlim',xmin,xmax)
#            print('Reset ylim',ymin,ymax)

            if ax.get_xscale() == 'log':
                xmin = 1e-11

            ax.set_xlim(left=xmin, right=xmax)
            ax.set_ylim(bottom=ymin, top=ymax)
            ax.autoscale(True, tight=False)
            plt.draw()

    def clear_data(self):
        # This is for the correct export of data.
        self.xdata = None
        self.ydata = []
        self.labels = []

    def add_axes(self, *args, **kwargs):
        """ Adds axes to this widget.  """
        ax = self.fig.add_axes(*args, **kwargs)
        ax.cursorlines = None    # used to store lines to display cursors
#
#        # Update lines
#        ax.callbacks.connect('xlim_changed', on_xlims_change)
#        ax.callbacks.connect('ylim_changed', on_ylims_change)

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
        # Re-add field-on if needed
        self.show_field_on_region()

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
        d = np.c_[tuple([self.xdata, ] + self.ydata)]

        with open(fname, "w") as fout:
            fout.write("# Input: %s\n" % location)
            fout.write("# Date: %s\n" % time.ctime())
            fout.write("# Columns:\n")
            for c, label in enumerate(self.labels):
                fout.write("#    %-.3d:  %s\n" % (c, label))

            np.savetxt(fout, d)

    def show_field_on_region(self):
        ''' 
        '''
        gui = self.get_gui()
        if gui.actionShowField.isChecked():
            field = gui.data.get_cond('Reduced field')
            b = np.array(field > field[0], dtype=np.int64)
            pulse_start = np.argwhere(np.diff(b) == 1)
            pulse_stop = np.argwhere(np.diff(b) == -1)
            if len(pulse_stop) < len(pulse_start):
                pulse_stop = np.vstack((pulse_stop, len(field)-1))
            for istart, istop in zip(pulse_start.flatten(), pulse_stop.flatten()):
                for ax in self.axes:
                    ax.axvspan(gui.data.t[istart], gui.data.t[istop],
                               alpha=0.05, color='b')
                    # Reset y-axis to cope with bug when old yrange was larger
                    # than the new one (see https://github.com/erwanp/qtplaskin/issues/18)
                    ax.relim()
                    ax.autoscale_view(scalex=False, scaley=True)


class ConditionsPlotWidget(MplWidget):

    def init_axes(self):

        # Synchronize timescale with first Ax (or make it the first Ax)
        sharex = None
        gui = self.get_gui()
        if gui.firstAx is not None:
            sharex = gui.firstAx

        self.condAx = self.add_axes([0.1, 0.1, 0.85, 0.85], sharex=sharex)

        if gui.firstAx is None:  # register this Widget as the Ax to be sync with
            gui.firstAx = self.condAx
            self.reset_lims()

        # Add grid
        self.grid()

        # Show field-on region
        self.show_field_on_region()

#        self.condAx.set_ylim(ymin=self.condAx.get_ylim()[0])


class DensityPlotWidget(MplWidget):

    def init_axes(self):

        # Synchronize timescale with first Ax (or make it the first Ax)
        sharex = None
        gui = self.get_gui()
        if gui.firstAx is not None:
            sharex = gui.firstAx

        self.densAx = self.add_axes([0.085, 0.1, 0.7, 0.85], sharex=sharex)

        if gui.firstAx is None:  # register this Widget as the Ax to be sync with
            gui.firstAx = self.densAx
            self.reset_lims()

        # Add grid
        self.grid()

        # Show field-on region
        self.show_field_on_region()


class SourcePlotWidget(MplWidget):
    ''' sensitivity analysis '''

    def init_axes(self):

        # Synchronize timescale with first Ax (or make it the first Ax)
        sharex = None
        gui = self.get_gui()
        if gui.firstAx is not None:
            sharex = gui.firstAx

        self.removalAx = self.add_axes([0.085, 0.1, 0.65, 0.4], sharex=sharex)
        self.creationAx = self.add_axes(
            [0.085, 0.58, 0.65, 0.4], sharex=self.removalAx)

        if gui.firstAx is None:  # register this Widget as the Ax to be sync with
            gui.firstAx = self.removalAx
            self.reset_lims()

        # Add grid
        self.grid()

        # Show field-on region
        self.show_field_on_region()


class RatePlotWidget(MplWidget):

    def init_axes(self):

        # Synchronize timescale with first Ax (or make it the first Ax)
        sharex = None
        gui = self.get_gui()
        if gui.firstAx is not None:
            sharex = gui.firstAx

        self.rateAx = self.add_axes([0.085, 0.1, 0.65, 0.85], sharex=sharex)

        if gui.firstAx is None:  # register this Widget as the Ax to be sync with
            gui.firstAx = self.rateAx
            self.reset_lims()

        # Add grid
        self.grid()

        # Show field-on region
        self.show_field_on_region()
