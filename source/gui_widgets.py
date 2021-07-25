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
from pyqtgraph.Qt import QtGui, QtCore
from scipy import ndimage
import tifffile as tiff
import time
import warnings

# Local
from source.data_processing import *
from source.dialog_widgets import *

# ==============================================================================

class OptionsWidget(pg.LayoutWidget):

    """
    Contains controls to view and customize images and alter the viewing window.

    - Live mode: A directory of image file names is displayed and the user can
        view an image by clicking on its name. The user can also view all images
        in an automated loop by clicking on "Simulate Live Plotting". The refresh
        rate can be changed with the spinbox adjacent to the button.

    - Post mode: A 3d array of image data is created from a directory of images.
        The user can view slices of the data by choosing a direction and moving
        the respective slider.

    - Plotting options: The user can choose a variety of options to customize
        their image viewing experience:
            - Mouse crosshair toggle
            - Mouse zoom/pan mode toggle
            - bkgrd color toggle
            - ColorMap scale toggle/percentile slider
    """

    def __init__ (self, parent):
        super(OptionsWidget, self).__init__(parent)
        self.main_window = parent

        # Create GroupBoxes/TabWidget for GroupBoxes
        self.image_mode_tabs = QtGui.QTabWidget()
        self.live_image_gbox = QtGui.QGroupBox("Live")
        self.post_image_gbox = QtGui.QGroupBox("Post")
        self.image_mode_tabs.addTab(self.live_image_gbox, "Live")
        self.image_mode_tabs.addTab(self.post_image_gbox, "Post")

        self.options_gbox = QtGui.QGroupBox("Plotting Options")

        # Disable Options GroupBox until file selected
        self.options_gbox.setEnabled(False)

        # Add GroupBoxes to widget
        self.addWidget(self.image_mode_tabs, row=0, col=0)
        self.addWidget(self.options_gbox, row=1, col=0)

        # Create/add layouts
        self.live_image_layout = QtGui.QGridLayout()
        self.post_image_layout = QtGui.QGridLayout()
        self.options_layout = QtGui.QGridLayout()
        self.live_image_gbox.setLayout(self.live_image_layout)
        self.post_image_gbox.setLayout(self.post_image_layout)
        self.options_gbox.setLayout(self.options_layout)

    # --------------------------------------------------------------------------

    def setupComponents(self):

        """
        - Creates subwidgets
        - Adds subwidgets to widget
        - Connects subwidgets to functions
        """

        # Create live mode widgets

        """
        ** TODO: HKL conversion parameter dialog (+ button to open dialog) for live
            plotting. Contains:

            - detectorDir1 (str)
            - detectorDir2 (str)
            - cch1/2 (float)
            - Nch1/2 (int)
            - distance (float) (optional)
            - pwidth1/2 (float) (optional)
            - chpdeg1/2 (float) (optional)
            - detrot (float) (optional)
            - tiltazimuth (float) (optional)
            - tilt (float) (optional)
            - Nav (tuple or list) (optional)
            - roi (tuple or list) (optional)

            - ub matrix & diffractometer angles should be read in from EPICS/spec
        """

        # Live widgets
        self.live_set_scan_btn = QtGui.QPushButton("Set Scan")
        self.live_set_scan_txtbox = QtGui.QLineEdit()
        self.live_set_scan_txtbox.setReadOnly(True)
        self.live_xyz_rbtn = QtGui.QRadioButton("XYZ")
        self.live_xyz_rbtn.setEnabled(False)
        self.live_hkl_rbtn = QtGui.QRadioButton("HKL")
        self.live_hkl_rbtn.setEnabled(False)
        self.live_coords_group = QtGui.QButtonGroup()
        self.live_coords_group.addButton(self.live_xyz_rbtn)
        self.live_coords_group.addButton(self.live_hkl_rbtn)
        self.live_hkl_params_btn = QtGui.QPushButton("Parameters")
        self.live_hkl_params_btn.setEnabled(False)
        self.live_image_list = QtGui.QListWidget()
        self.live_current_image_lbl = QtGui.QLabel("Current Image:")
        self.live_current_image_txtbox = QtGui.QLineEdit()
        self.live_current_image_txtbox.setReadOnly(True)

        # Live layout
        self.live_image_layout.addWidget(self.live_set_scan_btn, 0, 0, 1, 3)
        self.live_image_layout.addWidget(self.live_set_scan_txtbox, 0, 3, 1, 3)
        self.live_image_layout.addWidget(self.live_xyz_rbtn, 1, 0)
        self.live_image_layout.addWidget(self.live_hkl_rbtn, 1, 1)
        self.live_image_layout.addWidget(self.live_hkl_params_btn, 1, 2, 1, 4)
        self.live_image_layout.addWidget(self.live_image_list, 2, 0, 3, 6)
        self.live_image_layout.addWidget(self.live_current_image_lbl, 5, 0, 1, 2)
        self.live_image_layout.addWidget(self.live_current_image_txtbox, 5, 2, 1, 4)

        # Live widget connections
        self.live_set_scan_btn.clicked.connect(self.liveSetScan)
        self.live_xyz_rbtn.toggled.connect(self.liveToggleHKLParametersButton)
        self.live_hkl_rbtn.toggled.connect(self.liveToggleHKLParametersButton)
        self.live_xyz_rbtn.toggled.connect(self.liveSetImageList)
        self.live_hkl_params_btn.clicked.connect(self.liveSetHKLParameters)
        self.live_image_list.itemClicked.connect(self.liveLoadImage)

        # Post widgets
        self.post_set_project_btn = QtGui.QPushButton("Set Project")
        self.post_set_project_txtbox = QtGui.QLineEdit()
        self.post_set_project_txtbox.setReadOnly(True)
        self.post_xyz_rbtn = QtGui.QRadioButton("XYZ")
        self.post_xyz_rbtn.setEnabled(False)
        self.post_hkl_rbtn = QtGui.QRadioButton("HKL")
        self.post_hkl_rbtn.setEnabled(False)
        self.post_coords_group = QtGui.QButtonGroup()
        self.post_coords_group.addButton(self.post_xyz_rbtn)
        self.post_coords_group.addButton(self.post_hkl_rbtn)
        self.post_spec_config_btn = QtGui.QPushButton("Spec/Config Files")
        self.post_spec_config_btn.setEnabled(False)
        self.post_scan_list = QtGui.QListWidget()
        self.post_current_scan_lbl = QtGui.QLabel("Current Scan:")
        self.post_current_scan_txtbox = QtGui.QLineEdit()
        self.post_current_scan_txtbox.setReadOnly(True)
        self.post_process_scan_btn = QtGui.QPushButton("Process Scan")
        self.post_slice_direction_lbl = QtGui.QLabel("Slice Direction:")
        self.post_slice_direction_cbox = QtGui.QComboBox()
        self.post_slice_direction_cbox.addItems(["X(H)", "Y(K)", "Z(L)"])
        self.post_slice_direction_cbox.setEnabled(False)
        self.post_slice_sbox = QtGui.QDoubleSpinBox()
        self.post_slice_sbox.setEnabled(False)
        self.post_slice_sbox.setDecimals(5)
        self.post_slice_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.post_slice_slider.setTickPosition(QtGui.QSlider.TicksBothSides)
        self.post_slice_slider.setEnabled(False)

        # Post Layout
        self.post_image_layout.addWidget(self.post_set_project_btn, 0, 0, 1, 3)
        self.post_image_layout.addWidget(self.post_set_project_txtbox, 0, 3, 1, 3)
        self.post_image_layout.addWidget(self.post_xyz_rbtn, 1, 0)
        self.post_image_layout.addWidget(self.post_hkl_rbtn, 1, 1)
        self.post_image_layout.addWidget(self.post_spec_config_btn, 1, 2, 1, 4)
        self.post_image_layout.addWidget(self.post_scan_list, 2, 0, 3, 6)
        self.post_image_layout.addWidget(self.post_current_scan_lbl, 5, 0, 1, 2)
        self.post_image_layout.addWidget(self.post_current_scan_txtbox, 5, 2, 1, 4)
        self.post_image_layout.addWidget(self.post_process_scan_btn, 6, 0, 1, 6)
        self.post_image_layout.addWidget(self.post_slice_direction_lbl, 7, 0, 1, 2)
        self.post_image_layout.addWidget(self.post_slice_direction_cbox, 7, 2, 1, 4)
        self.post_image_layout.addWidget(self.post_slice_sbox, 8, 0, 1, 1)
        self.post_image_layout.addWidget(self.post_slice_slider, 8, 1, 1, 5)

        # Post widget connections
        self.post_set_project_btn.clicked.connect(self.postSetProject)
        self.post_xyz_rbtn.toggled.connect(self.postToggleSpecConfigButton)
        self.post_hkl_rbtn.toggled.connect(self.postToggleSpecConfigButton)
        self.post_xyz_rbtn.toggled.connect(self.postSetScanList)
        self.post_spec_config_btn.clicked.connect(self.postSetSpecConfigFiles)
        self.post_process_scan_btn.clicked.connect(self.postProcessScan)
        self.post_process_scan_btn.clicked.connect(self.postSetAxes)
        self.post_slice_direction_cbox.currentTextChanged.connect(self.postLoadImage)
        self.post_slice_direction_cbox.currentTextChanged.connect(self.postSetAxes)
        self.post_slice_slider.valueChanged.connect(self.postLoadImage)

        # Options widgets
        self.options_roi_chkbox = QtGui.QCheckBox("ROI")
        self.options_crosshair_mouse_chkbox = QtGui.QCheckBox("Crosshair")
        self.options_crosshair_color_btn = pg.ColorButton()
        self.options_mouse_mode_lbl = QtGui.QLabel("Mouse Mode:")
        self.options_mouse_mode_group = QtGui.QButtonGroup()
        self.options_mouse_pan_rbtn = QtGui.QRadioButton("Pan")
        self.options_mouse_pan_rbtn.setChecked(True)
        self.options_mouse_rect_rbtn = QtGui.QRadioButton("Rectangle")
        self.options_mouse_mode_group.addButton(self.options_mouse_pan_rbtn)
        self.options_mouse_mode_group.addButton(self.options_mouse_rect_rbtn)
        self.options_bkgrd_color_lbl = QtGui.QLabel("Bkgrd Color:")
        self.options_bkgrd_color_group = QtGui.QButtonGroup()
        self.options_bkgrd_black_rbtn = QtGui.QRadioButton("Black")
        self.options_bkgrd_black_rbtn.setChecked(True)
        self.options_bkgrd_white_rbtn = QtGui.QRadioButton("White")
        self.options_bkgrd_color_group.addButton(self.options_bkgrd_black_rbtn)
        self.options_bkgrd_color_group.addButton(self.options_bkgrd_white_rbtn)
        self.options_cmap_scale_lbl = QtGui.QLabel("CMap Scale:")
        self.options_cmap_scale_group = QtGui.QButtonGroup()
        self.options_cmap_linear_rbtn = QtGui.QRadioButton("Linear")
        self.options_cmap_linear_rbtn.setChecked(True)
        self.options_cmap_log_rbtn = QtGui.QRadioButton("Logarithmic")
        self.options_cmap_scale_group.addButton(self.options_cmap_linear_rbtn)
        self.options_cmap_scale_group.addButton(self.options_cmap_log_rbtn)
        self.options_cmap_pctl_lbl = QtGui.QLabel("CMap Pctl:")
        self.options_cmap_pctl_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.options_cmap_pctl_slider.setMinimum(1)
        self.options_cmap_pctl_slider.setMaximum(100)
        self.options_cmap_pctl_slider.setSingleStep(10)
        self.options_cmap_pctl_slider.setTickInterval(10)
        self.options_cmap_pctl_slider.setTickPosition(QtGui.QSlider.TicksBothSides)
        self.options_cmap_pctl_slider.setValue(100)
        self.options_aspect_ratio_lbl = QtGui.QLabel("Aspect Ratio:")
        self.options_aspect_ratio_group = QtGui.QButtonGroup()
        self.options_aspect_ratio_auto_rbtn = QtGui.QRadioButton("Auto")
        self.options_aspect_ratio_auto_rbtn.setChecked(True)
        self.options_aspect_ratio_one_rbtn = QtGui.QRadioButton("1:1")
        self.options_advanced_roi_btn = QtGui.QPushButton("Advanced ROI")
        self.options_advanced_roi_txtbox = QtGui.QLineEdit()
        self.options_advanced_roi_txtbox.setReadOnly(True)

        # Options layout
        self.options_layout.addWidget(self.options_roi_chkbox, 0, 0)
        self.options_layout.addWidget(self.options_crosshair_mouse_chkbox, 0, 1)
        self.options_layout.addWidget(self.options_crosshair_color_btn, 0, 2)
        self.options_layout.addWidget(self.options_mouse_mode_lbl, 2, 0)
        self.options_layout.addWidget(self.options_mouse_pan_rbtn, 2, 1)
        self.options_layout.addWidget(self.options_mouse_rect_rbtn, 2, 2)
        self.options_layout.addWidget(self.options_bkgrd_color_lbl, 3, 0)
        self.options_layout.addWidget(self.options_bkgrd_black_rbtn, 3, 1)
        self.options_layout.addWidget(self.options_bkgrd_white_rbtn, 3, 2)
        self.options_layout.addWidget(self.options_cmap_scale_lbl, 4, 0)
        self.options_layout.addWidget(self.options_cmap_linear_rbtn, 4, 1)
        self.options_layout.addWidget(self.options_cmap_log_rbtn, 4, 2)
        self.options_layout.addWidget(self.options_cmap_pctl_lbl, 5, 0)
        self.options_layout.addWidget(self.options_cmap_pctl_slider, 5, 1, 1, 2)
        self.options_layout.addWidget(self.options_aspect_ratio_lbl, 6, 0)
        self.options_layout.addWidget(self.options_aspect_ratio_auto_rbtn, 6, 1)
        self.options_layout.addWidget(self.options_aspect_ratio_one_rbtn, 6, 2)
        self.options_layout.addWidget(self.options_advanced_roi_btn, 7, 0)
        self.options_layout.addWidget(self.options_advanced_roi_txtbox, 7, 1, 1, 2)

        # Options widget connections
        self.options_roi_chkbox.stateChanged.connect(self.toggleROIBoxes)
        self.options_crosshair_mouse_chkbox.stateChanged.connect(self.toggleMouseCrosshair)
        self.options_crosshair_color_btn.sigColorChanged.connect(self.changeCrosshairColor)
        self.options_mouse_pan_rbtn.toggled.connect(self.toggleMouseMode)
        self.options_mouse_rect_rbtn.toggled.connect(self.toggleMouseMode)
        self.options_bkgrd_black_rbtn.toggled.connect(self.toggleBkgrdColor)
        self.options_bkgrd_white_rbtn.toggled.connect(self.toggleBkgrdColor)
        self.options_cmap_linear_rbtn.toggled.connect(self.toggleCmapScale)
        self.options_cmap_log_rbtn.toggled.connect(self.toggleCmapScale)
        self.options_cmap_pctl_slider.valueChanged.connect(self.changeCmapPctl)
        self.options_aspect_ratio_auto_rbtn.toggled.connect(self.toggleAspectRatio)
        self.options_aspect_ratio_one_rbtn.toggled.connect(self.toggleAspectRatio)
        self.options_advanced_roi_btn.clicked.connect(self.setAdvancedROI)

    # --------------------------------------------------------------------------

    def liveSetScan(self):

        """
        Selects scan directory for live mode.
        """

        # Clear scan image list and resets coordinate system radio buttons
        self.live_image_list.clear()

        # Directory path containing scan images
        self.live_scan_path = QtGui.QFileDialog.getExistingDirectory(self,
            "Open Scan Directory")

        if self.live_scan_path != "":
            # Checks if directory only contains image files
            for file_name in os.listdir(self.live_scan_path):
                if not file_name.endswith((".tif", ".tiff")):
                    return

            # Separates path basename from path to display in txtbox
            self.live_scan_path_base = os.path.basename(self.live_scan_path)
            self.live_set_scan_txtbox.setText(self.live_scan_path_base)
            self.live_image_files = sorted(os.listdir(self.live_scan_path))

            # Enables coordinate system radio buttons
            self.live_xyz_rbtn.setEnabled(True)
            self.live_hkl_rbtn.setEnabled(True)

            # Sets scan image list is xyz is already selected
            if self.live_xyz_rbtn.isChecked():
                self.liveSetImageList()

    # --------------------------------------------------------------------------

    def liveToggleHKLParametersButton(self):

        """
        - Enables/disables HKL conversion parameters button.
        - Clears scan image list
        """

        if self.live_hkl_rbtn.isChecked():
            self.live_hkl_params_btn.setEnabled(True)
        else:
            self.live_hkl_params_btn.setEnabled(False)

        self.live_image_list.clear()

    # --------------------------------------------------------------------------

    def liveSetHKLParameters(self):

        dialog = ConversionParametersDialogWidget()

        print("PAST DIALOG")

    # --------------------------------------------------------------------------

    def liveSetImageList(self):

        """
        Displays scan image directory contents in list widget.
        """

        self.live_image_list.clear()
        self.live_image_list.addItems(self.live_image_files)

    # --------------------------------------------------------------------------

    def liveLoadImage(self, file_name):

        """
        - Reads image from file path.
        - Calls displayImage to load image into viewing window.
        """

        # Concatenates directory and file names
        file_path = f"{self.live_scan_path}/{file_name.text()}"

        # Reads image
        self.image = np.rot90(tiff.imread(file_path), 2)

        # Loads image into viewing window
        self.main_window.image_widget.displayImage(self.image, rect=None)

        # Sets file name as current image
        self.live_current_image_txtbox.setText(file_name.text())

        # Enable options
        self.options_gbox.setEnabled(True)

    # --------------------------------------------------------------------------

    def postSetProject(self):

        """

        """

        self.post_scan_list.clear()

        self.post_project_path = QtGui.QFileDialog.getExistingDirectory(self,
            "Open Project Directory")

        if self.post_project_path != "" and "images" in os.listdir(self.post_project_path):
            # Separates path basename from path to display in txtbox
            self.post_project_path_base = os.path.basename(self.post_project_path)
            self.post_set_project_txtbox.setText(self.post_project_path_base)

            # Sets correct scan path
            self.post_images_path = os.path.join(self.post_project_path, "images")
            self.post_scans_path = f"{self.post_images_path}/{os.listdir(self.post_images_path)[0]}"
            self.post_scan_folders = sorted(os.listdir(self.post_scans_path))

            # Enables coordinate system radio buttons
            self.post_xyz_rbtn.setEnabled(True)
            self.post_hkl_rbtn.setEnabled(True)

    # --------------------------------------------------------------------------

    def postToggleSpecConfigButton(self):

        """

        """

        if self.post_hkl_rbtn.isChecked():
            self.post_spec_config_btn.setEnabled(True)
        else:
            self.post_spec_config_btn.setEnabled(False)

        self.post_scan_list.clear()

    # --------------------------------------------------------------------------

    def postSetSpecConfigFiles(self):

        """
        Opens data source dialog.
        """

        # See DataSourceDialogWidget class for more info
        dialog = DataSourceDialogWidget()

        self.post_spec_path = dialog.spec_name
        self.post_detector_path = dialog.detector_config_name
        self.post_instrument_path = dialog.instrument_config_name
        self.post_pixel_count_nx = dialog.pixel_count_nx
        self.post_pixel_count_ny = dialog.pixel_count_ny
        self.post_pixel_count_nz = dialog.pixel_count_nz

        self.postSetScanList()

    # --------------------------------------------------------------------------

    def postSetScanList(self):

        """

        """

        self.post_scan_list.clear()
        self.post_scan_list.addItems(self.post_scan_folders)

    # --------------------------------------------------------------------------

    def postProcessScan(self):

        """

        """
        scan = self.post_scan_list.currentItem()
        if not scan == None:
            self.postLoadData(scan)
    # --------------------------------------------------------------------------

    def postLoadData(self, scan):

        """

        """

        self.dataset = []
        scan_path = os.path.join(self.post_scans_path, scan.text())
        self.post_image_files = sorted(os.listdir(scan_path))

        if self.post_xyz_rbtn.isChecked():
            for i in range(1, len(self.post_image_files)):
                # Creates 2d image from file path
                file_path = f"{scan_path}/{self.post_image_files[i]}"
                image = ndimage.rotate(tiff.imread(file_path), 90)
                # Appends image to list of images
                self.dataset.append(image)

            self.dataset = np.stack(self.dataset)
            self.dataset = np.swapaxes(self.dataset, 0, 2)

            self.x_h_axis = [0, self.dataset.shape[0]]
            self.y_k_axis = [0, self.dataset.shape[1]]
            self.z_l_axis = [0, self.dataset.shape[2]]

        elif self.post_hkl_rbtn.isChecked():
            scan_number = scan.text()[1:]

            # Creates vti file
            vti_file = DataProcessing.createVTIFile(self.post_project_path, self.post_spec_path,
                self.post_detector_path, self.post_instrument_path, scan_number,
                self.post_pixel_count_nx, self.post_pixel_count_ny, self.post_pixel_count_nz)

            # Converts vti file into 3D array with proper axes
            self.axes, self.dataset = DataProcessing.loadData(vti_file)
            self.x_h_axis = [self.axes[0][0], self.axes[0][-1]]
            self.y_k_axis = [self.axes[1][0], self.axes[1][-1]]
            self.z_l_axis = [self.axes[2][0], self.axes[2][-1]]

            self.main_window.roi_plots_widget.clearROIPlots()

        self.post_current_scan_txtbox.setText(scan.text())

        self.postLoadImage()

    # --------------------------------------------------------------------------

    def postLoadImage(self):

        """

        """

        self.postSetSliceRanges()

        x_h_min, x_h_max = self.x_h_axis
        y_k_min, y_k_max = self.y_k_axis
        z_l_min, z_l_max = self.z_l_axis

        slice_direction = self.post_slice_direction_cbox.currentText()

        if slice_direction == "X(H)":
            # Creates rectangle for array to be plotted inside of
            rect = QtCore.QRectF(z_l_min, y_k_min, z_l_max - z_l_min, y_k_max - y_k_min)
            x_h_slice = self.post_slice_slider.value()
            slice_value = (x_h_max - x_h_min) * (x_h_slice + 1) / self.dataset.shape[0] + x_h_min
            self.image = self.dataset[x_h_slice, :, :]

        elif slice_direction == "Y(K)":
            rect = QtCore.QRectF(z_l_min, x_h_min, z_l_max - z_l_min, x_h_max - x_h_min)
            y_k_slice = self.post_slice_slider.value()
            slice_value = (y_k_max - y_k_min) * (y_k_slice + 1) / self.dataset.shape[1] + y_k_min
            self.image = self.dataset[:, y_k_slice, :]

        elif slice_direction == "Z(L)":
            rect = QtCore.QRectF(y_k_min, x_h_min, y_k_max - y_k_min, x_h_max - x_h_min)
            z_l_slice = self.post_slice_slider.value()
            slice_value = (z_l_max - z_l_min) * (z_l_slice + 1) / self.dataset.shape[2] + z_l_min
            self.image = self.dataset[ :, :, z_l_slice]

        self.image = np.flipud(self.image)

        self.post_slice_sbox.setValue(slice_value)

        # Sets image in viewing window
        self.main_window.image_widget.displayImage(self.image, rect=rect)

        if self.options_roi_chkbox.isChecked():
            self.main_window.roi_plots_widget.displayROIPlots(self.dataset, slice_direction, rect)
        else:
            self.main_window.roi_plots_widget.clearROIPlots()

        # Enable options
        self.options_gbox.setEnabled(True)
        self.post_slice_direction_cbox.setEnabled(True)
        self.post_slice_slider.setEnabled(True)

    # --------------------------------------------------------------------------

    def postSetSliceRanges(self):

        """

        """

        if self.post_slice_direction_cbox.currentText() == "X(H)":
            self.post_slice_slider.setRange(0, self.dataset.shape[0] - 1)
            self.post_slice_sbox.setRange(self.x_h_axis[0], self.x_h_axis[1])
        elif self.post_slice_direction_cbox.currentText() == "Y(K)":
            self.post_slice_slider.setRange(0, self.dataset.shape[1] - 1)
            self.post_slice_sbox.setRange(self.y_k_axis[0], self.y_k_axis[1])
        elif self.post_slice_direction_cbox.currentText() == "Z(L)":
            self.post_slice_slider.setRange(0, self.dataset.shape[2] - 1)
            self.post_slice_sbox.setRange(self.z_l_axis[0], self.z_l_axis[1])

    # --------------------------------------------------------------------------

    def postSetAxes(self):

        """

        """

        if self.post_hkl_rbtn.isChecked():
            if self.post_slice_direction_cbox.currentText() == "X(H)":
                self.main_window.image_widget.setLabel("left", "K")
                self.main_window.image_widget.setLabel("bottom", "L")
            elif self.post_slice_direction_cbox.currentText() == "Y(K)":
                self.main_window.image_widget.setLabel("left", "H")
                self.main_window.image_widget.setLabel("bottom", "L")
            else:
                self.main_window.image_widget.setLabel("left", "H")
                self.main_window.image_widget.setLabel("bottom", "K")
        else:
            self.main_window.image_widget.setLabel("left", "")
            self.main_window.image_widget.setLabel("bottom", "")


    # --------------------------------------------------------------------------

    def toggleROIBoxes(self, state):

        """
        Toggles visibility for ROI boxes.
        """

        # 2 = checked
        if state == 2:
            self.main_window.image_widget.roi_1.show()
            self.main_window.image_widget.roi_2.show()
            self.main_window.image_widget.roi_3.show()
            self.main_window.image_widget.roi_4.show()
        else:
            self.main_window.image_widget.roi_1.hide()
            self.main_window.image_widget.roi_2.hide()
            self.main_window.image_widget.roi_3.hide()
            self.main_window.image_widget.roi_4.hide()

    # --------------------------------------------------------------------------

    def toggleMouseCrosshair(self, state):

        """
        Toggles visibility for mouse crosshair.
        """

        # 2 = checked
        if state == 2:
            self.main_window.image_widget.v_line.setVisible(True)
            self.main_window.image_widget.h_line.setVisible(True)
        else:
            self.main_window.image_widget.v_line.setVisible(False)
            self.main_window.image_widget.h_line.setVisible(False)

    # --------------------------------------------------------------------------

    def changeCrosshairColor(self):

        """
        Changes color for mouse crosshair.
        """

        color = self.options_crosshair_color_btn.color()

        self.main_window.image_widget.v_line.setPen(pg.mkPen(color))
        self.main_window.image_widget.h_line.setPen(pg.mkPen(color))

    # --------------------------------------------------------------------------

    def toggleMouseMode(self):

        """
        Toggles mode for zooming and panning with mouse.

        - Pan: Left click to pan; wheel to zoom.
        - Rectangle: Left click and drag to select roi to view; wheel to zoom.
        """

        button = self.sender()

        if button.text() == "Pan":
            self.main_window.image_widget.view.setMouseMode(pg.ViewBox.PanMode)
        else:
            self.main_window.image_widget.view.setMouseMode(pg.ViewBox.RectMode)

    # --------------------------------------------------------------------------

    def toggleBkgrdColor(self):

        """
        Toggles bkgrd color for image plot widget.

        - Options: black or white.
        """

        button = self.sender()

        if button.text() == "Black":
            self.main_window.image_widget.setBackground("default")
        else:
            self.main_window.image_widget.setBackground("w")

    # --------------------------------------------------------------------------

    def toggleCmapScale(self):

        """
        Toggles colormap scale for image.

        - Options: linear or logarithmic.
        """

        button = self.sender()

        if button.text() == "Logarithmic":
            self.main_window.image_widget.options_cmap_scale = "Log"
            self.main_window.image_widget.displayImage(self.image)
        else:
            self.main_window.image_widget.options_cmap_scale = "Linear"
            self.main_window.image_widget.displayImage(self.image)

    # --------------------------------------------------------------------------

    def changeCmapPctl(self):

        """
        Changes colormap pctl to value of slider (between 0.0 and 1.0).
        """

        slider = self.sender()

        self.main_window.image_widget.cmap_pctl = slider.value() / 100.0
        self.main_window.image_widget.displayImage(self.image)

    # --------------------------------------------------------------------------

    def toggleAspectRatio(self):

        """
        Toggles aspect ratio for image.

        - Options: auto or 1 to 1.
        """

        button = self.sender()

        if button.text() == "Auto":
            self.main_window.image_widget.setAspectLocked(False)
        else:
            self.main_window.image_widget.setAspectLocked(True, ratio=1)

    # --------------------------------------------------------------------------

    def setAdvancedROI(self):

        dialog = AdvancedROIDialogWidget()

        first_roi = dialog.first_roi
        operator = dialog.operator
        second_roi = dialog.second_roi

        str_title = f"{first_roi} {operator} {second_roi}"
        if not "" in [first_roi, operator, second_roi]:
            self.options_advanced_roi_txtbox.setText(str_title)

            self.main_window.advanced_roi_plot_widget.getRegions(first_roi, operator,
                second_roi, str_title)


    # --------------------------------------------------------------------------

    def simLivePlotting(self):

        """
        Simulates live update of image plot. Updates separated by refresh rate.
        """

        # Loops through images
        for i in range(self.live_image_list.count()):
            # Loads image to viewing window
            self.loadLiveImage(self.live_image_list.item(i))
            # Necessary to refresh UI
            QtGui.QApplication.processEvents()
            # Loop sleeps for set period (<1 second)
            time.sleep(self.live_refresh_rate)

    # --------------------------------------------------------------------------

    def changeRefreshRate(self, value):

        """
        Changes refresh rate for live plotting (Between 0 and 1 second).
        """

        self.live_refresh_rate = value

