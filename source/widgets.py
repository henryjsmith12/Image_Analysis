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
            - ROI toggle/** TODO: color picker
            - Mouse crosshair toggle
            - Mouse zoom/pan mode toggle
            - Background color toggle
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

        self.live_browse_btn = QtGui.QPushButton("Browse")
        self.live_clear_btn = QtGui.QPushButton("Clear")
        self.live_file_list = QtGui.QListWidget()
        self.live_current_file_lbl = QtGui.QLabel("Current Image:")
        self.live_current_file_txtbox = QtGui.QLineEdit()
        self.live_current_file_txtbox.setReadOnly(True)
        self.live_plot_btn = QtGui.QPushButton("Simulate Live Plotting")
        self.live_refresh_rate_lbl = QtGui.QLabel("Refresh Delay (s):")
        self.live_refresh_rate_spinbox = QtGui.QDoubleSpinBox()
        self.live_refresh_rate_spinbox.setSingleStep(0.01)
        self.live_refresh_rate_spinbox.setRange(0.0, 1.0)
        self.live_refresh_rate_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.live_refresh_rate_slider.setRange(0, 100)
        self.live_refresh_rate = 0.0

        # Create post mode widgets
        self.post_data_source_btn = QtGui.QPushButton("Set Data Source")
        self.post_data_source_list = QtGui.QListWidget()
        self.post_current_directory_lbl = QtGui.QLabel("Current Scan:")
        self.post_current_directory_txtbox = QtGui.QLineEdit()
        self.post_current_directory_txtbox.setReadOnly(True)
        self.post_direction_lbl = QtGui.QLabel("Slice Direction:")
        self.post_direction_group = QtGui.QButtonGroup()
        self.post_h_direction_rbtn = QtGui.QRadioButton("H")
        self.post_h_direction_rbtn.setChecked(True)
        self.post_k_direction_rbtn = QtGui.QRadioButton("K")
        self.post_l_direction_rbtn = QtGui.QRadioButton("L")
        self.post_direction_group.addButton(self.post_h_direction_rbtn)
        self.post_direction_group.addButton(self.post_k_direction_rbtn)
        self.post_direction_group.addButton(self.post_l_direction_rbtn)
        self.post_h_slider_lbl = QtGui.QLabel("H Slice:")
        self.post_h_spinbox = QtGui.QSpinBox()
        self.post_h_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.post_h_slider.setTickPosition(QtGui.QSlider.TicksBothSides)
        self.post_k_slider_lbl = QtGui.QLabel("K Slice:")
        self.post_k_spinbox = QtGui.QSpinBox()
        self.post_k_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.post_k_slider.setTickPosition(QtGui.QSlider.TicksBothSides)
        self.post_k_slider.setEnabled(False)
        self.post_l_slider_lbl = QtGui.QLabel("L Slice:")
        self.post_l_spinbox = QtGui.QSpinBox()
        self.post_l_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.post_l_slider.setTickPosition(QtGui.QSlider.TicksBothSides)
        self.post_l_slider.setEnabled(False)

        # Create options widgets
        self.roi_boxes_chkbox = QtGui.QCheckBox("ROI")
        self.roi_color_btn = pg.ColorButton()
        self.crosshair_mouse_chkbox = QtGui.QCheckBox("Crosshair")
        self.crosshair_color_btn = pg.ColorButton()
        self.mouse_mode_lbl = QtGui.QLabel("Mouse Mode:")
        self.mouse_mode_group = QtGui.QButtonGroup()
        self.mouse_pan_rbtn = QtGui.QRadioButton("Pan")
        self.mouse_pan_rbtn.setChecked(True)
        self.mouse_rect_rbtn = QtGui.QRadioButton("Rectangle")
        self.mouse_mode_group.addButton(self.mouse_pan_rbtn)
        self.mouse_mode_group.addButton(self.mouse_rect_rbtn)
        self.background_color_lbl = QtGui.QLabel("Background Color:")
        self.background_color_group = QtGui.QButtonGroup()
        self.background_black_rbtn = QtGui.QRadioButton("Black")
        self.background_black_rbtn.setChecked(True)
        self.background_white_rbtn = QtGui.QRadioButton("White")
        self.background_color_group.addButton(self.background_black_rbtn)
        self.background_color_group.addButton(self.background_white_rbtn)
        self.cmap_scale_lbl = QtGui.QLabel("CMap Scale:")
        self.cmap_scale_group = QtGui.QButtonGroup()
        self.cmap_linear_rbtn = QtGui.QRadioButton("Linear")
        self.cmap_linear_rbtn.setChecked(True)
        self.cmap_log_rbtn = QtGui.QRadioButton("Logarithmic")
        self.cmap_scale_group.addButton(self.cmap_linear_rbtn)
        self.cmap_scale_group.addButton(self.cmap_log_rbtn)
        self.cmap_pctl_lbl = QtGui.QLabel("CMap Pctl:")
        self.cmap_pctl_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.cmap_pctl_slider.setMinimum(1)
        self.cmap_pctl_slider.setMaximum(100)
        self.cmap_pctl_slider.setSingleStep(10)
        self.cmap_pctl_slider.setTickInterval(10)
        self.cmap_pctl_slider.setTickPosition(QtGui.QSlider.TicksBothSides)
        self.cmap_pctl_slider.setValue(100)

        # Add widgets to GroupBoxes
        self.live_image_layout.addWidget(self.live_browse_btn, 0, 0, 1, 2)
        self.live_image_layout.addWidget(self.live_clear_btn, 0, 2, 1, 2)
        self.live_image_layout.addWidget(self.live_file_list, 1, 0, 3, 4)
        self.live_image_layout.addWidget(self.live_current_file_lbl, 4, 0)
        self.live_image_layout.addWidget(self.live_current_file_txtbox, 4, 1, 1, 3)
        self.live_image_layout.addWidget(self.live_plot_btn, 5, 0, 1, 2)
        self.live_image_layout.addWidget(self.live_refresh_rate_lbl, 5, 2)
        self.live_image_layout.addWidget(self.live_refresh_rate_spinbox, 5, 3)

        self.post_image_layout.addWidget(self.post_data_source_btn, 0, 0, 1, 2)
        self.post_image_layout.addWidget(self.post_data_source_list, 1, 0, 3, 5)
        self.post_image_layout.addWidget(self.post_current_directory_lbl, 4, 0)
        self.post_image_layout.addWidget(self.post_current_directory_txtbox, 4, 1, 1, 4)
        self.post_image_layout.addWidget(self.post_direction_lbl, 5, 0)
        self.post_image_layout.addWidget(self.post_h_direction_rbtn, 5, 1)
        self.post_image_layout.addWidget(self.post_k_direction_rbtn, 5, 2)
        self.post_image_layout.addWidget(self.post_l_direction_rbtn, 5, 3)
        self.post_image_layout.addWidget(self.post_h_slider_lbl, 6, 0)
        self.post_image_layout.addWidget(self.post_h_spinbox, 6, 1)
        self.post_image_layout.addWidget(self.post_h_slider, 6, 2, 1, 3)
        self.post_image_layout.addWidget(self.post_k_slider_lbl, 7, 0)
        self.post_image_layout.addWidget(self.post_k_spinbox, 7, 1)
        self.post_image_layout.addWidget(self.post_k_slider, 7, 2, 1, 3)
        self.post_image_layout.addWidget(self.post_l_slider_lbl, 8, 0)
        self.post_image_layout.addWidget(self.post_l_spinbox, 8, 1)
        self.post_image_layout.addWidget(self.post_l_slider, 8, 2, 1, 3)
        self.options_layout.addWidget(self.roi_boxes_chkbox, 0, 0)
        self.options_layout.addWidget(self.crosshair_mouse_chkbox, 0, 1)
        self.options_layout.addWidget(self.crosshair_color_btn, 0, 2)
        self.options_layout.addWidget(self.mouse_mode_lbl, 2, 0)
        self.options_layout.addWidget(self.mouse_pan_rbtn, 2, 1)
        self.options_layout.addWidget(self.mouse_rect_rbtn, 2, 2)
        self.options_layout.addWidget(self.background_color_lbl, 3, 0)
        self.options_layout.addWidget(self.background_black_rbtn, 3, 1)
        self.options_layout.addWidget(self.background_white_rbtn, 3, 2)
        self.options_layout.addWidget(self.cmap_scale_lbl, 4, 0)
        self.options_layout.addWidget(self.cmap_linear_rbtn, 4, 1)
        self.options_layout.addWidget(self.cmap_log_rbtn, 4, 2)
        self.options_layout.addWidget(self.cmap_pctl_lbl, 5, 0)
        self.options_layout.addWidget(self.cmap_pctl_slider, 5, 1, 1, 2)

        # Link widgets to actions
        self.live_browse_btn.clicked.connect(self.openDirectory)
        self.live_clear_btn.clicked.connect(self.clear)
        self.live_file_list.itemClicked.connect(self.loadLiveImage)
        self.live_plot_btn.clicked.connect(self.simLivePlotting)
        self.live_refresh_rate_spinbox.valueChanged.connect(self.changeRefreshRate)

        self.post_data_source_btn.clicked.connect(self.setDataSource)
        self.post_data_source_list.itemClicked.connect(self.loadDataSource)
        self.post_h_direction_rbtn.toggled.connect(self.toggleSliceDirection)
        self.post_k_direction_rbtn.toggled.connect(self.toggleSliceDirection)
        self.post_l_direction_rbtn.toggled.connect(self.toggleSliceDirection)
        self.post_h_spinbox.valueChanged[int].connect(self.changeSliderValue)
        self.post_k_spinbox.valueChanged[int].connect(self.changeSliderValue)
        self.post_l_spinbox.valueChanged[int].connect(self.changeSliderValue)
        self.post_h_slider.valueChanged.connect(self.loadPostImage)
        self.post_k_slider.valueChanged.connect(self.loadPostImage)
        self.post_l_slider.valueChanged.connect(self.loadPostImage)
        self.roi_boxes_chkbox.stateChanged.connect(self.toggleROIBoxes)
        self.crosshair_mouse_chkbox.stateChanged.connect(self.toggleMouseCrosshair)
        self.crosshair_color_btn.sigColorChanged.connect(self.changeCrosshairColor)
        self.mouse_pan_rbtn.toggled.connect(self.toggleMouseMode)
        self.mouse_rect_rbtn.toggled.connect(self.toggleMouseMode)
        self.background_black_rbtn.toggled.connect(self.toggleBackgroundColor)
        self.background_white_rbtn.toggled.connect(self.toggleBackgroundColor)
        self.cmap_linear_rbtn.toggled.connect(self.toggleCmapScale)
        self.cmap_log_rbtn.toggled.connect(self.toggleCmapScale)
        self.cmap_pctl_slider.valueChanged.connect(self.changeCmapPctl)

    # --------------------------------------------------------------------------

    def openDirectory(self):

        """
        - Selects directory for both live and post modes
        - Loads data for post mode
        """

        # Find directory with image files
        self.directory = QtGui.QFileDialog.getExistingDirectory(self, "Open Folder")

        # (Alphabetically) Sorted list of files
        self.image_files = sorted(os.listdir(self.directory))

        # For post mode plotting
        self.image_data = []

        # Live mode
        if self.live_image_gbox is self.image_mode_tabs.currentWidget():
            # Clear current directory and display new directory
            # Images can be view by clicking name
            self.live_file_list.clear()
            self.live_file_list.addItems(self.image_files)

        # Post mode
        else:
            # Display directory name in textbox
            self.post_current_directory_txtbox.setText(self.directory)
            # Loop through images in selected directory
            for i in range(len(self.image_files)):
                if self.image_files[i] != "alignment.tif":
                    # Creates 2d image from file path
                    file_path = f"{self.directory}/{self.image_files[i]}"
                    image = ndimage.rotate(tiff.imread(file_path), 90)
                    # Appends image to list of images
                    self.image_data.append(image)

            # Converts list of 2d images to 3d array
            self.image_data = np.stack(self.image_data)

            # Sets limits for sliders and spinboxes
            self.post_h_slider.setMaximum(self.image_data.shape[0] - 1)
            self.post_h_spinbox.setRange(0, self.image_data.shape[0] - 1)
            self.post_k_slider.setMaximum(self.image_data.shape[1] - 1)
            self.post_k_spinbox.setRange(0, self.image_data.shape[1] - 1)
            self.post_l_slider.setMaximum(self.image_data.shape[2] - 1)
            self.post_l_spinbox.setRange(0, self.image_data.shape[2] - 1)

            # Creates plots of average intesity for each ROI
            self.main_window.roi_plots_widget.displayROIPlots()

            # Loads 3d array into viewing window
            self.loadPostImage()

    # --------------------------------------------------------------------------

    def clear(self):

        """
        Clears images from viewing window and file list
        """

        self.file_list.clear()

        # Clear plots
        self.main_window.image_widget.clear()
        self.main_window.x_plot_widget.clear()
        self.main_window.y_plot_widget.clear()

        self.current_file_txtbox.setText("")

        # Disbale options
        self.options_gbox.setEnabled(False)

    # --------------------------------------------------------------------------

    def loadLiveImage(self, file):

        """
        Loads image to viewing window.
        """

        # Concatenates directory and file names
        self.file_path = f"{self.directory}/{file.text()}"

        # Reads image file and sets image
        self.image = ndimage.rotate(tiff.imread(self.file_path), 90)
        self.main_window.image_widget.displayImage(self.image)

        self.live_current_file_txtbox.setText(file.text())

        # Enable options
        self.options_gbox.setEnabled(True)

    # --------------------------------------------------------------------------

    def setDataSource(self):
        dialog = DataSourceDialogWidget()
        if dialog:
            self.project = dialog.project_name
            self.spec = dialog.spec_name
            self.detector = dialog.detector_config_name
            self.instrument = dialog.instrument_config_name
            self.process_data = dialog.process_data

            if not self.project == "":
                if os.path.exists(os.path.join(self.project, "images")):
                    image_directory = os.path.join(self.project, "images")
                    self.scan_directory = os.path.join(image_directory, os.listdir(image_directory)[0])
                    scans = sorted(os.listdir(self.scan_directory))

                    self.post_data_source_list.clear()
                    self.post_data_source_list.addItems(scans)

                    self.main_window.image_widget.setLabel("left", "K")
                    self.main_window.image_widget.setLabel("bottom", "L")



    # --------------------------------------------------------------------------

    def loadDataSource(self, scan):

        self.dataset = []

        if not "" in [self.spec, self.detector, self.instrument]:
            scan = scan.text()[2:]
            vti_file = DataProcessing.createVTIFile(self.project, self.spec, self.detector,
                self.instrument, scan)

            self.axes, self.dataset = DataProcessing.loadData(vti_file)
            self.h_axis = [self.axes[0][0], self.axes[0][-1]]
            self.k_axis = [self.axes[1][0], self.axes[1][-1]]
            self.l_axis = [self.axes[2][0], self.axes[2][-1]]

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

            self.h_axis = [0, self.dataset.shape[0]]
            self.k_axis = [0, self.dataset.shape[1]]
            self.l_axis = [0, self.dataset.shape[2]]

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
        h_min, h_max = self.h_axis
        k_min, k_max = self.k_axis
        l_min, l_max = self.l_axis

        # h
        if self.post_h_direction_rbtn.isChecked():
            self.post_h_spinbox.setValue(int(self.post_h_slider.value()))
            rect = QtCore.QRectF(l_min, k_min, l_max - l_min, k_max - k_min)
            h_slice = int(self.post_h_slider.value())
            self.image = self.dataset[h_slice, :, :]

        # k
        elif self.post_k_direction_rbtn.isChecked():
            self.post_k_spinbox.setValue(int(self.post_k_slider.value()))
            rect = QtCore.QRectF(l_min, h_min, l_max - l_min, h_max - h_min)
            k_slice = int(self.post_k_slider.value())
            self.image = self.dataset[:, k_slice, :]

        # l
        else:
            self.post_l_spinbox.setValue(int(self.post_l_slider.value()))
            rect = QtCore.QRectF(k_min, h_min, k_max - k_min, h_max - h_min)
            l_slice = int(self.post_l_slider.value())
            self.image = self.dataset[:, :, l_slice]


        # Sets image
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

        color = self.crosshair_color_btn.color()

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

    def toggleBackgroundColor(self):

        """
        Toggles background color for image plot widget.

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
            self.main_window.image_widget.cmap_scale = "Log"
            self.main_window.image_widget.displayImage(self.image)
        else:
            self.main_window.image_widget.cmap_scale = "Linear"
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

    def simLivePlotting(self):

        """
        Simulates live update of image plot. Updates separated by refresh rate.
        """

        # Loops through images
        for i in range(self.live_file_list.count()):
            # Loads image to viewing window
            self.loadLiveImage(self.live_file_list.item(i))
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
        self.image_max_intensity_lbl = QtGui.QLabel("Max Intensity:")
        self.image_max_intensity_txtbox = QtGui.QLineEdit()
        self.image_max_intensity_txtbox.setReadOnly(True)
        self.image_cmap_pctl_lbl = QtGui.QLabel("CMap Pctl:")
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
        self.image_layout.addWidget(self.image_cmap_pctl_lbl, 3, 0)
        self.image_layout.addWidget(self.image_cmap_pctl_txtbox, 3, 1)

# ==============================================================================

class ImageWidget(pg.PlotWidget):

    """
    Contains viewing window for images.
    """

    def __init__ (self, parent):
        super(ImageWidget, self).__init__(parent)
        self.main_window = parent

        # x:y ratio set to 1
        #self.setAspectLocked(False)
        #self.setAspectLocked(True)
        # Background initially set to black
        self.setBackground("default")

        self.view = self.getViewBox()
        self.image_item = pg.ImageItem()
        self.addItem(self.image_item)

        # Sets current cmap/cmap scaling
        self.cmap_scale = "Linear"
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
        self.roi1 = ROIWidget([-1, -1], [2, 2], roi_1_layout, roi_1_plot)
        self.roi2 = ROIWidget([-0.75, -0.75], [1.5, 1.5], roi_2_layout, roi_2_plot)
        self.roi3 = ROIWidget([-0.5, -0.5], [1, 1], roi_3_layout, roi_3_plot)
        self.roi4 = ROIWidget([-0.25, -0.25], [0.5, 0.5], roi_4_layout, roi_4_plot)
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

        self.image = np.rot90(image, 3)

        # Checks colormap scale
        if self.cmap_scale == "Log":
            norm = colors.LogNorm(vmax=np.amax(self.image)*self.cmap_pctl)
        else:
            norm = colors.Normalize(vmax=np.amax(self.image)*self.cmap_pctl)

        # Normalizes image
        norm_image = norm(self.image)
        # Adds colormap to image
        color_image = plt.cm.jet(norm_image)
        # Sets image
        self.image_item.setImage(color_image)
        self.image_item.setRect(rect)

        # Update analysis textboxes
        self.main_window.analysis_widget.image_width_txtbox.setText(str(self.image.shape[0]))
        self.main_window.analysis_widget.image_height_txtbox.setText(str(self.image.shape[1]))
        self.main_window.analysis_widget.image_max_intensity_txtbox.setText(str(np.amax(self.image)))
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
        self.main_window.analysis_widget.mouse_x_txtbox.setText(str(int(x)))
        self.main_window.analysis_widget.mouse_y_txtbox.setText(str(int(y)))

        # Checks if mouse is within confines of image
        if self.image.shape[0] >= x >= 0 and self.image.shape[1] >= y >= 0:
            intensity = self.image[int(x), int(y)]
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

    def displayROIPlots(self):

        """
        Uses data to display avg intensities in all ROI plots. This function is
        only used for the initial display when a new dataset is loaded.
        """

        data = self.main_window.options_widget.image_data

        self.main_window.image_widget.roi1.plotAverageIntensity(data)
        self.main_window.image_widget.roi2.plotAverageIntensity(data)
        self.main_window.image_widget.roi3.plotAverageIntensity(data)
        self.main_window.image_widget.roi4.plotAverageIntensity(data)

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

        #self.roi_plot.setLabel("left", "Avg Intensity")

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
        self.x_spinbox = QtGui.QSpinBox()
        self.x_spinbox.setMinimum(0)
        self.x_spinbox.setMaximum(1000)
        self.y_lbl = QtGui.QLabel("y Pos:")
        self.y_spinbox = QtGui.QSpinBox()
        self.y_spinbox.setMinimum(0)
        self.y_spinbox.setMaximum(1000)
        self.width_lbl = QtGui.QLabel("Width:")
        self.width_spinbox = QtGui.QSpinBox()
        self.width_spinbox.setMinimum(0)
        self.width_spinbox.setMaximum(1000)
        self.height_lbl = QtGui.QLabel("Height:")
        self.height_spinbox = QtGui.QSpinBox()
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

            data_roi = self.data[:, x_min:x_max, y_min:y_max]
            avg_intensity = []

            for i in range(data_roi.shape[0]):
                avg = np.mean(data_roi[i])
                avg_intensity.append(avg)

            self.roi_plot.plot(avg_intensity, clear=True)

# ==============================================================================

class DataSourceDialogWidget(QtGui.QDialog):

    def __init__ (self):
        super().__init__()

        self.setWindowModality(QtCore.Qt.ApplicationModal)

        self.project_name = ""
        self.spec_name = ""
        self.detector_config_name = ""
        self.instrument_config_name = ""
        self.process_data = False
        self.ok = False

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
        self.dialog_btnbox.addButton("Cancel", QtGui.QDialogButtonBox.RejectRole)
        self.dialog_btnbox.addButton("OK", QtGui.QDialogButtonBox.AcceptRole)

        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)

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

        self.project_btn.clicked.connect(self.selectProject)
        self.spec_btn.clicked.connect(self.selectSpecFile)
        self.detector_btn.clicked.connect(self.selectDetectorConfigFile)
        self.instrument_btn.clicked.connect(self.selectInstrumentConfigFile)
        self.process_data_chkbox.stateChanged.connect(self.setDataProcessingStatus)
        self.dialog_btnbox.accepted.connect(self.accept)
        self.dialog_btnbox.rejected.connect(self.reject)

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
