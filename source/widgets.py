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

# ==============================================================================

class OptionsWidget(pg.LayoutWidget):

    """
    - File selector
    - List of image files
    - Plotting options
    """

    def __init__ (self, parent):
        super(OptionsWidget, self).__init__(parent)
        self.main_window = parent

        # Create GroupBoxes
        self.image_selection_tabs = QtGui.QTabWidget()
        self.live_image_gbox = QtGui.QGroupBox("Live")
        self.remote_image_gbox = QtGui.QGroupBox("Remote")
        self.image_selection_tabs.addTab(self.live_image_gbox, "Live")
        self.image_selection_tabs.addTab(self.remote_image_gbox, "Remote")
        self.options_gbox = QtGui.QGroupBox("Plotting Options")

        # Disable Options GroupBox until file selected
        self.options_gbox.setEnabled(False)

        # Add GroupBoxes to widget
        self.addWidget(self.image_selection_tabs, row=0, col=0)
        self.addWidget(self.options_gbox, row=1, col=0)

        # Create/add layouts
        self.live_image_layout = QtGui.QGridLayout()
        self.remote_image_layout = QtGui.QGridLayout()
        self.options_layout = QtGui.QGridLayout()
        self.live_image_gbox.setLayout(self.live_image_layout)
        self.remote_image_gbox.setLayout(self.remote_image_layout)
        self.options_gbox.setLayout(self.options_layout)

    # --------------------------------------------------------------------------

    def setupComponents(self):
        # Create live image widgets
        self.live_browse_btn = QtGui.QPushButton("Browse")
        self.live_clear_btn = QtGui.QPushButton("Clear")
        self.live_file_list = QtGui.QListWidget()
        self.live_current_file_lbl = QtGui.QLabel("Current Image:")
        self.live_current_file_txtbox = QtGui.QLineEdit()
        self.live_current_file_txtbox.setReadOnly(True)
        self.live_refresh_rate_lbl = QtGui.QLabel("Refresh Delay (s):")
        self.live_refresh_rate_spinbox = QtGui.QDoubleSpinBox()
        self.live_refresh_rate_spinbox.setSingleStep(0.01)
        self.live_refresh_rate_spinbox.setRange(0.0, 1.0)
        self.live_refresh_rate_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.live_refresh_rate_slider.setRange(0, 100)
        self.live_refresh_rate = 0.0

        # Create remote image widgets
        self.remote_browse_btn = QtGui.QPushButton("Browse")
        self.remote_current_directory_lbl = QtGui.QLabel("Current Directory:")
        self.remote_current_directory_txtbox = QtGui.QLineEdit()
        self.remote_current_directory_txtbox.setReadOnly(True)
        self.remote_direction_lbl = QtGui.QLabel("Slice Direction:")
        self.remote_direction_group = QtGui.QButtonGroup()
        self.remote_x_direction_rbtn = QtGui.QRadioButton("x")
        self.remote_x_direction_rbtn.setChecked(True)
        self.remote_y_direction_rbtn = QtGui.QRadioButton("y")
        self.remote_z_direction_rbtn = QtGui.QRadioButton("z")
        self.remote_direction_group.addButton(self.remote_x_direction_rbtn)
        self.remote_direction_group.addButton(self.remote_y_direction_rbtn)
        self.remote_direction_group.addButton(self.remote_z_direction_rbtn)
        self.remote_x_slider_lbl = QtGui.QLabel("x Slice:")
        self.remote_x_spinbox = QtGui.QSpinBox()
        self.remote_x_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.remote_x_slider.setTickPosition(QtGui.QSlider.TicksBothSides)
        self.remote_y_slider_lbl = QtGui.QLabel("y Slice:")
        self.remote_y_spinbox = QtGui.QSpinBox()
        self.remote_y_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.remote_y_slider.setTickPosition(QtGui.QSlider.TicksBothSides)
        self.remote_y_slider.setEnabled(False)
        self.remote_z_slider_lbl = QtGui.QLabel("z Slice:")
        self.remote_z_spinbox = QtGui.QSpinBox()
        self.remote_z_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.remote_z_slider.setTickPosition(QtGui.QSlider.TicksBothSides)
        self.remote_z_slider.setEnabled(False)

        # Create options widgets
        self.live_plot_btn = QtGui.QPushButton("Simulate Live Plotting")
        self.reset_btn = QtGui.QPushButton("Reset View")
        self.roi_boxes_chkbox = QtGui.QCheckBox("ROI")
        self.crosshair_lbl = QtGui.QLabel("Crosshair:")
        self.crosshair_mouse_chkbox = QtGui.QCheckBox("Mouse")
        self.mouse_mode_lbl = QtGui.QLabel("Mouse Mode:")
        self.mouse_mode_group = QtGui.QButtonGroup()
        self.pan_mode_rbtn = QtGui.QRadioButton("Pan")
        self.pan_mode_rbtn.setChecked(True)
        self.rect_mode_rbtn = QtGui.QRadioButton("Rectangle")
        self.mouse_mode_group.addButton(self.pan_mode_rbtn)
        self.mouse_mode_group.addButton(self.rect_mode_rbtn)
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
        self.cmap_linear_pctl_lbl = QtGui.QLabel("CMap Pctl:")
        self.cmap_linear_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.cmap_linear_slider.setMinimum(1)
        self.cmap_linear_slider.setMaximum(100)
        self.cmap_linear_slider.setSingleStep(10)
        self.cmap_linear_slider.setTickInterval(10)
        self.cmap_linear_slider.setTickPosition(QtGui.QSlider.TicksBothSides)
        self.cmap_linear_slider.setValue(100)

        # Add widgets to GroupBoxes
        self.live_image_layout.addWidget(self.live_browse_btn, 0, 0, 1, 2)
        self.live_image_layout.addWidget(self.live_clear_btn, 0, 2, 1, 2)
        self.live_image_layout.addWidget(self.live_file_list, 1, 0, 3, 4)
        self.live_image_layout.addWidget(self.live_current_file_lbl, 4, 0)
        self.live_image_layout.addWidget(self.live_current_file_txtbox, 4, 1, 1, 3)
        self.live_image_layout.addWidget(self.live_plot_btn, 5, 0, 1, 2)
        self.live_image_layout.addWidget(self.live_refresh_rate_lbl, 5, 2)
        self.live_image_layout.addWidget(self.live_refresh_rate_spinbox, 5, 3)

        self.remote_image_layout.addWidget(self.remote_browse_btn, 0, 0, 1, 4)
        self.remote_image_layout.addWidget(self.remote_current_directory_lbl, 1, 0)
        self.remote_image_layout.addWidget(self.remote_current_directory_txtbox, 1, 1, 1, 4)
        self.remote_image_layout.addWidget(self.remote_direction_lbl, 2, 0)
        self.remote_image_layout.addWidget(self.remote_x_direction_rbtn, 2, 1)
        self.remote_image_layout.addWidget(self.remote_y_direction_rbtn, 2, 2)
        self.remote_image_layout.addWidget(self.remote_z_direction_rbtn, 2, 3)
        self.remote_image_layout.addWidget(self.remote_x_slider_lbl, 3, 0)
        self.remote_image_layout.addWidget(self.remote_x_spinbox, 3, 1)
        self.remote_image_layout.addWidget(self.remote_x_slider, 3, 2, 1, 3)
        self.remote_image_layout.addWidget(self.remote_y_slider_lbl, 4, 0)
        self.remote_image_layout.addWidget(self.remote_y_spinbox, 4, 1)
        self.remote_image_layout.addWidget(self.remote_y_slider, 4, 2, 1, 3)
        self.remote_image_layout.addWidget(self.remote_z_slider_lbl, 5, 0)
        self.remote_image_layout.addWidget(self.remote_z_spinbox, 5, 1)
        self.remote_image_layout.addWidget(self.remote_z_slider, 5, 2, 1, 3)

        self.options_layout.addWidget(self.roi_boxes_chkbox, 0, 0)
        self.options_layout.addWidget(self.crosshair_lbl, 1, 0, 1, 1)
        self.options_layout.addWidget(self.crosshair_mouse_chkbox, 1, 1)
        self.options_layout.addWidget(self.mouse_mode_lbl, 2, 0)
        self.options_layout.addWidget(self.pan_mode_rbtn, 2, 1)
        self.options_layout.addWidget(self.rect_mode_rbtn, 2, 2)
        self.options_layout.addWidget(self.background_color_lbl, 3, 0)
        self.options_layout.addWidget(self.background_black_rbtn, 3, 1)
        self.options_layout.addWidget(self.background_white_rbtn, 3, 2)
        self.options_layout.addWidget(self.cmap_scale_lbl, 4, 0)
        self.options_layout.addWidget(self.cmap_linear_rbtn, 4, 1)
        self.options_layout.addWidget(self.cmap_log_rbtn, 4, 2)
        self.options_layout.addWidget(self.cmap_linear_pctl_lbl, 5, 0)
        self.options_layout.addWidget(self.cmap_linear_slider, 5, 1, 1, 2)

        # Link widgets to actions
        self.live_browse_btn.clicked.connect(self.openDirectory)
        self.live_clear_btn.clicked.connect(self.clear)
        self.live_file_list.itemClicked.connect(self.loadLiveImage)
        self.live_plot_btn.clicked.connect(self.simLivePlotting)
        self.live_refresh_rate_spinbox.valueChanged.connect(self.changeRefreshRate)

        self.remote_browse_btn.clicked.connect(self.openDirectory)
        self.remote_x_direction_rbtn.toggled.connect(self.toggleSliceDirection)
        self.remote_y_direction_rbtn.toggled.connect(self.toggleSliceDirection)
        self.remote_z_direction_rbtn.toggled.connect(self.toggleSliceDirection)
        self.remote_x_spinbox.valueChanged[int].connect(self.changeSliderValue)
        self.remote_y_spinbox.valueChanged[int].connect(self.changeSliderValue)
        self.remote_z_spinbox.valueChanged[int].connect(self.changeSliderValue)
        self.remote_x_slider.valueChanged.connect(self.loadRemoteImage)
        self.remote_y_slider.valueChanged.connect(self.loadRemoteImage)
        self.remote_z_slider.valueChanged.connect(self.loadRemoteImage)

        self.roi_boxes_chkbox.stateChanged.connect(self.toggleROIBoxes)
        self.crosshair_mouse_chkbox.stateChanged.connect(self.toggleMouseCrosshair)
        self.pan_mode_rbtn.toggled.connect(self.toggleMouseMode)
        self.rect_mode_rbtn.toggled.connect(self.toggleMouseMode)
        self.background_black_rbtn.toggled.connect(self.toggleBackgroundColor)
        self.background_white_rbtn.toggled.connect(self.toggleBackgroundColor)
        self.cmap_linear_rbtn.toggled.connect(self.toggleCmapScale)
        self.cmap_log_rbtn.toggled.connect(self.toggleCmapScale)
        self.cmap_linear_slider.valueChanged.connect(self.changeCmapLinearPctl)

    # --------------------------------------------------------------------------

    def openDirectory(self):
        # Find directory with image files
        self.directory = QtGui.QFileDialog.getExistingDirectory(self, "Open Folder")

        # Sorted list of files
        self.image_files = sorted(os.listdir(self.directory))

        # For remote plotting
        self.image_data = []

        # Live plotting
        if self.live_image_gbox is self.image_selection_tabs.currentWidget():
            # Display files
            self.live_file_list.clear()
            self.live_file_list.addItems(self.image_files)
        # Remote plotting
        else:
            self.remote_current_directory_txtbox.setText(self.directory)
            for i in range(len(self.image_files)):
                if self.image_files[i] != "alignment.tif":
                    file_path = f"{self.directory}/{self.image_files[i]}"
                    image = ndimage.rotate(tiff.imread(file_path), 90)
                    self.image_data.append(image)
            self.image_data = np.stack(self.image_data)
            self.remote_x_slider.setMaximum(self.image_data.shape[0] - 1)
            self.remote_x_spinbox.setRange(0, self.image_data.shape[0] - 1)
            self.remote_y_slider.setMaximum(self.image_data.shape[1] - 1)
            self.remote_y_spinbox.setRange(0, self.image_data.shape[1] - 1)
            self.remote_z_slider.setMaximum(self.image_data.shape[2] - 1)
            self.remote_z_spinbox.setRange(0, self.image_data.shape[2] - 1)
            self.loadRemoteImage()

    # --------------------------------------------------------------------------

    def clear(self):
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
        #Concatenate directory and file names
        self.file_path = f"{self.directory}/{file.text()}"

        # Read and set image file
        self.image = ndimage.rotate(tiff.imread(self.file_path), 90)
        self.main_window.image_widget.displayImage(self.image)

        self.live_current_file_txtbox.setText(file.text())

        # Enable options
        self.options_gbox.setEnabled(True)

    # --------------------------------------------------------------------------

    def loadRemoteImage(self):
        # Read and set image file
        if self.remote_x_direction_rbtn.isChecked():
            self.remote_x_spinbox.setValue(int(self.remote_x_slider.value()))
            x_slice = int(self.remote_x_slider.value())
            self.image = self.image_data[x_slice, :, :]

        elif self.remote_y_direction_rbtn.isChecked():
            self.remote_y_spinbox.setValue(int(self.remote_y_slider.value()))
            y_slice = int(self.remote_y_slider.value())
            self.image = self.image_data[:, y_slice, :]
            #self.image = ndimage.rotate(self.image, 90)
        else:
            self.remote_z_spinbox.setValue(int(self.remote_z_slider.value()))
            z_slice = int(self.remote_z_slider.value())
            self.image = self.image_data[:, :, z_slice]
            #self.image = ndimage.rotate(self.image, 90)

        self.main_window.image_widget.displayImage(self.image)

        # Enable options
        self.options_gbox.setEnabled(True)

    # --------------------------------------------------------------------------

    def toggleSliceDirection(self):
        button = self.sender()

        if button.text() == "x":
            self.remote_x_slider.setEnabled(True)
            self.remote_y_slider.setEnabled(False)
            self.remote_z_slider.setEnabled(False)
        elif button.text() == "y":
            self.remote_x_slider.setEnabled(False)
            self.remote_y_slider.setEnabled(True)
            self.remote_z_slider.setEnabled(False)
        else:
            self.remote_x_slider.setEnabled(False)
            self.remote_y_slider.setEnabled(False)
            self.remote_z_slider.setEnabled(True)

        self.loadRemoteImage()

    # --------------------------------------------------------------------------

    def changeSliderValue(self, value):
        spinbox = self.sender()

        if spinbox == self.remote_x_spinbox:
            self.remote_x_slider.setValue(value)
        elif spinbox == self.remote_y_spinbox:
            self.remote_y_slider.setValue(value)
        else:
            self.remote_z_slider.setValue(value)

    # --------------------------------------------------------------------------

    def toggleROIBoxes(self, state):
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
        # Turn mouse crosshair on/off
        if state == 2:
            self.main_window.image_widget.v_line.setVisible(True)
            self.main_window.image_widget.h_line.setVisible(True)
        else:
            self.main_window.image_widget.v_line.setVisible(False)
            self.main_window.image_widget.h_line.setVisible(False)

    # --------------------------------------------------------------------------

    def toggleMouseMode(self):
        button = self.sender()
        # Toggles between pan and rectangle mouse controls
        if button.text() == "Pan":
            self.main_window.image_widget.view.setMouseMode(pg.ViewBox.PanMode)
        else:
            self.main_window.image_widget.view.setMouseMode(pg.ViewBox.RectMode)

    # --------------------------------------------------------------------------

    def toggleBackgroundColor(self):
        button = self.sender()
        # Toggles between background colors for plot widget
        if button.text() == "Black":
            self.main_window.image_widget.setBackground("default")
        else:
            self.main_window.image_widget.setBackground("w")

    # --------------------------------------------------------------------------

    def toggleCmapScale(self):
        button = self.sender()
        # Toggles between log and linear scaling
        if button.text() == "Logarithmic":
            self.main_window.image_widget.cmap_scale = "Log"
            self.main_window.image_widget.displayImage(self.image)
        else:
            self.main_window.image_widget.cmap_scale = "Linear"
            self.main_window.image_widget.displayImage(self.image)

    # --------------------------------------------------------------------------

    def changeCmapLinearPctl(self):
        slider = self.sender()

        self.main_window.image_widget.cmap_linear_norm_pctl = slider.value() / 100.0
        self.main_window.image_widget.displayImage(self.image)

    # --------------------------------------------------------------------------

    def simLivePlotting(self):
        # Loops through files in list
        for i in range(self.live_file_list.count()):
            self.loadLiveImage(self.live_file_list.item(i))
            QtGui.QApplication.processEvents()
            time.sleep(self.live_refresh_rate)

    # --------------------------------------------------------------------------

    def changeRefreshRate(self, value):
        self.live_refresh_rate = value