# ==============================================================================

class AnalysisWidget(pg.LayoutWidget):

    """
    Contains mouse, image, and ROI information.

    - Mouse: Shows coordinates and pixel intesity for mouse position on image.

    - Images: Shows image width/height, maximum pixel intensity, and colormap pctl.

    - ROI: Spinboxes for box position and size that give the user a second method
        of altering ROI's. Although visually housed in the analysis widget, the
        ROI widgets are initialized in the ImageWidget __init__ function.
    """

    def __init__ (self, parent):
        super(AnalysisWidget, self).__init__(parent)
        self.main_window = parent

        # Create GroupBoxes
        self.mouse_gbox = QtGui.QGroupBox("Mouse")
        self.image_gbox = QtGui.QGroupBox("Image")
        self.roi_1_gbox = QtGui.QGroupBox("ROI 1")
        self.roi_2_gbox = QtGui.QGroupBox("ROI 2")
        self.roi_3_gbox = QtGui.QGroupBox("ROI 3")
        self.roi_4_gbox = QtGui.QGroupBox("ROI 4")

        # Add GroupBoxes to widget
        self.addWidget(self.mouse_gbox, row=0, col=0, rowspan=1)
        self.addWidget(self.image_gbox, row=1, col=0, rowspan=1)
        self.addWidget(self.roi_1_gbox, row=0, col=1, rowspan=2)
        self.addWidget(self.roi_2_gbox, row=0, col=2, rowspan=2)
        self.addWidget(self.roi_3_gbox, row=0, col=3, rowspan=2)
        self.addWidget(self.roi_4_gbox, row=0, col=4, rowspan=2)

        # Create/add layouts
        self.mouse_layout = QtGui.QGridLayout()
        self.image_layout = QtGui.QGridLayout()
        self.roi_1_layout = QtGui.QGridLayout()
        self.roi_2_layout = QtGui.QGridLayout()
        self.roi_3_layout = QtGui.QGridLayout()
        self.roi_4_layout = QtGui.QGridLayout()
        self.mouse_gbox.setLayout(self.mouse_layout)
        self.image_gbox.setLayout(self.image_layout)
        self.roi_1_gbox.setLayout(self.roi_1_layout)
        self.roi_2_gbox.setLayout(self.roi_2_layout)
        self.roi_3_gbox.setLayout(self.roi_3_layout)
        self.roi_4_gbox.setLayout(self.roi_4_layout)

        self.setEnabled(False)

    # --------------------------------------------------------------------------

    def setupComponents(self):

        """
        - Creates subwidgets
        - Adds subwidgets to widget
        """

        # Create mouse widgets
        self.mouse_x_lbl = QtGui.QLabel("x Pos:")
        self.mouse_x_txtbox = QtGui.QLineEdit()
        self.mouse_x_txtbox.setReadOnly(True)
        self.mouse_y_lbl = QtGui.QLabel("y Pos:")
        self.mouse_y_txtbox = QtGui.QLineEdit()
        self.mouse_y_txtbox.setReadOnly(True)
        self.mouse_intensity_lbl = QtGui.QLabel("Intensity:")
        self.mouse_intensity_txtbox = QtGui.QLineEdit()
        self.mouse_intensity_txtbox.setReadOnly(True)
        self.mouse_h_lbl = QtGui.QLabel("H")
        self.mouse_h_txtbox = QtGui.QLineEdit()
        self.mouse_h_txtbox.setReadOnly(True)
        self.mouse_k_lbl = QtGui.QLabel("K")
        self.mouse_k_txtbox = QtGui.QLineEdit()
        self.mouse_k_txtbox.setReadOnly(True)
        self.mouse_l_lbl = QtGui.QLabel("L")
        self.mouse_l_txtbox = QtGui.QLineEdit()
        self.mouse_l_txtbox.setReadOnly(True)

        # Create image widgets
        self.image_width_lbl = QtGui.QLabel("Width:")
        self.image_width_txtbox = QtGui.QLineEdit()
        self.image_width_txtbox.setReadOnly(True)
        self.image_height_lbl = QtGui.QLabel("Height:")
        self.image_height_txtbox = QtGui.QLineEdit()
        self.image_height_txtbox.setReadOnly(True)
        self.image_max_intensity_lbl = QtGui.QLabel("Max:")
        self.image_max_intensity_txtbox = QtGui.QLineEdit()
        self.image_max_intensity_txtbox.setReadOnly(True)
        self.image_options_cmap_pctl_lbl = QtGui.QLabel("CMap Pctl:")
        self.image_cmap_pctl_txtbox = QtGui.QLineEdit()
        self.image_cmap_pctl_txtbox.setReadOnly(True)

        # Add widgets to GroupBoxes
        self.mouse_layout.addWidget(self.mouse_x_lbl, 0, 0)
        self.mouse_layout.addWidget(self.mouse_x_txtbox, 0, 1)
        self.mouse_layout.addWidget(self.mouse_y_lbl, 1, 0)
        self.mouse_layout.addWidget(self.mouse_y_txtbox, 1, 1)
        self.mouse_layout.addWidget(self.mouse_intensity_lbl, 2, 0)
        self.mouse_layout.addWidget(self.mouse_intensity_txtbox, 2, 1)
        self.mouse_layout.addWidget(self.mouse_h_lbl, 0, 2)
        self.mouse_layout.addWidget(self.mouse_h_txtbox, 0, 3)
        self.mouse_layout.addWidget(self.mouse_k_lbl, 1, 2)
        self.mouse_layout.addWidget(self.mouse_k_txtbox, 1, 3)
        self.mouse_layout.addWidget(self.mouse_l_lbl, 2, 2)
        self.mouse_layout.addWidget(self.mouse_l_txtbox, 2, 3)

        self.image_layout.addWidget(self.image_width_lbl, 0, 0)
        self.image_layout.addWidget(self.image_width_txtbox, 0, 1)
        self.image_layout.addWidget(self.image_height_lbl, 1, 0)
        self.image_layout.addWidget(self.image_height_txtbox, 1, 1)
        self.image_layout.addWidget(self.image_max_intensity_lbl, 2, 0)
        self.image_layout.addWidget(self.image_max_intensity_txtbox, 2, 1)
        self.image_layout.addWidget(self.image_options_cmap_pctl_lbl, 3, 0)
        self.image_layout.addWidget(self.image_cmap_pctl_txtbox, 3, 1)

