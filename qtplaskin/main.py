#! /usr/bin/env python

"""
Main module

Use
------
    run it from the qtplaskin script under script/
    
Or from Python with:
    
    import qtplaskin
    qtplaskin.main.load([FOLDER])

"""


from __future__ import print_function, division, unicode_literals, absolute_import
from builtins import range

import sys
import os
from itertools import cycle
import traceback

try:
    from PyQt5 import QtGui, QtWidgets
except ImportError:
    raise ImportError('Warning. Qtplaskin was upgraded to PyQt5. You need to' +
                      ' install PyQt5.')

# Qt5 bindings for core Qt functionalities (non-GUI)
from PyQt5 import QtCore

# Python Qt5 bindings for GUI objects
from PyQt5.QtCore import Qt

from numpy import (array, zeros, nanmax, nanmin, where, isfinite,
                   argsort, r_, isreal, logical_and, float64, diff)

# import the MainWindow widget from the converted .ui files
try:
    from .mainwindow import Ui_MainWindow
    from .modeldata import HDF5Data, RealtimeData, DirectoryData, FastDirData, OldDirectoryData
    from .timeformatter import TimeFormatter
except:
    from qtplaskin.mainwindow import Ui_MainWindow
    from qtplaskin.modeldata import HDF5Data, RealtimeData, DirectoryData, FastDirData, OldDirectoryData
    from qtplaskin.timeformatter import TimeFormatter

#import publib

try:
    import mpldatacursor
    CURSOR_AVAIL = True
except:
    CURSOR_AVAIL = False

COLOR_SERIES = ["#5555ff", "#ff5555", "#909090",
                "#ff55ff", "#008800", "#8d0ade",
                "#33bbcc", "#000000", "#444400",
                "#7777ff", "#77ff77"]
LINE_WIDTH = 1.7

# We do not plot densities or rates below these thresholds
DENS_THRESHOLD = 1e-10
RATE_THRESHOLD = 1e-20

CONDITIONS_PRETTY_NAMES = {
    'gas_temperature': "Gas temperature [K]",
    'Tgas_K': "Gas temperature [K]",
    'reduced_frequency': r"Reduced frequency cm$^\mathdefault{3}$s$^\mathdefault{-1}$",
    'reduced_field': "Reduced field E/N [Td]",
    'E/N_Td': "Reduced field E/N [Td]",
    'elec_temperature': "Electron temperature [K]",
    'Telec_K': "Electron temperature [K]",
    'elec_drift_velocity': "Electron drift velocity [cm/s]",
    'elec_diff_coeff': r"Electron diffusion coeff. [cm$^\mathdefault{2}$s$^\mathdefault{-1}$]",
    'elec_frequency_n': r"Electron reduced colission freq. [cm$^\mathdefault{3}$s$^\mathdefault{-1}$]",
    'elec_power_n': r"Electron reduced power [eV cm$^\mathdefault{3}$s$^\mathdefault{-1}$]",
    'elec_power_elastic_n': r"Electron reduced elastic power [eV cm$^\mathdefault{3}$s$^\mathdefault{-1}$]",
    'elec_power_inelastic_n': r"Electron reduced inelastic power [eV cm$^\mathdefault{3}$s$^\mathdefault{-1}$]"}


class DesignerMainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    """Customization for Qt Designer created window"""

    def __init__(self, parent=None):
        # initialization of the superclass
        super(DesignerMainWindow, self).__init__(parent)
        # setup the GUI --> function generated by pyuic4
        self.setupUi(self)

        # In some lists we can select more than one item
        self.speciesList.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection)
        self.reactList.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection)
        # @EP: also allow to select several conditions (useful for User defined data)
        self.condList.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection)

        for w in [self.reactList, self.speciesList, self.speciesSourceList,
                  self.condList]:
            w.horizontalHeader().setVisible(True)

        self.plot_widgets = [self.condWidget,
                             self.densWidget,
                             self.reactWidget,
                             self.sourceWidget]
        self.cursors = []

        self.update_timer = QtCore.QTimer()
        self.latest_dir = "."

        # connect the signals with the slots
        self.condButton.clicked.connect(self.update_cond_graph)
        self.plotButton.clicked.connect(self.update_spec_graph)
        self.sourceButton.clicked.connect(self.update_source_graph)
        self.reactButton.clicked.connect(self.update_react_graph)

        self.actionOpen.triggered.connect(self.select_file)
        self.actionStart_a_simulation.triggered.connect(
            self.start_a_simulation)
        self.actionImport_from_directory.triggered.connect(
            self.import_from_directory)
        self.actionUpdate.triggered.connect(self.data_update)
        self.actionExport_data.triggered.connect(self.export_data)
        self.actionSave.triggered.connect(self.save_to_file)
        self.actionQuit.triggered.connect(QtWidgets.qApp.quit)

    def print_status(self, string):
        ''' Print to status bar
        Useful for debugging'''
        self.statusbar.showMessage(string)

    def datacursor(self, widget, unit=None, labname='Label'):
        ''' Plot datacursors (useful when the number of lines gets confusing)

        Parameters
        ----------

        unit and labname: 
            to customize the info box'''

        # Clean previous cursors  (prevent overlaps with remaining cursors)
        while len(self.cursors) > 0:
            dc = self.cursors.pop()
            dc.hide().disable()

        if self.actionDatacursor.isChecked() and CURSOR_AVAIL:

            def formatter(x=None, y=None, z=None, s=None, label=None, **kwargs):

                _ = kwargs['event'].mouseevent.inaxes

                output = []
                # output.append(u't: {0:0.3e} s'.format(x))
                output.append(TimeFormatter().simple_function(x, 0, number_after_decimals=3))
                output.append(u'y: {0:0.3e} {1}'.format(y, unit))

                for key, val in zip(['z', 's'], [z, s]):
                    if val is not None:
                        try:
                            output.append(
                                u'{key}: {val:0.3e}'.format(key=key, val=val))
                        except ValueError:
                            # X & Y will be strings at this point.
                            # For masked arrays, etc, "z" and s values may be a
                            # string
                            output.append(
                                u'{key}: {val}'.format(key=key, val=val))

                # label may be None or an empty string (for an un-labeled AxesImage)...
                # Un-labeled Line2D's will have labels that start with an
                # underscore
                if label and not label.startswith('_'):
                    output.append(u'{0}: {1}'.format(labname, label))

                if kwargs.get(u'point_label', None) is not None:
                    output.append(
                        u'Point: ' + u', '.join(kwargs['point_label']))

                return u'\n'.join(output)

            for ax in widget.axes:
                if not ax.cursorlines is None:
                    self.cursors.append(mpldatacursor.datacursor(
                        ax.cursorlines, hover=True, size=10, color='k',
                        bbox=dict(fc='white', alpha=0.9),
                        formatter=formatter))
        return None

    # Drag'n'Drop.  Implemented by Marc Foletto.
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    # Drag'n'Drop.
    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                fname = url.toLocalFile()
                self.import_file_or_dir(fname)

            event.acceptProposedAction()

    # Chose if drop is a file or a directory
    def import_file_or_dir(self, path):
        if os.path.exists(path):
            if os.path.isdir(path):
                self._import_from_directory(path)
            else:
                # Let us allow the user to import files with any extension:
                # if they are not in hdf5 format and exception will be raised
                # anyhow.
                self.load_h5file(path)

    def set_location(self, location):
        """ Sets the opened location. """
        self.setWindowTitle("%s - QtPlaskin" % location)
        self.location = location

    @property
    def xscale(self):
        if self.actionLog_scale_in_time.isChecked():
            return 'log'
        else:
            return 'linear'

    def update_cond_graph(self):
        """Updates the graph with conditions

        Attributes
        ----------

        autoscale
            will keep timescale from last ax unless it's the first plot. Default None.

        """
