"""
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

# ==============================================================================

import pyqtgraph as pg
import matplotlib.colors as colors
import matplotlib.pyplot as plt
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import os
from scipy import ndimage
import tifffile as tiff
import time

from source.data_processing import * # Local

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
        self.post_slice_direction_lbl = QtGui.QLabel("Slice Direction:")
        self.post_slice_direction_cbox = QtGui.QComboBox()
        self.post_slice_direction_cbox.setEnabled(False)
        self.post_slice_sbox = QtGui.QSpinBox()
        self.post_slice_sbox.setEnabled(False)
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
        self.post_image_layout.addWidget(self.post_slice_direction_lbl, 6, 0, 1, 2)
        self.post_image_layout.addWidget(self.post_slice_direction_cbox, 6, 2, 1, 4)
        self.post_image_layout.addWidget(self.post_slice_sbox, 7, 0, 1, 1)
        self.post_image_layout.addWidget(self.post_slice_slider, 7, 1, 1, 5)

        # Post widget connections
        self.post_set_project_btn.clicked.connect(self.setDataSource)
        self.post_scan_list.itemClicked.connect(self.loadDataSource)

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

        # Options widget connections
        self.options_roi_chkbox.stateChanged.connect(self.toggleROIBoxes)
        self.options_crosshair_mouse_chkbox.stateChanged.connect(self.toggleMouseCrosshair)
        self.options_crosshair_color_btn.sigColorChanged.connect(self.changeCrosshairColor)
        self.options_mouse_pan_rbtn.toggled.connect(self.toggleMouseMode)
        self.options_mouse_rect_rbtn.toggled.connect(self.toggleMouseMode)
        self.options_bkgrd_black_rbtn.toggled.connect(self.togglebkgrdColor)
        self.options_bkgrd_white_rbtn.toggled.connect(self.togglebkgrdColor)
        self.options_cmap_linear_rbtn.toggled.connect(self.toggleCmapScale)
        self.options_cmap_log_rbtn.toggled.connect(self.toggleCmapScale)
        self.options_cmap_pctl_slider.valueChanged.connect(self.changeCmapPctl)
        self.options_aspect_ratio_auto_rbtn.toggled.connect(self.toggleAspectRatio)
        self.options_aspect_ratio_one_rbtn.toggled.connect(self.toggleAspectRatio)

    # --------------------------------------------------------------------------

    def liveSetScan(self):

        """
        Selects scan directory for live mode.
        """

        # Clear scan image list and resets coordinate system radio buttons
        self.live_image_list.clear()
        self.live_xyz_rbtn.setChecked(False)
        self.live_xyz_rbtn.setChecked(False)

        # Directory path containing scan images
        self.live_scan_path = QtGui.QFileDialog.getExistingDirectory(self,
            "Open Scan Directory")

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
        ...

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
        self.image = np.fliplr(tiff.imread(file_path))

        # Loads image into viewing window
        self.main_window.image_widget.displayImage(self.image, rect=None)

        # Sets file name as current image
        self.live_current_image_txtbox.setText(file_name.text())

        # Enable options
        self.options_gbox.setEnabled(True)

    # --------------------------------------------------------------------------

    def postSetProject(self):
        ...

    # --------------------------------------------------------------------------

    def postSetScanList(self):
        ...

    # --------------------------------------------------------------------------

    def postToggleSpecConfigButton(self):
        ...

    # --------------------------------------------------------------------------

    def postSetSpecConfigFiles(self):
        ...
    
    # --------------------------------------------------------------------------

    def postLoadImage(self):
        ...

    # --------------------------------------------------------------------------

    def setDataSource(self):

        """
        - Opens data source dialog
        - If directory is valid, scan subdirectories are shown in the list widget
        """

        # See DataSourceDialogWidget class for more info
        dialog = DataSourceDialogWidget()

        # If dialog return value == True
        if dialog:
            self.project = dialog.project_name
            self.spec = dialog.spec_name
            self.detector = dialog.detector_config_name
            self.instrument = dialog.instrument_config_name
            self.process_data = dialog.process_data

            # If project direcory is given
            if not self.project == "":

                # If project directory has image subdirectory
                if os.path.exists(os.path.join(self.project, "images")):
                    image_directory = os.path.join(self.project, "images")
                    # Image directory should only have one subdirectory
                    # Subdirectory should share name with .spec file
                    self.scan_directory = os.path.join(image_directory, os.listdir(image_directory)[0])
                    # Sorted alphabetically
                    scans = sorted(os.listdir(self.scan_directory))

                    # Clear current list items and add new list items
                    self.post_scan_list.clear()
                    self.post_scan_list.addItems(scans)

                    # Sets axis labels for image plot
                    self.main_window.image_widget.setLabel("left", "K")
                    self.main_window.image_widget.setLabel("bottom", "L")

    # --------------------------------------------------------------------------

    def loadDataSource(self, scan):

        """
        - Creates 3D array of data from given scan directory
        - Sets spinbox/slider limits based on array's dimensions
        """

        # Placeholder list for 3D array
        self.dataset = []

        # If spec and config directories were given (processed data)
        if not "" in [self.spec, self.detector, self.instrument]:
            # Last two chars (should be digits) of scan name
            scan = scan.text()[1:]

            # Creates vti file
            vti_file = DataProcessing.createVTIFile(self.project, self.spec, self.detector,
                self.instrument, scan)

            # Converts vti file into 3D array with proper axes
            self.axes, self.dataset = DataProcessing.loadData(vti_file)
            self.h_axis = [self.axes[0][0], self.axes[0][-1]]
            self.k_axis = [self.axes[1][0], self.axes[1][-1]]
            self.l_axis = [self.axes[2][0], self.axes[2][-1]]

            self.main_window.roi_plots_widget.clearROIPlots()

        # If only project directory was given (unprocessed data)
        else:
            # (Alphabetically) Sorted list of scan images
            scan_path = os.path.join(self.scan_directory, scan.text())
            self.image_files = sorted(os.listdir(scan_path))

            for i in range(len(self.image_files)):
                if self.image_files[i] != "alignment.tif":
                    # Creates 2d image from file path
                    file_path = f"{scan_path}/{self.image_files[i]}"
                    image = ndimage.rotate(tiff.imread(file_path), 90)
                    # Appends image to list of images
                    self.dataset.append(image)
            self.dataset = np.stack(self.dataset)
            self.dataset = np.swapaxes(self.dataset, 0, 2)

            # Axes go from 0 to shape of array in each direction
            self.h_axis = [0, self.dataset.shape[0]]
            self.k_axis = [0, self.dataset.shape[1]]
            self.l_axis = [0, self.dataset.shape[2]]

            self.main_window.roi_plots_widget.displayROIPlots(self.dataset)

        self.post_h_slider.setMaximum(self.dataset.shape[0] - 1)
        self.post_h_spinbox.setRange(0, self.dataset.shape[0] - 1)
        self.post_k_slider.setMaximum(self.dataset.shape[1] - 1)
        self.post_k_spinbox.setRange(0, self.dataset.shape[1] - 1)
        self.post_l_slider.setMaximum(self.dataset.shape[2] - 1)
        self.post_l_spinbox.setRange(0, self.dataset.shape[2] - 1)

        self.loadPostImage()


    # --------------------------------------------------------------------------

    def loadPostImage(self):

        """
        Loads image to viewing window.
        """

        # Splits axis into min/max
        h_min, h_max = self.h_axis
        k_min, k_max = self.k_axis
        l_min, l_max = self.l_axis

        # h direction
        if self.post_h_direction_rbtn.isChecked():
            # Syncs slider and spinbox
            self.post_h_spinbox.setValue(int(self.post_h_slider.value()))
            # Creates rectangle for array to be plotted inside of
            rect = QtCore.QRectF(l_min, k_min, l_max - l_min, k_max - k_min)
            h_slice = int(self.post_h_slider.value())
            self.image = self.dataset[h_slice, :, :]

        # k direction
        elif self.post_k_direction_rbtn.isChecked():
            self.post_k_spinbox.setValue(int(self.post_k_slider.value()))
            rect = QtCore.QRectF(l_min, h_min, l_max - l_min, h_max - h_min)
            k_slice = int(self.post_k_slider.value())
            self.image = self.dataset[:, k_slice, :]

        # l direction
        else:
            self.post_l_spinbox.setValue(int(self.post_l_slider.value()))
            rect = QtCore.QRectF(k_min, h_min, k_max - k_min, h_max - h_min)
            l_slice = int(self.post_l_slider.value())
            self.image = self.dataset[:, :, l_slice]

        # Sets image in viewing window
        self.main_window.image_widget.displayImage(self.image, rect=rect)

        # Enable options
        self.options_gbox.setEnabled(True)

    # --------------------------------------------------------------------------

    def toggleSliceDirection(self):

        """
        Toggles direction of data slice for post mode plotting.
        """

        button = self.sender()

        if button.text() == "H":
            self.post_h_slider.setEnabled(True)
            self.post_k_slider.setEnabled(False)
            self.post_l_slider.setEnabled(False)
            self.main_window.image_widget.setLabel("left", "K")
            self.main_window.image_widget.setLabel("bottom", "L")
        elif button.text() == "K":
            self.post_h_slider.setEnabled(False)
            self.post_k_slider.setEnabled(True)
            self.post_l_slider.setEnabled(False)
            self.main_window.image_widget.setLabel("left", "H")
            self.main_window.image_widget.setLabel("bottom", "L")
        else:
            self.post_h_slider.setEnabled(False)
            self.post_k_slider.setEnabled(False)
            self.post_l_slider.setEnabled(True)
            self.main_window.image_widget.setLabel("left", "H")
            self.main_window.image_widget.setLabel("bottom", "K")

        # Loads new image into viewing window
        self.loadPostImage()

    # --------------------------------------------------------------------------

    def changeSliderValue(self, value):

        """
        Toggles data slice for post mode plotting.
        """

        spinbox = self.sender()

        if spinbox == self.post_h_spinbox:
            self.post_h_slider.setValue(value)
        elif spinbox == self.post_k_spinbox:
            self.post_k_slider.setValue(value)
        else:
            self.post_l_slider.setValue(value)

        # No need to call loadPostImage()
        # Connected with valueChanged signal that calls loadPostImage()

    # --------------------------------------------------------------------------

    def toggleROIBoxes(self, state):

        """
        Toggles visibility for ROI boxes.
        """

        # 2 = checked
        if state == 2:
            self.main_window.image_widget.roi1.show()
            self.main_window.image_widget.roi2.show()
            self.main_window.image_widget.roi3.show()
            self.main_window.image_widget.roi4.show()
        else:
            self.main_window.image_widget.roi1.hide()
            self.main_window.image_widget.roi2.hide()
            self.main_window.image_widget.roi3.hide()
            self.main_window.image_widget.roi4.hide()



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

    def togglebkgrdColor(self):

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
        self.roi1_gbox = QtGui.QGroupBox("ROI 1")
        self.roi2_gbox = QtGui.QGroupBox("ROI 2")
        self.roi3_gbox = QtGui.QGroupBox("ROI 3")
        self.roi4_gbox = QtGui.QGroupBox("ROI 4")

        # Add GroupBoxes to widget
        self.addWidget(self.mouse_gbox, row=0, col=0, rowspan=1)
        self.addWidget(self.image_gbox, row=1, col=0, rowspan=1)
        self.addWidget(self.roi1_gbox, row=0, col=1, rowspan=2)
        self.addWidget(self.roi2_gbox, row=0, col=2, rowspan=2)
        self.addWidget(self.roi3_gbox, row=0, col=3, rowspan=2)
        self.addWidget(self.roi4_gbox, row=0, col=4, rowspan=2)

        # Create/add layouts
        self.mouse_layout = QtGui.QGridLayout()
        self.image_layout = QtGui.QGridLayout()
        self.roi_1_layout = QtGui.QGridLayout()
        self.roi_2_layout = QtGui.QGridLayout()
        self.roi_3_layout = QtGui.QGridLayout()
        self.roi_4_layout = QtGui.QGridLayout()
        self.mouse_gbox.setLayout(self.mouse_layout)
        self.image_gbox.setLayout(self.image_layout)
        self.roi1_gbox.setLayout(self.roi_1_layout)
        self.roi2_gbox.setLayout(self.roi_2_layout)
        self.roi3_gbox.setLayout(self.roi_3_layout)
        self.roi4_gbox.setLayout(self.roi_4_layout)

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
        self.roi1 = ROIWidget([200, 100], [40, 40], roi_1_layout, roi_1_plot)
        self.roi2 = ROIWidget([210, 110], [30, 30], roi_2_layout, roi_2_plot)
        self.roi3 = ROIWidget([220, 120], [20, 20], roi_3_layout, roi_3_plot)
        self.roi4 = ROIWidget([230, 130], [10, 10], roi_4_layout, roi_4_plot)
        self.addItem(self.roi1)
        self.addItem(self.roi2)
        self.addItem(self.roi3)
        self.addItem(self.roi4)

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

        # Checks colormap scale
        if self.options_cmap_scale == "Log":
            norm = colors.LogNorm(vmax=np.amax(self.image)*self.cmap_pctl)
        else:
            norm = colors.Normalize(vmax=np.amax(self.image)*self.cmap_pctl)

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
        self.main_window.analysis_widget.image_width_txtbox.setText(str(self.image.shape[0]))
        self.main_window.analysis_widget.image_height_txtbox.setText(str(self.image.shape[1]))
        self.main_window.analysis_widget.image_max_intensity_txtbox.setText(str(round(np.amax(self.image))))
        self.main_window.analysis_widget.image_cmap_pctl_txtbox.setText(str(self.cmap_pctl))

        # Update crosshair information
        self.view.scene().sigMouseMoved.connect(self.updateMouseCrosshair)

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

    def displayROIPlots(self, data):

        """
        Uses data to display avg intensities in all ROI plots. This function is
        only used for the initial display when a new dataset is loaded.
        """

        self.main_window.image_widget.roi1.plotAverageIntensity(data)
        self.main_window.image_widget.roi2.plotAverageIntensity(data)
        self.main_window.image_widget.roi3.plotAverageIntensity(data)
        self.main_window.image_widget.roi4.plotAverageIntensity(data)

    # --------------------------------------------------------------------------

    def clearROIPlots(self):

        """
        Clears all ROI plots.
        """
        self.roi_1_plot.clear()
        self.roi_2_plot.clear()
        self.roi_3_plot.clear()
        self.roi_4_plot.clear()

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

        self.roi_plot.setLabel("left", "Avg Intensity")
        self.roi_plot.setLabel("bottom", "L Slice")

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
        self.y_lbl = QtGui.QLabel("y Pos:")
        self.y_spinbox = QtGui.QDoubleSpinBox()
        self.y_spinbox.setMinimum(0)
        self.y_spinbox.setMaximum(1000)
        self.width_lbl = QtGui.QLabel("Width:")
        self.width_spinbox = QtGui.QDoubleSpinBox()
        self.width_spinbox.setMinimum(0)
        self.width_spinbox.setMaximum(1000)
        self.height_lbl = QtGui.QLabel("Height:")
        self.height_spinbox = QtGui.QDoubleSpinBox()
        self.height_spinbox.setMinimum(0)
        self.height_spinbox.setMaximum(1000)
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

        self.plotAverageIntensity(self.data)

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

    def plotAverageIntensity(self, data):

        """
        Creates list of avg pixel intensities from ROI through set of images.
        """

        self.data = data

        if self.data != []:
            x_min = int(self.pos()[0])
            x_max = int(self.pos()[0] + self.size()[0])
            y_min = int(self.pos()[1])
            y_max = int(self.pos()[1] + self.size()[1])

            data_roi = self.data[y_min:y_max, x_min:x_max, :]
            avg_intensity = []

            for i in range(data_roi.shape[2]):
                avg = np.mean(data_roi[:, :, i])
                avg_intensity.append(avg)

            self.roi_plot.plot(avg_intensity, clear=True)

# ==============================================================================

class DataSourceDialogWidget(QtGui.QDialog):

    """
    Creates modal dialog widget for the user to choose directories and files as
    their data source.
    """

    def __init__ (self):
        super().__init__()

        self.setWindowModality(QtCore.Qt.ApplicationModal)

        # Holds values from textboxes/checkbox
        self.project_name = ""
        self.spec_name = ""
        self.detector_config_name = ""
        self.instrument_config_name = ""
        self.process_data = False
        self.ok = False

        # Creates subwidgets
        self.process_data_chkbox = QtGui.QCheckBox("Process Data")
        self.project_lbl = QtGui.QLabel("Project:")
        self.project_txtbox = QtGui.QLineEdit()
        self.project_txtbox.setReadOnly(True)
        self.project_btn = QtGui.QPushButton("Browse")
        self.spec_lbl = QtGui.QLabel("spec File:")
        self.spec_txtbox = QtGui.QLineEdit()
        self.spec_txtbox.setReadOnly(True)
        self.spec_btn = QtGui.QPushButton("Browse")
        self.spec_btn.setEnabled(False)
        self.detector_lbl = QtGui.QLabel("Det. Config:")
        self.detector_txtbox = QtGui.QLineEdit()
        self.detector_txtbox.setReadOnly(True)
        self.detector_btn = QtGui.QPushButton("Browse")
        self.detector_btn.setEnabled(False)
        self.instrument_lbl = QtGui.QLabel("Instr. Config:")
        self.instrument_txtbox = QtGui.QLineEdit()
        self.instrument_txtbox.setReadOnly(True)
        self.instrument_btn = QtGui.QPushButton("Browse")
        self.instrument_btn.setEnabled(False)
        self.dialog_btnbox = QtGui.QDialogButtonBox()
        self.dialog_btnbox.addButton("OK", QtGui.QDialogButtonBox.AcceptRole)

        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)

        # Adds widgets to layout
        self.layout.addWidget(self.project_lbl, 0, 0)
        self.layout.addWidget(self.project_txtbox, 0, 1, 1, 3)
        self.layout.addWidget(self.project_btn, 0, 4)
        self.layout.addWidget(self.spec_lbl, 1, 0)
        self.layout.addWidget(self.spec_txtbox, 1, 1, 1, 3)
        self.layout.addWidget(self.spec_btn, 1, 4)
        self.layout.addWidget(self.detector_lbl, 2, 0)
        self.layout.addWidget(self.detector_txtbox, 2, 1, 1, 3)
        self.layout.addWidget(self.detector_btn, 2, 4)
        self.layout.addWidget(self.instrument_lbl, 3, 0)
        self.layout.addWidget(self.instrument_txtbox, 3, 1, 1, 3)
        self.layout.addWidget(self.instrument_btn, 3, 4)
        self.layout.addWidget(self.process_data_chkbox, 4, 0)
        self.layout.addWidget(self.dialog_btnbox, 4, 3, 1, 2)

        # Connects widgets to functions
        self.project_btn.clicked.connect(self.selectProject)
        self.spec_btn.clicked.connect(self.selectSpecFile)
        self.detector_btn.clicked.connect(self.selectDetectorConfigFile)
        self.instrument_btn.clicked.connect(self.selectInstrumentConfigFile)
        self.process_data_chkbox.stateChanged.connect(self.setDataProcessingStatus)
        self.dialog_btnbox.accepted.connect(self.accept)

        # Runs dialog widget
        self.exec_()

    # --------------------------------------------------------------------------

    def selectProject(self):
        project = QtGui.QFileDialog.getExistingDirectory(self)
        self.project_name = project
        self.project_txtbox.setText(project)

    # --------------------------------------------------------------------------

    def selectSpecFile(self):
        spec = QtGui.QFileDialog.getOpenFileName(self, "", "", "spec Files (*.spec)")
        self.spec_name = spec[0]
        self.spec_txtbox.setText(spec[0])

    # --------------------------------------------------------------------------

    def selectDetectorConfigFile(self):
        detector = QtGui.QFileDialog.getOpenFileName(self, "", "", "xml Files (*.xml)")
        self.detector_config_name = detector[0]
        self.detector_txtbox.setText(detector[0])

    # --------------------------------------------------------------------------

    def selectInstrumentConfigFile(self):
        instrument = QtGui.QFileDialog.getOpenFileName(self, "", "", "xml Files (*.xml)")
        self.instrument_config_name = instrument[0]
        self.instrument_txtbox.setText(instrument[0])

    # --------------------------------------------------------------------------

    def setDataProcessingStatus(self):

        """
        Changes the enabled status of certain widgets based on the checkbox's state.
        """

        checkbox = self.sender()

        if checkbox.checkState():
            self.process_data = True
            self.spec_btn.setEnabled(True)
            self.detector_btn.setEnabled(True)
            self.instrument_btn.setEnabled(True)
        else:
            self.process_data = False
            self.spec_btn.setEnabled(False)
            self.detector_btn.setEnabled(False)
            self.instrument_btn.setEnabled(False)

# ==============================================================================