# ==============================================================================

class AnalysisWidget(pg.LayoutWidget):

    """
    - ROI values
    - peak values
    - Mouse (Crosshair) values
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
        self.roi1_layout = QtGui.QGridLayout()
        self.roi2_layout = QtGui.QGridLayout()
        self.roi3_layout = QtGui.QGridLayout()
        self.roi4_layout = QtGui.QGridLayout()
        self.mouse_gbox.setLayout(self.mouse_layout)
        self.image_gbox.setLayout(self.image_layout)
        self.roi1_gbox.setLayout(self.roi1_layout)
        self.roi2_gbox.setLayout(self.roi2_layout)
        self.roi3_gbox.setLayout(self.roi3_layout)
        self.roi4_gbox.setLayout(self.roi4_layout)

    # --------------------------------------------------------------------------

    def setupComponents(self):
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
    - Image display
    - Avg intensity calculation
    """

    def __init__ (self, parent):
        super(ImageWidget, self).__init__(parent)
        self.main_window = parent

        #self.hideAxis("left")
        #self.hideAxis("bottom")
        self.setAspectLocked(True)
        self.setBackground("default")

        self.view = self.getViewBox()
        self.image_item = pg.ImageItem()
        self.addItem(self.image_item)

        # Set current cmap/cmap scaling
        self.cmap_scale = "Linear"
        self.cmap_linear_norm_pctl = 1.0

        self.roi1 = ROIWidget([200, 100], [40, 40], self.main_window.analysis_widget.roi1_layout)
        self.roi2 = ROIWidget([205, 105], [30, 30], self.main_window.analysis_widget.roi2_layout)
        self.roi3 = ROIWidget([210, 110], [20, 20], self.main_window.analysis_widget.roi3_layout)
        self.roi4 = ROIWidget([215, 115], [10, 10], self.main_window.analysis_widget.roi4_layout)

        self.addItem(self.roi1)
        self.addItem(self.roi2)
        self.addItem(self.roi3)
        self.addItem(self.roi4)

        # Create mouse crosshair
        self.v_line = pg.InfiniteLine(angle=90, movable=False)
        self.h_line = pg.InfiniteLine(angle=0, movable=False)
        self.v_line.setVisible(False)
        self.h_line.setVisible(False)
        self.addItem(self.v_line, ignoreBounds=True)
        self.addItem(self.h_line, ignoreBounds=True)

        # Create roi crosshair
        self.roi_v_line = pg.InfiniteLine(angle=90, movable=False)
        self.roi_h_line = pg.InfiniteLine(angle=0, movable=False)
        self.roi_v_line.setVisible(False)
        self.roi_h_line.setVisible(False)
        self.roi_v_line.setZValue(1000)
        self.roi_h_line.setZValue(1000)
        self.addItem(self.roi_v_line, ignoreBounds=True)
        self.addItem(self.roi_h_line, ignoreBounds=True)

    # --------------------------------------------------------------------------

    def displayImage(self, image):

        self.image = image

        if self.cmap_scale == "Log":
            norm = colors.LogNorm(vmax=np.amax(self.image)*self.cmap_linear_norm_pctl)
        else:
            norm = colors.Normalize(vmax=np.amax(self.image)*self.cmap_linear_norm_pctl)

        # vmax=np.amax(self.image)
        norm_image = norm(self.image)
        color_image = plt.cm.jet(norm_image)
        self.image_item.setImage(color_image)

        # Update analysis textboxes
        self.main_window.analysis_widget.image_width_txtbox.setText(str(self.image.shape[0]))
        self.main_window.analysis_widget.image_height_txtbox.setText(str(self.image.shape[1]))
        self.main_window.analysis_widget.image_max_intensity_txtbox.setText(str(np.amax(self.image)))
        self.main_window.analysis_widget.image_cmap_pctl_txtbox.setText(str(self.cmap_linear_norm_pctl))

        # Update crosshair information
        self.view.scene().sigMouseMoved.connect(self.updateMouseCrosshair)

    # --------------------------------------------------------------------------

    def updateMouseCrosshair(self, scene_point):
        # View coordinates to plot coordinates
        view_point = self.view.mapSceneToView(scene_point)

        x, y = view_point.x(), view_point.y()

        # Changes position of crosshair
        self.v_line.setPos(x)
        self.h_line.setPos(y)

        # Update analysis textboxes
        self.main_window.analysis_widget.mouse_x_txtbox.setText(str(int(x)))
        self.main_window.analysis_widget.mouse_y_txtbox.setText(str(int(y)))

        if self.image.shape[0] >= x >= 0 and self.image.shape[1] >= y >= 0:
            intensity = self.image[int(x), int(y)]
            self.main_window.analysis_widget.mouse_intensity_txtbox.setText(str(intensity))