#
#        try:
#            condition = list(iter_2_selected(self.condList))[0][0]
#        except AttributeError:
#            return

        # Get current range
        former_xrange = None
        if self.firstAx is not None:
            former_xrange = self.firstAx.get_xlim()

        # clear the Axes
        if not self.condWidget.axes:
            self.condWidget.init_axes()
        else:
            self.condWidget.clear()

        QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))

        citer = cycle(COLOR_SERIES)
        lines = []
        label = ''
        # Loop over all selected conditions
        for item in iter_2_selected(self.condList):
            name = item[1]
            y = array(self.data.condition(item[0]), dtype=float64)
            condition_name = self.data.conditions[item[0] - 1]

            flt = logical_and(isreal(y), isfinite(y))
            label = CONDITIONS_PRETTY_NAMES.get(condition_name, condition_name)
            lines.append(self.condWidget.axes[0].plot(self.data.t[flt], y[flt], lw=LINE_WIDTH,
                                                      label=name,  # scalex=False,
                                                      zorder=10,
                                                      c=next(citer))[0])

        self.condWidget.condAx.cursorlines = lines
        self.datacursor(self.condWidget)

        self.condWidget.set_scales(yscale='linear', xscale=self.xscale)
        self.condWidget.axes[0].set_xlabel("time")
        self.condWidget.axes[0].set_ylabel(label)

        # Reset former xrange
        if former_xrange is not None:
            self.condWidget.axes[0].set_xlim(former_xrange)
        else:  # autoscale to full range
            self.condWidget.axes[0].autoscale(True, axis='x')

        self.condWidget.axes[0].xaxis.set_major_formatter(TimeFormatter().simple_function)

        # force an image redraw
        self.condWidget.draw()

        self.condWidget.add_data(self.data.t, y, label)
        QtWidgets.QApplication.restoreOverrideCursor()

    def update_spec_graph(self, autoscale=None):
        """Updates the graph with densities

        Attributes
        ----------

        autoscale
            will keep timescale from last ax unless it's the first plot. Default None.
        """

        # Get current range
        former_xrange = None
        if self.firstAx is not None:
            former_xrange = self.firstAx.get_xlim()

        # clear the Axes
        if not self.speciesList.selectedItems():
            return

        if not self.densWidget.axes:
            self.densWidget.init_axes()
        else:
            self.densWidget.clear()

        QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))
        self.data.flush()

        citer = cycle(COLOR_SERIES)
        lines = []
        # Loop over all selected species
        for item in iter_2_selected(self.speciesList):
            name = item[1]
            dens = self.data.density(item[0])
            flt = dens > DENS_THRESHOLD
            lines.append(self.densWidget.axes[0].plot(self.data.t[flt], dens[flt],
                                                      lw=LINE_WIDTH, scalex=False,
                                                      c=next(citer), label=name,
                                                      zorder=10)[0])
            self.densWidget.add_data(self.data.t, dens, name)

        self.densWidget.densAx.cursorlines = lines
        self.datacursor(self.densWidget, unit='cm-3', labname='Spec.')

        self.densWidget.set_scales(yscale='log', xscale=self.xscale)
        self.densWidget.axes[0].set_xlabel("time")
        self.densWidget.axes[0].set_ylabel(r"Density [cm$^\mathdefault{-3}$]")
        self.densWidget.axes[0].legend(loc=(1.05, 0.0), prop=dict(size=11))

        # Reset former xrange
        if former_xrange is not None:
            self.densWidget.axes[0].set_xlim(former_xrange)
        else:  # autoscale to full range
            self.densWidget.axes[0].autoscale(True, axis='x')

        self.densWidget.axes[0].xaxis.set_major_formatter(TimeFormatter().simple_function)

        # force an image redraw
        self.densWidget.draw()

        QtWidgets.QApplication.restoreOverrideCursor()

    def update_source_graph(self, autoscale=None):
        """Updates the graph with sources rates

        Attributes
        ----------

        autoscale
            will keep timescale from last ax unless it's the first plot. Default None.
        """
        try:
            species = list(iter_2_selected(self.speciesSourceList))[0]
        except AttributeError:
            return

        # Get current range
        former_xrange = None
        if self.firstAx is not None:
            former_xrange = self.firstAx.get_xlim()

        # clear the Axes
        if not self.sourceWidget.axes:
            self.sourceWidget.init_axes()
        else:
            self.sourceWidget.clear()

        QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))

        filters = {0: (0.1, -1),
                   1: (0.01, -1),
                   2: (0.001, -1),
                   3: (1e-4, -1),
                   4: (0.0, -1)}

        delta, max_rates = filters[self.Combo_filter.currentIndex()]

        icreation, idestruct = select_rates(
            self.data, species[0], delta, max_rates=max_rates)

        citer = cycle(COLOR_SERIES)
        lines = []
        for i in icreation:
            name = self.data.reactions[i-1]
            rate = array(self.data.rate(i))
            flt = rate > RATE_THRESHOLD
            label = "[%d] %s" % (i, name)

            lines.append(self.sourceWidget.creationAx.plot(self.data.t[flt],
                                                           rate[flt],
                                                           c=next(citer),
                                                           lw=LINE_WIDTH,
                                                           label=label,
                                                           scalex=False,
                                                           zorder=10)[0])

            self.sourceWidget.add_data(self.data.t, rate, label)
        self.sourceWidget.creationAx.cursorlines = lines

        citer = cycle(COLOR_SERIES)
        lines = []
        for i in idestruct:
            name = self.data.reactions[i-1]
            rate = array(self.data.rate(i))
            flt = rate > RATE_THRESHOLD
            label = "[%d] %s" % (i, name)

            lines.append(self.sourceWidget.removalAx.plot(self.data.t[flt],
                                                          rate[flt],
                                                          c=next(citer),
                                                          lw=LINE_WIDTH,
                                                          label=label,
                                                          scalex=False,
                                                          zorder=10)[0])

            self.sourceWidget.add_data(self.data.t, rate, "- " + label)
        self.sourceWidget.removalAx.cursorlines = lines

        self.datacursor(self.sourceWidget, unit='cm-3/s', labname='Reac.')

        self.sourceWidget.creationAx.set_ylabel(
            r"Production [cm$^\mathdefault{-3}$s$^\mathdefault{-1}$]")
        self.sourceWidget.creationAx.legend(loc=(1.05, 0.0),
                                            prop=dict(size=9))

        self.sourceWidget.removalAx.set_ylabel(
            r"Losses [cm$^\mathdefault{-3}$s$^\mathdefault{-1}$]")

        self.sourceWidget.removalAx.set_xlabel("time")

        self.sourceWidget.removalAx.legend(loc=(1.05, 0.0),
                                           prop=dict(size=9))

        self.sourceWidget.set_scales(yscale='log', xscale=self.xscale)

        # Reset former xrange
        if former_xrange is not None:
            if former_xrange[0] <= 0 and self.xscale == 'log':
                former_xrange = (1e-11, former_xrange[1])
            self.sourceWidget.creationAx.set_xlim(former_xrange)