# ==============================================================================

class ImageWidget(pg.PlotWidget):

    """
    Contains viewing window for images.
    """

    def __init__ (self, parent):
        super(ImageWidget, self).__init__(parent)
        self.main_window = parent

        # bkgrd initially set to black
        self.setBackground("default")

        self.invertY(True)

        self.view = self.getViewBox()
        self.image_item = pg.ImageItem()
        self.addItem(self.image_item)

        # Sets current cmap/cmap scaling
        self.options_cmap_scale = "Linear"
        self.cmap_pctl = 1.0

        # Creates and adds ROIWidgets
        # See ROIWidget class for more information
        roi_1_layout = self.main_window.analysis_widget.roi_1_layout
        roi_2_layout = self.main_window.analysis_widget.roi_2_layout
        roi_3_layout = self.main_window.analysis_widget.roi_3_layout
        roi_4_layout = self.main_window.analysis_widget.roi_4_layout
        roi_1_plot = self.main_window.roi_plots_widget.roi_1_plot
        roi_2_plot = self.main_window.roi_plots_widget.roi_2_plot
        roi_3_plot = self.main_window.roi_plots_widget.roi_3_plot
        roi_4_plot = self.main_window.roi_plots_widget.roi_4_plot
        self.roi_1 = ROIWidget([200, 100], [40, 40], roi_1_layout, roi_1_plot)
        self.roi_2 = ROIWidget([205, 105], [30, 30], roi_2_layout, roi_2_plot)
        self.roi_3 = ROIWidget([210, 110], [20, 20], roi_3_layout, roi_3_plot)
        self.roi_4 = ROIWidget([215, 115], [10, 10], roi_4_layout, roi_4_plot)
        self.addItem(self.roi_1)
        self.addItem(self.roi_2)
        self.addItem(self.roi_3)
        self.addItem(self.roi_4)

        #print(self.view.)

        # Creates mouse crosshair
        self.v_line = pg.InfiniteLine(angle=90, movable=False)
        self.h_line = pg.InfiniteLine(angle=0, movable=False)
        self.v_line.setVisible(False)
        self.h_line.setVisible(False)
        self.addItem(self.v_line, ignoreBounds=True)
        self.addItem(self.h_line, ignoreBounds=True)

    # --------------------------------------------------------------------------

    def displayImage(self, image, rect=None):

        """
        Adds image to plot window with correct options.
        """

        # Rotates image 270 degrees
        self.image = np.rot90(image, 3)
        c_map_max = np.amax(self.image) * self.cmap_pctl

        # Checks colormap scale
        if self.options_cmap_scale == "Log":
            norm = colors.LogNorm(vmax=c_map_max)
        else:
            norm = colors.Normalize(vmax=c_map_max)

        # Normalizes image
        norm_image = norm(self.image)

        # Adds colormap to image
        color_image = plt.cm.jet(norm_image)
        # Sets image
        self.image_item.setImage(color_image)

        if rect == None:
            rect = QtCore.QRect(0, 0, self.image.shape[0], self.image.shape[1])

        self.image_item.setRect(rect)
        self.rect = rect

        # Update analysis textboxes
        self.main_window.analysis_widget.setEnabled(True)
        self.main_window.analysis_widget.image_width_txtbox.setText(str(self.image.shape[0]))
        self.main_window.analysis_widget.image_height_txtbox.setText(str(self.image.shape[1]))
        self.main_window.analysis_widget.image_max_intensity_txtbox.setText(str(round(np.amax(self.image))))
        self.main_window.analysis_widget.image_cmap_pctl_txtbox.setText(str(self.cmap_pctl))

        # Update crosshair information
        self.view.scene().sigMouseMoved.connect(self.updateMouseCrosshair)
        self.view.scene().sigMouseMoved.connect(self.updateHKLTextboxes)

    # --------------------------------------------------------------------------

    def updateMouseCrosshair(self, scene_point):

        """
        Changes crosshair information and updates lines.
        """

        # View coordinates to plot coordinates
        view_point = self.view.mapSceneToView(scene_point)

        x, y = view_point.x(), view_point.y()

        # Changes position of crosshair
        self.v_line.setPos(x)
        self.h_line.setPos(y)

        # Update analysis textboxes
        self.main_window.analysis_widget.mouse_x_txtbox.setText(str(round(x, 5)))
        self.main_window.analysis_widget.mouse_y_txtbox.setText(str(round(y, 5)))

        x = (x - self.rect.x()) * self.image.shape[0] / self.rect.width()
        y = (y - self.rect.y()) * self.image.shape[1] / self.rect.height()

        # Checks if mouse is within confines of image
        if self.image.shape[0] >= x >= 0 and self.image.shape[1] >= y >= 0:
            intensity = round(self.image[int(x), int(y)])
            self.main_window.analysis_widget.mouse_intensity_txtbox.setText(str(intensity))

    # --------------------------------------------------------------------------

    def updateHKLTextboxes(self, scene_point):

        if self.main_window.options_widget.post_hkl_rbtn.isChecked():
            view_point = self.view.mapSceneToView(scene_point)

            x, y = view_point.x(), view_point.y()
            z = self.main_window.options_widget.post_slice_sbox.value()

            if self.main_window.options_widget.post_slice_direction_cbox.currentText() == "X(H)":
                self.main_window.analysis_widget.mouse_h_txtbox.setText(str(round(z, 5)))
                self.main_window.analysis_widget.mouse_k_txtbox.setText(str(round(y, 5)))
                self.main_window.analysis_widget.mouse_l_txtbox.setText(str(round(x, 5)))
            elif self.main_window.options_widget.post_slice_direction_cbox.currentText() == "Y(K)":
                self.main_window.analysis_widget.mouse_h_txtbox.setText(str(round(y, 5)))
                self.main_window.analysis_widget.mouse_k_txtbox.setText(str(round(z, 5)))
                self.main_window.analysis_widget.mouse_l_txtbox.setText(str(round(x, 5)))
            else:
                self.main_window.analysis_widget.mouse_h_txtbox.setText(str(round(y, 5)))
                self.main_window.analysis_widget.mouse_k_txtbox.setText(str(round(x, 5)))
                self.main_window.analysis_widget.mouse_l_txtbox.setText(str(round(z, 5)))
        else:
            self.main_window.analysis_widget.mouse_h_txtbox.setText("")
            self.main_window.analysis_widget.mouse_k_txtbox.setText("")
            self.main_window.analysis_widget.mouse_l_txtbox.setText("")