# ==============================================================================

class ROIWidget(pg.ROI):

    def __init__ (self, position, size, layout):
        super().__init__(position, size=size)

        self.pen = pg.mkPen("m", width=2)
        self.setPen(self.pen)

        self.addScaleHandle([0.5, 0], [0.5, 0.5])
        self.addScaleHandle([0, 0.5], [0.5, 0.5])
        self.addScaleHandle([0, 0], [0.5, 0.5])
        self.hide()

        self.layout = layout

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

        self.layout.addWidget(self.x_lbl, 0, 0)
        self.layout.addWidget(self.x_spinbox, 0, 1)
        self.layout.addWidget(self.y_lbl, 1, 0)
        self.layout.addWidget(self.y_spinbox, 1, 1)
        self.layout.addWidget(self.width_lbl, 2, 0)
        self.layout.addWidget(self.width_spinbox, 2, 1)
        self.layout.addWidget(self.height_lbl, 3, 0)
        self.layout.addWidget(self.height_spinbox, 3, 1)

        self.sigRegionChanged.connect(self.updateAnalysis)
        self.visibleChanged.connect(self.updateAnalysis)
        self.width_spinbox.valueChanged.connect(self.updateSize)
        self.height_spinbox.valueChanged.connect(self.updateSize)
        self.x_spinbox.valueChanged.connect(self.updatePosition)
        self.y_spinbox.valueChanged.connect(self.updatePosition)

        # Keeps track of whether textboxes or roi was updated last
        # Helps avoid infinite loop of updating
        self.updating = ""

    # --------------------------------------------------------------------------

    def updateAnalysis(self):
        if self.updating != "roi":
            self.updating = "analysis"
            self.x_spinbox.setValue(self.pos()[0] + self.size()[0] / 2)
            self.y_spinbox.setValue(self.pos()[1] + self.size()[1] / 2)
            self.width_spinbox.setValue(self.size()[0])
            self.height_spinbox.setValue(self.size()[1])
            self.updating = ""

    # --------------------------------------------------------------------------

    def updateSize(self):
        if self.updating != "analysis":
            self.updating = "roi"
            width = self.width_spinbox.value()
            height = self.height_spinbox.value()
            self.setSize((width, height))
            self.updatePosition()
            self.updating = ""

    # --------------------------------------------------------------------------

    def updatePosition(self):
        if self.updating != "analysis":
            self.updating = "roi"
            # Bottom lefthand corner of roi
            x_origin = self.x_spinbox.value() - self.size()[0] / 2
            y_origin = self.y_spinbox.value() - self.size()[1] / 2
            self.setPos((x_origin, y_origin))
            self.updating = ""