#            self.sourceWidget.removalAx.set_xlim(former_xrange)  # synchronized already
        else:  # autoscale to full range
            self.sourceWidget.creationAx.autoscale(True, axis='x')

        # self.sourceWidget.creationAx.xaxis.set_major_formatter(TimeFormatter())
        # self.sourceWidget.removalAx.xaxis.set_major_formatter(TimeFormatter())

        self.sourceWidget.creationAx.xaxis.set_major_formatter(
            TimeFormatter().simple_function)
        self.sourceWidget.removalAx.xaxis.set_major_formatter(
            TimeFormatter().simple_function)

        # force an image redraw
        self.sourceWidget.draw()

        QtWidgets.QApplication.restoreOverrideCursor()

    def update_react_graph(self, autoscale=None):
        """Updates the graph with reaction rates

        Attributes
        ----------

        autoscale
            will keep timescale from last ax unless it's the first plot. Default None.
        """
        if not self.reactList.selectedItems():
            return

        # Get current range
        former_xrange = None
        if self.firstAx is not None:
            former_xrange = self.firstAx.get_xlim()

        # clear the Axes
        if not self.reactWidget.axes:
            self.reactWidget.init_axes()
        else:
            self.reactWidget.clear()

        QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))

        citer = cycle(COLOR_SERIES)
        lines = []
        for item in iter_2_selected(self.reactList):
            name = item[1]
            rate = array(self.data.rate(item[0]))

            flt = rate > RATE_THRESHOLD
            label = "[%d] %s" % (item[0], name)

            lines.append(self.reactWidget.axes[0].plot(self.data.t[flt], rate[flt],
                                                       c=next(citer),
                                                       lw=LINE_WIDTH,
                                                       label=label,
                                                       zorder=10)[0])
            self.reactWidget.add_data(self.data.t, rate, label)

        self.reactWidget.rateAx.cursorlines = lines
        self.datacursor(self.reactWidget, unit='cm-3/s', labname='Reaction')

        self.reactWidget.set_scales(yscale='log', xscale=self.xscale)

        self.reactWidget.axes[0].set_xlabel("time")
        self.reactWidget.axes[0].set_ylabel(
            r"Rate [cm$^\mathdefault{-3}$s$^\mathdefault{-1}$]")
        self.reactWidget.axes[0].legend(loc=(1.025, 0.0),
                                        prop=dict(size=8))

        # Reset former xrange
        if former_xrange is not None:
            self.reactWidget.axes[0].set_xlim(former_xrange)

        self.reactWidget.axes[0].xaxis.set_major_formatter(TimeFormatter().simple_function)

        # force an image redraw
        self.reactWidget.draw()

        QtWidgets.QApplication.restoreOverrideCursor()

    def select_file(self):
        """opens a file select dialog"""
        # open the dialog and get the selected file
        file, *_rest = QtWidgets.QFileDialog.getOpenFileName(self, "Open data file",
                                                             ".",
                                                             "HDF5 files (*.h5 *.hdf5);;"
                                                             "All files (*)")
        # if a file is selected
        if file:
            try:
                self.load_h5file(file)
                self.set_location(file)

                self.update_lists()
                self.clear()

            except IOError as e:
                QtWidgets.QErrorMessage(self).showMessage(
                    "Failed to open file.  Incorrect format? <%s>" % e)

    def start_a_simulation(self):
        self.data = RealtimeData('fpr_1', 'init_species.dat',
                                 'field_constant.tsv',
                                 max_dt=10e-3)
        self.update_lists()

    def import_from_directory(self):
        fname = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Import data from directory",
            self.latest_dir, QtWidgets.QFileDialog.ShowDirsOnly)

        self._import_from_directory(fname)
        self.latest_dir = fname

    def _import_from_directory(self, fname):
        try:
            try:
                self.data = FastDirData(fname)
            except (MemoryError, ValueError, TypeError) as e:
                em = QtWidgets.QErrorMessage(self)
                em.setModal(True)
                em.setWindowTitle("QtPlaskin: Error")
                em.showMessage('''
                    Failed to open directory. <br>
                    {}: {}. <br>
                    Now trying the old (slower) way.
                    '''.format(type(e).__name__, str(e)))
                em.exec_()
                try:
                    self.data = DirectoryData(fname)
                except IOError as e:
                    em = QtWidgets.QErrorMessage(self)
                    em.setModal(True)
                    em.showMessage(
                        ("Failed to open directory (%s).\n" % str(e))
                        + "I will try now to import files in deprecated format.")
                    # If we do not call exec_ here, two dialogs may appear at
                    # the same time, confusing the user.
                    em.exec_()
                    self.data = OldDirectoryData(fname)
            except IOError as e:
                em = QtWidgets.QErrorMessage(self)
                em.setModal(True)
                em.showMessage(
                    ("Failed to open directory (%s).\n" % str(e))
                    + "I will try now to import files in deprecated format.")
                # If we do not call exec_ here, two dialogs may appear at
                # the same time, confusing the user.
                em.exec_()
                self.data = OldDirectoryData(fname)

            self.set_location(fname)
            self.update_lists()
            self.clear()
        except IOError as e:
            em = QtWidgets.QErrorMessage(self)
            em.setModal(True)
            em.exec_()
            em.showMessage(
                "Failed to open directory (%s).\n" % str(e))

    def data_update(self):
        try:
            self.data.update()
        except AttributeError:
            em = QtWidgets.QErrorMessage(self)
            em.setModal(True)
            em.showMessage("No data to update! Load data first.")
            return

        if self.condWidget.axes:
            self.update_cond_graph()
        if self.densWidget.axes:
            self.update_spec_graph()
        if self.sourceWidget.axes:
            self.update_source_graph()
        if self.reactWidget.axes:
            self.update_react_graph()

    def save_to_file(self):
        """opens a file select dialog"""
        # open the dialog and get the selected file
        fname, *_rest = QtWidgets.QFileDialog.getSaveFileName(self, "Save to file",
                                                              ".",
                                                              "HDF5 files (*.h5 *.hdf5);;"
                                                              "All files (*)")

        # if a file is selected
        if fname:
            self.data.save(fname)

    def export_data(self):
        """opens a file select dialog"""
        # open the dialog and get the selected file
        fname, *_rest = QtWidgets.QFileDialog.getSaveFileName(self, "Export data to file",
                                                              ".",
                                                              "TSV files (*.tsv);;"
                                                              "TXT files (*.txt);;"
                                                              "DAT files (*.dat);;"
                                                              "All files (*)")

        # if a file is selected
        if fname:
            fname = fname
            self.plot_widgets[self.tabWidget.currentIndex()]\
                .savedata(fname, self.location)

    def action_set_logtime(self):
        for w in self.plot_widgets:
            w.set_scales(xscale=self.xscale, redraw=True)

    def action_set_datacursor(self):
        """ 
        if cancel: delete all current datacursors.
        if added: show datacursor """
        if self.actionDatacursor.isChecked():
            for w in self.plot_widgets:
                self.datacursor(w)
        else:
            while len(self.cursors) > 0:
                dc = self.cursors.pop()
                dc.hide().disable()

    def load_h5file(self, file):
        self.data = HDF5Data(file)
        self.update_lists()
        self.clear()

    def update_lists(self):

        #self.species = sorted(self.data.species)
        #self.reactions = sorted(self.data.reactions)
        #self.conditions = sorted(self.data.conditions)

        def _populate(qtable, list, pretty_names={}):
            for _ in range(qtable.rowCount()):
                qtable.removeRow(0)

            for n, item in enumerate(list):
                row = qtable.rowCount()
                qtable.insertRow(row)
                # The + 1 is to move to the FORTRAN/ZdPlaskin convention
                nitem = QtWidgets.QTableWidgetItem(u'%4d' % (n + 1))
                nitem.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                nitem.setForeground(QtGui.QColor(160, 160, 160))
                qtable.setItem(row, 0, nitem)

                showed_item = pretty_names.get(item, item)
                sitem = QtWidgets.QTableWidgetItem(showed_item)
                sitem.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                qtable.setItem(row, 1, sitem)

        _populate(self.speciesList, self.data.species)
        _populate(self.speciesSourceList, self.data.species)
        _populate(self.reactList, self.data.reactions)
        _populate(self.condList, self.data.conditions,
                  pretty_names=CONDITIONS_PRETTY_NAMES)

    def clear(self):
        for w in self.plot_widgets:
            w.clear()

    def parse_file(self, filename):
        pass