# ==============================================================================

class ROIWidget(pg.ROI):

    """
    Contains ROI for viewing window and layout for its respective groupbox in the
    analysis widget.
    """

    def __init__ (self, position, size, layout, plot):
        super().__init__(position, size=size)

        self.layout = layout
        self.roi_plot = plot
        self.data = []
        self.slice_direction = ""
        self.rect = None

        self.roi_plot.setLabel("left", "Avg Intensity")
        self.roi_plot.setLabel("bottom", "Slice")

        self.pen = pg.mkPen(width=3)
        self.setPen(self.pen)

        # For vertical, horizontal, and diagonal scaling
        self.addScaleHandle([0.5, 0], [0.5, 0.5])
        self.addScaleHandle([0, 0.5], [0.5, 0.5])
        self.addScaleHandle([0, 0], [0.5, 0.5])

        # Intially hide the ROI
        self.hide()

        # Creates subwidgets for groupbox
        self.x_lbl = QtGui.QLabel("x Pos:")
        self.x_spinbox = QtGui.QDoubleSpinBox()
        self.x_spinbox.setMinimum(0)
        self.x_spinbox.setMaximum(1000)
        self.x_spinbox.setDecimals(5)
        self.y_lbl = QtGui.QLabel("y Pos:")
        self.y_spinbox = QtGui.QDoubleSpinBox()
        self.y_spinbox.setMinimum(0)
        self.y_spinbox.setMaximum(1000)
        self.y_spinbox.setDecimals(5)
        self.width_lbl = QtGui.QLabel("Width:")
        self.width_spinbox = QtGui.QDoubleSpinBox()
        self.width_spinbox.setMinimum(0)
        self.width_spinbox.setMaximum(1000)
        self.width_spinbox.setDecimals(5)
        self.height_lbl = QtGui.QLabel("Height:")
        self.height_spinbox = QtGui.QDoubleSpinBox()
        self.height_spinbox.setMinimum(0)
        self.height_spinbox.setMaximum(1000)
        self.height_spinbox.setDecimals(5)
        self.color_btn = pg.ColorButton()

        # Adds subwidgets to layout
        self.layout.addWidget(self.x_lbl, 0, 0)
        self.layout.addWidget(self.x_spinbox, 0, 1)
        self.layout.addWidget(self.y_lbl, 1, 0)
        self.layout.addWidget(self.y_spinbox, 1, 1)
        self.layout.addWidget(self.width_lbl, 2, 0)
        self.layout.addWidget(self.width_spinbox, 2, 1)
        self.layout.addWidget(self.height_lbl, 3, 0)
        self.layout.addWidget(self.height_spinbox, 3, 1)
        self.layout.addWidget(self.color_btn, 4, 0, 1, 2)

        # Connects subwidgets to signals
        self.sigRegionChanged.connect(self.updateAnalysis)
        self.visibleChanged.connect(self.updateAnalysis)
        self.width_spinbox.valueChanged.connect(self.updateSize)
        self.height_spinbox.valueChanged.connect(self.updateSize)
        self.x_spinbox.valueChanged.connect(self.updatePosition)
        self.y_spinbox.valueChanged.connect(self.updatePosition)
        self.color_btn.sigColorChanged.connect(self.changeColor)

        # Keeps track of whether textboxes or roi was updated last
        # Helps avoid infinite loop of updating
        # Acts like a semaphore of sorts
        self.updating = ""

    # --------------------------------------------------------------------------

    def updateAnalysis(self):

        """
        Updates spinboxes in analysis widget and ROI plots.
        """

        if self.updating != "roi":
            self.updating = "analysis"
            self.x_spinbox.setValue(self.pos()[0] + self.size()[0] / 2)
            self.y_spinbox.setValue(self.pos()[1] + self.size()[1] / 2)
            self.width_spinbox.setValue(self.size()[0])
            self.height_spinbox.setValue(self.size()[1])
            self.updating = ""

        self.plotAverageIntensity(self.data, self.slice_direction, self.rect)

    # --------------------------------------------------------------------------

    def updateSize(self):

        """
        Updates ROI size in viewing window.
        """

        if self.updating != "analysis":
            self.updating = "roi"
            width = self.width_spinbox.value()
            height = self.height_spinbox.value()
            self.setSize((width, height))
            self.updatePosition()
            self.updating = ""

    # --------------------------------------------------------------------------

    def updatePosition(self):

        """
        Updates ROI position in viewing window.
        """

        if self.updating != "analysis":
            self.updating = "roi"
            # Bottom lefthand corner of roi
            x_origin = self.x_spinbox.value() - self.size()[0] / 2
            y_origin = self.y_spinbox.value() - self.size()[1] / 2
            self.setPos((x_origin, y_origin))
            self.updating = ""

    # --------------------------------------------------------------------------

    def changeColor(self):

        """
        Changes ROI box color.
        """

        color = self.color_btn.color()

        self.setPen(pg.mkPen(color, width=3))

    # --------------------------------------------------------------------------

    def plotAverageIntensity(self, data, slice_direction, rect):

        """
        Creates list of avg pixel intensities from ROI through set of images.
        """

        self.data = data
        self.slice_direction = slice_direction
        self.rect = rect

        if self.data != [] and self.rect != None:

            x_min = int((self.pos()[0] - self.rect.x()) * self.data.shape[0] / self.rect.width())
            x_max = int((self.pos()[0] + self.size()[0] - self.rect.x()) * self.data.shape[0] / self.rect.width())
            y_min = int((self.pos()[1] - self.rect.y()) * self.data.shape[1] / self.rect.height())
            y_max = int((self.pos()[1] + self.size()[1] - self.rect.y()) * self.data.shape[1] / self.rect.height())

            if self.slice_direction == "X(H)":
                data_roi = self.data[:, y_min:y_max, x_min:x_max]
                avg_intensity = []

                for i in range(data_roi.shape[0]):
                    avg = np.mean(data_roi[i, :, :])
                    avg_intensity.append(avg)

            elif self.slice_direction == "Y(K)":
                data_roi = self.data[y_min:y_max, :, x_min:x_max]
                avg_intensity = []

                for i in range(data_roi.shape[1]):
                    avg = np.mean(data_roi[:, i, :])
                    avg_intensity.append(avg)

            elif self.slice_direction == "Z(L)":
                data_roi = self.data[y_min:y_max, x_min:x_max, :]
                avg_intensity = []

                for i in range(data_roi.shape[2]):
                    avg = np.mean(data_roi[:, :, i])
                    avg_intensity.append(avg)

            self.avg_intensity = avg_intensity
            self.roi_plot.plot(avg_intensity, clear=True)

