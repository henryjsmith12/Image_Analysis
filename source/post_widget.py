"""
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

# ==============================================================================

import math
import matplotlib.colors as colors
import matplotlib.pyplot as plt
import numpy as np
import os
import pyqtgraph as pg
from pyqtgraph.dockarea import *
from pyqtgraph.Qt import QtGui, QtCore
from scipy import ndimage
import tifffile as tiff
import time
import warnings

from rsMap3D.config.rsmap3dconfigparser import RSMap3DConfigParser
from rsMap3D.datasource.Sector33SpecDataSource import Sector33SpecDataSource
from rsMap3D.datasource.DetectorGeometryForXrayutilitiesReader import DetectorGeometryForXrayutilitiesReader as detReader
from rsMap3D.datasource.InstForXrayutilitiesReader import InstForXrayutilitiesReader as instrReader
from rsMap3D.gui.rsm3dcommonstrings import BINARY_OUTPUT
from rsMap3D.mappers.gridmapper import QGridMapper
from rsMap3D.mappers.output.vtigridwriter import VTIGridWriter
from rsMap3D.transforms.unitytransform3d import UnityTransform3D
from rsMap3D.utils.srange import srange
import vtk
from vtk.util import numpy_support as npSup
import xrayutilities as xu


from source.general_widgets import *

# ==============================================================================

class PostPlottingWidget(QtGui.QWidget):

    def __init__ (self):
        super().__init__()

        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)

        self.dock_area = DockArea()
        self.createDocks()
        self.createWidgets()

        self.layout.addWidget(self.dock_area)

        self.conversion_dialog = ConversionParametersDialog()

    # --------------------------------------------------------------------------

    def createDocks(self):
        self.data_selection_dock = Dock("Data Selection", size=(100, 100), hideTitle=True)
        self.options_dock = Dock("Options", size=(100, 100), hideTitle=True)
        self.analysis_dock = Dock("Analysis", size=(200, 100))
        self.roi_analysis_dock = Dock("ROI's", size=(200, 100))
        self.data_dock = Dock("Data", size=(100, 100), hideTitle=True)
        self.slice_dock = Dock("Slice", size=(100, 100), hideTitle=True)

        self.dock_area.addDock(self.data_selection_dock)
        self.dock_area.addDock(self.data_dock, "right", self.data_selection_dock)
        self.dock_area.addDock(self.slice_dock, "right", self.data_dock)
        self.dock_area.addDock(self.options_dock, "bottom", self.data_selection_dock)
        self.dock_area.addDock(self.analysis_dock, "bottom", self.data_dock)
        self.dock_area.moveDock(self.slice_dock, "top", self.analysis_dock)
        self.dock_area.moveDock(self.slice_dock, "right", self.data_dock)
        self.dock_area.addDock(self.roi_analysis_dock, "above", self.analysis_dock)
        self.dock_area.moveDock(self.analysis_dock, "above", self.roi_analysis_dock)

    # --------------------------------------------------------------------------

    def createWidgets(self):
        self.data_selection_widget = DataSelectionWidget(self)
        self.options_widget = OptionsWidget(self)
        self.analysis_widget = AnalysisWidget(self)
        self.roi_analysis_widget = ROIAnalysisWidget(self)
        self.data_widget = DataWidget(self)
        self.slice_widget = SliceWidget(self)

        self.data_selection_dock.addWidget(self.data_selection_widget)
        self.options_dock.addWidget(self.options_widget)
        self.analysis_dock.addWidget(self.analysis_widget)
        self.roi_analysis_dock.addWidget(self.roi_analysis_widget)
        self.data_dock.addWidget(self.data_widget)
        self.slice_dock.addWidget(self.slice_widget)

# ==============================================================================

class DataSelectionWidget(QtGui.QWidget):

    def __init__ (self, parent):
        super(DataSelectionWidget, self).__init__(parent)
        self.main_widget = parent

        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)

        self.project_btn = QtGui.QPushButton("Set Project")
        self.project_txtbox = QtGui.QLineEdit()
        self.project_txtbox.setReadOnly(True)
        self.spec_list = QtGui.QListWidget()
        self.scan_list = QtGui.QListWidget()
        self.conversion_chkbox = QtGui.QCheckBox("Convert Scan to HKL")
        self.conversion_btn = QtGui.QPushButton("Parameters")
        self.process_btn = QtGui.QPushButton("Process")

        self.layout.addWidget(self.project_btn, 0, 0)
        self.layout.addWidget(self.project_txtbox, 0, 1)
        self.layout.addWidget(self.spec_list, 1, 0, 1, 2)
        self.layout.addWidget(self.scan_list, 2, 0, 1, 2)
        self.layout.addWidget(self.conversion_chkbox, 3, 0)
        self.layout.addWidget(self.conversion_btn, 3, 1)
        self.layout.addWidget(self.process_btn, 4, 0, 1, 2)

        self.project_btn.clicked.connect(self.setProjectDirectory)
        self.spec_list.itemClicked.connect(self.setScanList)
        self.conversion_btn.clicked.connect(self.showConversionDialog)
        self.process_btn.clicked.connect(self.loadData)

    # --------------------------------------------------------------------------

    def setProjectDirectory(self):
        self.project_path = QtGui.QFileDialog.getExistingDirectory(self,
            "Open Project Directory")

        if self.project_path != "" and "images" in os.listdir(self.project_path):
            self.spec_files = []
            for file in os.listdir(self.project_path):
                if file.endswith(".spec"):
                    self.spec_files.append(os.path.splitext(file)[0])

            if self.spec_files == []:
                return

            self.project_txtbox.setText(os.path.basename(self.project_path))
            self.spec_list.clear()
            self.scan_list.clear()
            self.spec_list.addItems(self.spec_files)

    # --------------------------------------------------------------------------

    def setScanList(self, list_item):
        self.spec_base = list_item.text()
        self.scans_path = f"{self.project_path}/images/{self.spec_base}"

        self.scans = sorted(os.listdir(self.scans_path))

        self.scan_list.clear()
        self.scan_list.addItems(self.scans)

    # --------------------------------------------------------------------------

    def showConversionDialog(self):
        self.main_widget.conversion_dialog.show()
        self.main_widget.conversion_dialog.finished.connect(self.setConversionParameters)

    # --------------------------------------------------------------------------

    def setConversionParameters(self):
        dialog = self.main_widget.conversion_dialog

        self.spec_path = f"{self.project_path}/{self.spec_base}.spec"
        self.detector_path = dialog.detector_config_name
        self.instrument_path = dialog.instrument_config_name
        self.pixel_count_nx = dialog.pixel_count_nx
        self.pixel_count_ny = dialog.pixel_count_ny
        self.pixel_count_nz = dialog.pixel_count_nz

    # --------------------------------------------------------------------------

    def loadData(self):
        self.dataset = []
        self.dataset_rect = None

        scan = self.scan_list.currentItem()
        scan_number = scan.text()[1:]
        scan_path = f"{self.scans_path}/{scan.text()}"
        files = sorted(os.listdir(scan_path))

        if self.conversion_chkbox.isChecked():
            vti_file = ConversionLogic.createVTIFile(self.project_path, self.spec_path, \
                self.detector_path, self.instrument_path, scan_number, self.pixel_count_nx, \
                self.pixel_count_ny, self.pixel_count_nz)
            self.axes, self.dataset = ConversionLogic.loadData(vti_file)

            self.dataset_rect = [(self.axes[0][0], self.axes[0][-1]), (self.axes[1][0], \
                self.axes[1][-1]), (self.axes[2][0], self.axes[2][-1])]
        else:
            for i in range(0, len(files)):
                if files[i] != "alignment.tif":
                    file_path = f"{scan_path}/{files[i]}"
                    image = ndimage.rotate(tiff.imread(file_path), 90)
                    self.dataset.append(image)

            self.dataset = np.stack(self.dataset)
            self.dataset = np.swapaxes(self.dataset, 0, 2)

            self.dataset_rect = [(0, self.dataset.shape[0]), (0, self.dataset.shape[1]), \
                (0, self.dataset.shape[2])]

        self.main_widget.data_widget.displayDataset(self.dataset, new_dataset=True, \
            dataset_rect=self.dataset_rect)

# ==============================================================================

class OptionsWidget(QtGui.QWidget):

    def __init__ (self, parent):
        super(OptionsWidget, self).__init__(parent)
        self.main_widget = parent

        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)

        self.slice_direction_lbl = QtGui.QLabel("Slice Direction:")
        self.slice_direction_cbox = QtGui.QComboBox()
        self.slice_direction_cbox.addItems(["X(H)", "Y(K)", "Z(L)"])

        self.crosshair_chkbox = QtGui.QCheckBox("Crosshair")
        self.crosshair_colorbtn = pg.ColorButton()

        self.bkgrd_color_lbl = QtGui.QLabel("Bkgrd Color:")
        self.bkgrd_black_rbtn = QtGui.QRadioButton("Black")
        self.bkgrd_black_rbtn.setChecked(True)
        self.bkgrd_white_rbtn = QtGui.QRadioButton("White")
        self.bkgrd_color_group = QtGui.QButtonGroup()
        self.bkgrd_color_group.addButton(self.bkgrd_black_rbtn)
        self.bkgrd_color_group.addButton(self.bkgrd_white_rbtn)

        self.colormap_scale_lbl = QtGui.QLabel("Colormap Scale:")
        self.colormap_linear_rbtn = QtGui.QRadioButton("Linear")
        self.colormap_log_rbtn = QtGui.QRadioButton("Log")
        self.colormap_log_rbtn.setChecked(True)
        self.colormap_scale_group = QtGui.QButtonGroup()
        self.colormap_scale_group.addButton(self.colormap_linear_rbtn)
        self.colormap_scale_group.addButton(self.colormap_log_rbtn)

        self.colormap_max_lbl = QtGui.QLabel("Colormap Max:")
        self.colormap_slice_rbtn = QtGui.QRadioButton("Slice")
        self.colormap_scan_rbtn = QtGui.QRadioButton("Scan")
        self.colormap_scan_rbtn.setChecked(True)
        self.colormap_max_group = QtGui.QButtonGroup()
        self.colormap_max_group.addButton(self.colormap_slice_rbtn)
        self.colormap_max_group.addButton(self.colormap_scan_rbtn)

        self.layout.addWidget(self.slice_direction_lbl, 0, 0)
        self.layout.addWidget(self.slice_direction_cbox, 0, 1, 1, 2)
        self.layout.addWidget(self.crosshair_chkbox, 1, 0)
        self.layout.addWidget(self.crosshair_colorbtn, 1, 1, 1, 2)
        self.layout.addWidget(self.bkgrd_color_lbl, 2, 0)
        self.layout.addWidget(self.bkgrd_black_rbtn, 2, 1)
        self.layout.addWidget(self.bkgrd_white_rbtn, 2, 2)
        self.layout.addWidget(self.colormap_scale_lbl, 3, 0)
        self.layout.addWidget(self.colormap_linear_rbtn, 3, 1)
        self.layout.addWidget(self.colormap_log_rbtn, 3, 2)
        self.layout.addWidget(self.colormap_max_lbl, 4, 0)
        self.layout.addWidget(self.colormap_slice_rbtn, 4, 1)
        self.layout.addWidget(self.colormap_scan_rbtn, 4, 2)

        self.slice_direction_cbox.currentTextChanged.connect(self.changeSliceDirection)

    # --------------------------------------------------------------------------

    def changeSliceDirection(self):
        direction = self.sender().currentText()
        self.main_widget.data_widget.displayDataset( \
            self.main_widget.data_widget.dataset, direction)

    # --------------------------------------------------------------------------



# ==============================================================================

class AnalysisWidget(pg.LayoutWidget):

    def __init__ (self, parent):
        super(AnalysisWidget, self).__init__(parent)
        self.main_widget = parent

        self.scan_gbox = QtGui.QGroupBox("Scan")
        self.slice_gbox = QtGui.QGroupBox("Slice")
        self.mouse_gbox = QtGui.QGroupBox("Mouse")
        self.max_gbox = QtGui.QGroupBox("Max")

        self.addWidget(self.scan_gbox, row=0, col=0, rowspan=1)
        self.addWidget(self.slice_gbox, row=1, col=0, rowspan=1)
        self.addWidget(self.mouse_gbox, row=0, col=1, rowspan=2)
        self.addWidget(self.max_gbox, row=0, col=2, rowspan=2)

        self.scan_layout = QtGui.QGridLayout()
        self.slice_layout = QtGui.QGridLayout()
        self.mouse_layout = QtGui.QGridLayout()
        self.max_layout = QtGui.QGridLayout()

        self.scan_gbox.setLayout(self.scan_layout)
        self.slice_gbox.setLayout(self.slice_layout)
        self.mouse_gbox.setLayout(self.mouse_layout)
        self.max_gbox.setLayout(self.max_layout)

        self.scan_pixel_count_x_lbl = QtGui.QLabel("Pixel Count (x):")
        self.scan_pixel_count_x_txtbox = QtGui.QLineEdit()
        self.scan_pixel_count_x_txtbox.setReadOnly(True)
        self.scan_pixel_count_y_lbl = QtGui.QLabel("Pixel Count (y):")
        self.scan_pixel_count_y_txtbox = QtGui.QLineEdit()
        self.scan_pixel_count_y_txtbox.setReadOnly(True)
        self.scan_slice_count_lbl = QtGui.QLabel("Slice Count:")
        self.scan_slice_count_txtbox = QtGui.QLineEdit()
        self.scan_slice_count_txtbox.setReadOnly(True)

        self.slice_current_lbl = QtGui.QLabel("Current Slice:")
        self.slice_current_txtbox = QtGui.QLineEdit()
        self.slice_current_txtbox.setReadOnly(True)
        self.slice_max_intensity_lbl = QtGui.QLabel("Max Intensity:")
        self.slice_max_intensity_txtbox = QtGui.QLineEdit()
        self.slice_max_intensity_txtbox.setReadOnly(True)

        self.mouse_x_lbl = QtGui.QLabel("x Pos:")
        self.mouse_x_txtbox = QtGui.QLineEdit()
        self.mouse_x_txtbox.setReadOnly(True)
        self.mouse_y_lbl = QtGui.QLabel("y Pos:")
        self.mouse_y_txtbox = QtGui.QLineEdit()
        self.mouse_y_txtbox.setReadOnly(True)
        self.mouse_intensity_lbl = QtGui.QLabel("Intensity:")
        self.mouse_intensity_txtbox = QtGui.QLineEdit()
        self.mouse_intensity_txtbox.setReadOnly(True)
        self.mouse_h_lbl = QtGui.QLabel("H:")
        self.mouse_h_txtbox = QtGui.QLineEdit()
        self.mouse_h_txtbox.setReadOnly(True)
        self.mouse_k_lbl = QtGui.QLabel("K:")
        self.mouse_k_txtbox = QtGui.QLineEdit()
        self.mouse_k_txtbox.setReadOnly(True)
        self.mouse_l_lbl = QtGui.QLabel("L:")
        self.mouse_l_txtbox = QtGui.QLineEdit()
        self.mouse_l_txtbox.setReadOnly(True)

        self.max_x_lbl = QtGui.QLabel("x Pos:")
        self.max_x_txtbox = QtGui.QLineEdit()
        self.max_x_txtbox.setReadOnly(True)
        self.max_y_lbl = QtGui.QLabel("y Pos:")
        self.max_y_txtbox = QtGui.QLineEdit()
        self.max_y_txtbox.setReadOnly(True)
        self.max_intensity_lbl = QtGui.QLabel("Intensity:")
        self.max_intensity_txtbox = QtGui.QLineEdit()
        self.max_intensity_txtbox.setReadOnly(True)
        self.max_h_lbl = QtGui.QLabel("H:")
        self.max_h_txtbox = QtGui.QLineEdit()
        self.max_h_txtbox.setReadOnly(True)
        self.max_k_lbl = QtGui.QLabel("K:")
        self.max_k_txtbox = QtGui.QLineEdit()
        self.max_k_txtbox.setReadOnly(True)
        self.max_l_lbl = QtGui.QLabel("L:")
        self.max_l_txtbox = QtGui.QLineEdit()
        self.max_l_txtbox.setReadOnly(True)

        self.scan_layout.addWidget(self.scan_pixel_count_x_lbl, 0, 0)
        self.scan_layout.addWidget(self.scan_pixel_count_x_txtbox, 0, 1)
        self.scan_layout.addWidget(self.scan_pixel_count_y_lbl, 1, 0)
        self.scan_layout.addWidget(self.scan_pixel_count_y_txtbox, 1, 1)
        self.scan_layout.addWidget(self.scan_slice_count_lbl, 2, 0)
        self.scan_layout.addWidget(self.scan_slice_count_txtbox, 2, 1)

        self.slice_layout.addWidget(self.slice_current_lbl, 0, 0)
        self.slice_layout.addWidget(self.slice_current_txtbox, 0, 1)
        self.slice_layout.addWidget(self.slice_max_intensity_lbl, 1, 0)
        self.slice_layout.addWidget(self.slice_max_intensity_txtbox, 1, 1)

        self.mouse_layout.addWidget(self.mouse_x_lbl, 0, 0)
        self.mouse_layout.addWidget(self.mouse_x_txtbox, 0, 1)
        self.mouse_layout.addWidget(self.mouse_y_lbl, 1, 0)
        self.mouse_layout.addWidget(self.mouse_y_txtbox, 1, 1)
        self.mouse_layout.addWidget(self.mouse_intensity_lbl, 2, 0)
        self.mouse_layout.addWidget(self.mouse_intensity_txtbox, 2, 1)
        self.mouse_layout.addWidget(self.mouse_h_lbl, 3, 0)
        self.mouse_layout.addWidget(self.mouse_h_txtbox, 3, 1)
        self.mouse_layout.addWidget(self.mouse_k_lbl, 4, 0)
        self.mouse_layout.addWidget(self.mouse_k_txtbox, 4, 1)
        self.mouse_layout.addWidget(self.mouse_l_lbl, 5, 0)
        self.mouse_layout.addWidget(self.mouse_l_txtbox, 5, 1)

        self.max_layout.addWidget(self.max_x_lbl, 0, 0)
        self.max_layout.addWidget(self.max_x_txtbox, 0, 1)
        self.max_layout.addWidget(self.max_y_lbl, 1, 0)
        self.max_layout.addWidget(self.max_y_txtbox, 1, 1)
        self.max_layout.addWidget(self.max_intensity_lbl, 2, 0)
        self.max_layout.addWidget(self.max_intensity_txtbox, 2, 1)
        self.max_layout.addWidget(self.max_h_lbl, 3, 0)
        self.max_layout.addWidget(self.max_h_txtbox, 3, 1)
        self.max_layout.addWidget(self.max_k_lbl, 4, 0)
        self.max_layout.addWidget(self.max_k_txtbox, 4, 1)
        self.max_layout.addWidget(self.max_l_lbl, 5, 0)
        self.max_layout.addWidget(self.max_l_txtbox, 5, 1)

# ==============================================================================

class ROIAnalysisWidget(pg.LayoutWidget):

    def __init__ (self, parent):
        super(ROIAnalysisWidget, self).__init__(parent)
        self.main_widget = parent

# ==============================================================================

class DataWidget(pg.ImageView):

    def __init__ (self, parent):
        super(DataWidget, self).__init__(parent, view=pg.PlotItem(), imageItem=pg.ImageItem())
        self.main_widget = parent

        self.ui.histogram.hide()
        self.ui.roiBtn.hide()
        self.ui.menuBtn.hide()

        self.dataset = []
        self.slice_direction = None
        self.color_dataset = None
        self.dataset_rect = None

        self.line_roi = pg.LineSegmentROI([[10, 10], [20, 20]], pen='r')
        self.addItem(self.line_roi)

        self.line_roi.sigRegionChanged.connect(self.updateSlice)

    # --------------------------------------------------------------------------

    def displayDataset(self, dataset, slice_direction=None, new_dataset=False, dataset_rect=None):
        self.dataset = dataset
        self.dataset_rect = dataset_rect

        if slice_direction != None:
            self.slice_direction = slice_direction

        if self.slice_direction == None or self.slice_direction == "X(H)":
            self.plot_axes = {"t":0, "x":2, "y":1, "c":3}
            pos = (self.dataset_rect[2][0], self.dataset_rect[1][0])
            scale = ((self.dataset_rect[2][-1] - self.dataset_rect[2][0]) / self.dataset.shape[2],
                (self.dataset_rect[1][-1] - self.dataset_rect[1][0]) / self.dataset.shape[1])

            #slider_ticks =
        elif self.slice_direction == "Y(K)":
            self.plot_axes = {"t":1, "x":2, "y":0, "c":3}
            pos = (self.dataset_rect[2][0], self.dataset_rect[0][0])
            scale = ((self.dataset_rect[2][-1] - self.dataset_rect[2][0]) / self.dataset.shape[2],
                (self.dataset_rect[0][-1] - self.dataset_rect[0][0]) / self.dataset.shape[0])
            #slider_ticks =
        else:
            self.plot_axes = {"t":2, "x":1, "y":0, "c":3}
            pos = (self.dataset_rect[1][0], self.dataset_rect[0][0])
            scale = ((self.dataset_rect[1][-1] - self.dataset_rect[1][0]) / self.dataset.shape[1],
                (self.dataset_rect[0][-1] - self.dataset_rect[0][0]) / self.dataset.shape[0])
            #slider_ticks =

        if new_dataset == True:
            # Normalize image with logarithmic colormap
            colormap_max = np.amax(self.dataset)
            norm = colors.LogNorm(vmax=colormap_max)
            shape = self.dataset.shape
            temp_reshaped_dataset = np.reshape(self.dataset, -1)
            norm_dataset = np.reshape(norm(temp_reshaped_dataset), shape)
            self.color_dataset = plt.cm.jet(norm_dataset)

        self.setImage(self.color_dataset, axes=self.plot_axes, pos=pos, scale=scale)

        print(self.dataset_rect[2][0], self.dataset_rect[1][0])

        #self.updateSlice()

    # --------------------------------------------------------------------------

    def updateSlice(self):
        slice = self.line_roi.getArrayRegion(self.dataset, self.imageItem, \
            axes=(self.axes.get("x"), self.axes.get("y")))

        self.main_widget.slice_widget.displaySlice(slice)

# ==============================================================================

class SliceWidget(pg.ImageView):

    def __init__ (self, parent):
        super(SliceWidget, self).__init__(parent)
        self.main_widget = parent

        self.ui.histogram.hide()
        self.ui.roiBtn.hide()
        self.ui.menuBtn.hide()

    # --------------------------------------------------------------------------

    def displaySlice(self, slice):
        self.slice = slice
        # Normalize image with logarithmic colormap
        colormap_max = np.amax(self.main_widget.data_widget.dataset)
        norm = colors.LogNorm(vmax=colormap_max)
        norm_slice = norm(self.slice)
        color_slice = plt.cm.jet(norm_slice)

        # Set image to image item
        self.setImage(color_slice)

# ==============================================================================

class ConversionParametersDialog(QtGui.QDialog):

    def __init__ (self):
        super().__init__()

        self.setWindowModality(QtCore.Qt.ApplicationModal)

        self.detector_config_name = ""
        self.instrument_config_name = ""
        self.pixel_count_nx = 0
        self.pixel_count_ny = 0
        self.pixel_count_nz = 0

        # Create widgets
        self.detector_lbl = QtGui.QLabel("Det. Config:")
        self.detector_txtbox = QtGui.QLineEdit()
        self.detector_txtbox.setReadOnly(True)
        self.detector_btn = QtGui.QPushButton("Browse")
        self.instrument_lbl = QtGui.QLabel("Instr. Config:")
        self.instrument_txtbox = QtGui.QLineEdit()
        self.instrument_txtbox.setReadOnly(True)
        self.instrument_btn = QtGui.QPushButton("Browse")
        self.pixel_count_lbl = QtGui.QLabel("Pixel Count:")
        self.pixel_count_nx_sbox = QtGui.QSpinBox(maximum=1000, minimum=1)
        self.pixel_count_nx_sbox.setValue(200)
        self.pixel_count_ny_sbox = QtGui.QSpinBox(maximum=1000, minimum=1)
        self.pixel_count_ny_sbox.setValue(200)
        self.pixel_count_nz_sbox = QtGui.QSpinBox(maximum=1000, minimum=1)
        self.pixel_count_nz_sbox.setValue(200)
        self.dialog_btnbox = QtGui.QDialogButtonBox()
        self.dialog_btnbox.addButton("OK", QtGui.QDialogButtonBox.AcceptRole)

        # Create layout
        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)

        # Add widgets to layout
        self.layout.addWidget(self.detector_lbl, 1, 0)
        self.layout.addWidget(self.detector_txtbox, 1, 1, 1, 3)
        self.layout.addWidget(self.detector_btn, 1, 4)
        self.layout.addWidget(self.instrument_lbl, 2, 0)
        self.layout.addWidget(self.instrument_txtbox, 2, 1, 1, 3)
        self.layout.addWidget(self.instrument_btn, 2, 4)
        self.layout.addWidget(self.pixel_count_lbl, 3, 0)
        self.layout.addWidget(self.pixel_count_nx_sbox, 3, 1)
        self.layout.addWidget(self.pixel_count_ny_sbox, 3, 2)
        self.layout.addWidget(self.pixel_count_nz_sbox, 3, 3)
        self.layout.addWidget(self.dialog_btnbox, 4, 3, 1, 2)

        # Connect widgets to functions
        self.detector_btn.clicked.connect(self.selectDetectorConfigFile)
        self.instrument_btn.clicked.connect(self.selectInstrumentConfigFile)
        self.dialog_btnbox.accepted.connect(self.accept)

    # --------------------------------------------------------------------------

    def selectDetectorConfigFile(self):

        """
        Allows user to select a detector configuration .xml file.
        """

        detector = QtGui.QFileDialog.getOpenFileName(self, "", "", "xml Files (*.xml)")
        self.detector_txtbox.setText(detector[0])

    # --------------------------------------------------------------------------

    def selectInstrumentConfigFile(self):

        """
        Allows user to select an instrument configuration .xml file.
        """

        instrument = QtGui.QFileDialog.getOpenFileName(self, "", "", "xml Files (*.xml)")
        self.instrument_txtbox.setText(instrument[0])

    # --------------------------------------------------------------------------

    def accept(self):

        """
        Sets class variables to values in dialog and closes the dialog window.
        """

        self.detector_config_name = self.detector_txtbox.text()
        self.instrument_config_name = self.instrument_txtbox.text()
        self.pixel_count_nx = self.pixel_count_nx_sbox.value()
        self.pixel_count_ny = self.pixel_count_ny_sbox.value()
        self.pixel_count_nz = self.pixel_count_nz_sbox.value()
        self.close()

# ==============================================================================

class ConversionLogic():

    def createVTIFile(project_dir, spec_file, detector_config_name, instrument_config_name,
        scan, nx, ny, nz):

        # Necessary subfunctions for function to run smoothly
        # See rsMap3D source code
        def updateDataSourceProgress(value1, value2):
            print("DataSource Progress %s/%s" % (value1, value2))

        def updateMapperProgress(value1):
            print("Mapper Progress %s" % (value1))

        d_reader = detReader(detector_config_name)
        detector_name = "Pilatus"
        detector = d_reader.getDetectorById(detector_name)
        n_pixels = d_reader.getNpixels(detector)
        roi = [1, n_pixels[0], 1, n_pixels[1]]
        bin = [1,1]

        spec_name, spec_ext = os.path.splitext(os.path.basename(spec_file))
        # Set destination file for gridmapper
        output_file_name = os.path.join(project_dir, spec_name + "_" + scan + ".vti")

        if os.path.exists(output_file_name):
            return output_file_name

        app_config = RSMap3DConfigParser()
        max_image_memory = app_config.getMaxImageMemory()

        scan_range = srange(scan).list()
        data_source = Sector33SpecDataSource(project_dir, spec_name, spec_ext,
            instrument_config_name, detector_config_name, roi=roi, pixelsToAverage=bin,
            scanList=scan_range, appConfig=app_config)
        data_source.setCurrentDetector(detector_name)
        data_source.setProgressUpdater(updateDataSourceProgress)
        data_source.loadSource(mapHKL=True)
        data_source.setRangeBounds(data_source.getOverallRanges())
        image_tbu = data_source.getImageToBeUsed()
        image_size = np.prod(data_source.getDetectorDimensions())

        grid_mapper = QGridMapper(data_source, output_file_name, nx=nx, ny=ny, nz=nz,
            outputType=BINARY_OUTPUT, transform=UnityTransform3D(),
            gridWriter=VTIGridWriter(), appConfig=app_config)
        grid_mapper.setProgressUpdater(updateMapperProgress)
        grid_mapper.doMap()

        return output_file_name

    # --------------------------------------------------------------------------

    def loadData(vti_file):

        """
        Converts information from .vti file into an array in HKL.
        """

        reader = vtk.vtkXMLImageDataReader()
        reader.SetFileName(vti_file)
        reader.Update()

        data = reader.GetOutput()
        dim = data.GetDimensions()

        vec = list(dim)

        vec = [i for i in dim]
        vec.reverse()

        u = npSup.vtk_to_numpy(data.GetPointData().GetArray('Scalars_'))

        max_value = np.nanmax(u)
        min_value = np.nanmin(u)

        u = u.reshape(vec)

        # Swaps H and L
        ctrdata = np.swapaxes(u, 0, 2)

        origin = data.GetOrigin()
        spacing = data.GetSpacing()
        extent = data.GetExtent()

        x = []
        y = []
        z = []

        for point in range(extent[0], extent[1] + 1):
            x.append(origin[0] + point * spacing[0])
        for point in range(extent[2], extent[3] + 1):
            y.append(origin[1] + point * spacing[1])
        for point in range(extent[4], extent[5] + 1):
            z.append(origin[2] + point * spacing[2])

        axes = [x, y, z]

        return axes, ctrdata

# ==============================================================================