def filter_rates(f, delta, max_rates=4, min_rates=0):
    fmax = nanmax(f, axis=1)

    asort = argsort(-fmax)
    n = len(asort)

    # We always select at least the highest min_rates.
    highest = asort[:min_rates]

    # if n < max_rates:
    #    return highest

    # From the rest, we select those larger than delta, but not more
    # than max_rates
    p = asort[min_rates:max_rates]
    rest = p[fmax[p] > delta]

    if n == max_rates:
        return r_[highest, rest]

    # We should never leave aside rates that at some point are very
    # important, even if they fall outside max_rates
    p = asort[max_rates:]
    rest2 = p[fmax[p] > (1 - delta)]
    return r_[highest, rest, rest2]


def select_rates(data, specie_index, delta, max_rates):
    '''
    Returns a tuple of two sets containing reaction indices
    of production (first set) and losses (second set)
    '''
    dreactions = data.sources(specie_index)
    reactions = list(dreactions.keys())

    r = zeros((len(reactions), len(data.t)))
    for i, react in enumerate(reactions):
        r[i, :] = dreactions[react]

    spos = nanmax(where(r > 0, r, 0), axis=0)
    fpos = r / spos
    # This is b.c. numpy does not provide a nanargsort
    fpos = where(isfinite(fpos), fpos, 0)

    sneg = nanmin(where(r < 0, r, 0), axis=0)
    fneg = r / sneg
    # This is b.c. numpy does not provide a nanargsort
    fneg = where(isfinite(fneg), fneg, 0)

    prod = {reactions[i] +
            1 for i in filter_rates(fpos, delta, max_rates=max_rates)}
    loss = {reactions[i] +
            1 for i in filter_rates(fneg, delta, max_rates=max_rates)}
    return prod, loss