# ==============================================================================

class ROIPlotsWidget(pg.GraphicsLayoutWidget):

    """
    Contains average intensity plots for ROI's. Plots only work with post mode.
    """

    def __init__ (self, parent, title="Average Intensity"):
        super(ROIPlotsWidget, self).__init__(parent)
        self.main_window = parent

        self.roi_1_plot = self.addPlot(title="ROI 1")
        self.roi_2_plot = self.addPlot(title="ROI 2")
        self.nextRow()
        self.roi_3_plot = self.addPlot(title="ROI 3")
        self.roi_4_plot = self.addPlot(title="ROI 4")

    # --------------------------------------------------------------------------

    def displayROIPlots(self, data, slice_direction, rect):

        """
        Uses data to display avg intensities in all ROI plots. This function is
        only used for the initial display when a new dataset is loaded.
        """

        warnings.filterwarnings("ignore", category=RuntimeWarning)

        self.main_window.image_widget.roi_1.plotAverageIntensity(data, slice_direction, rect)
        self.main_window.image_widget.roi_2.plotAverageIntensity(data, slice_direction, rect)
        self.main_window.image_widget.roi_3.plotAverageIntensity(data, slice_direction, rect)
        self.main_window.image_widget.roi_4.plotAverageIntensity(data, slice_direction, rect)

    # --------------------------------------------------------------------------

    def clearROIPlots(self):

        """
        Clears all ROI plots.
        """
        self.roi_1_plot.clear()
        self.roi_2_plot.clear()
        self.roi_3_plot.clear()
        self.roi_4_plot.clear()

    # --------------------------------------------------------------------------

    def enableROIPlots(self):

        """
        Enables all ROI plots.
        """
        self.roi_1_plot.setEnabled(True)
        self.roi_2_plot.setEnabled(True)
        self.roi_3_plot.setEnabled(True)
        self.roi_4_plot.setEnabled(True)

    # --------------------------------------------------------------------------

    def disableROIPlots(self):

        """
        Disables all ROI plots.
        """
        self.roi_1_plot.setEnabled(False)
        self.roi_2_plot.setEnabled(False)
        self.roi_3_plot.setEnabled(False)
        self.roi_4_plot.setEnabled(False)

# ==============================================================================

class AdvancedROIPlotWidget(pg.PlotWidget):

    def __init__ (self, parent):
        super(AdvancedROIPlotWidget, self).__init__(parent)
        self.main_window = parent

        self.setLabel("left", "Avg Intensity")
        self.setLabel("bottom", "Slice")

        self.first_roi = None
        self.operator = None
        self.second_roi = None

        self.main_window.image_widget.roi_1.sigRegionChanged.connect(self.plotData)
        self.main_window.image_widget.roi_2.sigRegionChanged.connect(self.plotData)
        self.main_window.image_widget.roi_3.sigRegionChanged.connect(self.plotData)
        self.main_window.image_widget.roi_4.sigRegionChanged.connect(self.plotData)

    # --------------------------------------------------------------------------

    def getRegions(self, first_roi_name, operator, second_roi_name, title):
        self.first_roi = self.getCorrespondingROI(first_roi_name)
        self.operator = operator
        self.second_roi = self.getCorrespondingROI(second_roi_name)

        self.plotData()
        self.setTitle(title)

    # --------------------------------------------------------------------------

    def plotData(self):
        if not None in [self.first_roi, self.operator, self.second_roi]:
            first_avg_intensity = np.array(self.first_roi.avg_intensity)
            second_avg_intensity = np.array(self.second_roi.avg_intensity)

            if self.operator == "-":
                avg_intensity = np.subtract(first_avg_intensity, second_avg_intensity)

            self.plot(avg_intensity, clear=True)

    # --------------------------------------------------------------------------

    def getCorrespondingROI(self, roi_name):
        roi_dict = {
            "ROI 1" : self.main_window.image_widget.roi_1,
            "ROI 2" : self.main_window.image_widget.roi_2,
            "ROI 3" : self.main_window.image_widget.roi_3,
            "ROI 4" : self.main_window.image_widget.roi_4
        }

        return roi_dict[roi_name]