def iter_2_selected(qtablewidget):
    selectedRanges = qtablewidget.selectedRanges()

    selected = []
    for r in selectedRanges:
        bottom, top = r.bottomRow(), r.topRow()
        for i in range(top, bottom + 1):
            itemId = qtablewidget.item(i, 0)
            itemStr = qtablewidget.item(i, 1)
            selected.append((int(itemId.text()), str(itemStr.text())))

    return selected


def load(folder):
    return main(['.', folder])


def main(argv):

    # create the GUI application
    # checks if QApplication already exists
    app = QtWidgets.QApplication.instance()
    if not app:  # create QApplication if it doesnt exist
        app = QtWidgets.QApplication(argv)
        # This check is useful not to crash when testing successive times from
        # IPython

    # instantiate the main window
    dmw = DesignerMainWindow()

    # Load file if present in sys.argv
    if(len(argv) > 1):
        fname = argv[1]
        dmw.import_file_or_dir(fname)

    # show it
    dmw.show()
    dmw.raise_()

    def new_excepthook(type, value, tb):
        em = QtWidgets.QErrorMessage(dmw)
        em.setModal(True)
        msg = "An unhandled exception was raised:\n"
        em.showMessage(
            msg + '&#xa;<br>'.join(traceback.format_exception(type, value, tb)))
        # If we do not call exec_ here, two dialogs may appear at
        # the same time, confusing the user.
        em.exec_()

    sys.excepthook = new_excepthook

    # start the Qt main loop execution, exiting from this script
    # with the same return code of Qt application
    sys.exit(app.exec_())

# %% Run from here (for testing purpose)


if __name__ == '__main__':
    main(sys.argv)
