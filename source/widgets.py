"""
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

# ==============================================================================

import pyqtgraph as pg
import pyqtgraph.opengl as gl
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
        self.crosshair_lbl = QtGui.QLabel("Crosshair:")
        self.crosshair_mouse_chkbox = QtGui.QCheckBox("Mouse")
        self.crosshair_roi_chkbox = QtGui.QCheckBox("ROI")
        self.mouse_mode_lbl = QtGui.QLabel("Mouse Mode:")
        self.mouse_mode_group = QtGui.QButtonGroup()
        self.pan_mode_rbtn = QtGui.QRadioButton("Pan")
        self.pan_mode_rbtn.setChecked(True)
        self.rect_mode_rbtn = QtGui.QRadioButton("Rectangle")
        self.mouse_mode_group.addButton(self.pan_mode_rbtn)
        self.mouse_mode_group.addButton(self.rect_mode_rbtn)
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

        self.remote_image_layout.addWidget(self.remote_browse_btn, 0, 0, 1, 4)
        self.remote_image_layout.addWidget(self.remote_current_directory_lbl, 1, 0)
        self.remote_image_layout.addWidget(self.remote_current_directory_txtbox, 1, 1, 1, 3)
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

        self.options_layout.addWidget(self.crosshair_lbl, 0, 0, 1, 1)
        self.options_layout.addWidget(self.crosshair_mouse_chkbox, 0, 1)
        self.options_layout.addWidget(self.crosshair_roi_chkbox, 0, 2)
        self.options_layout.addWidget(self.mouse_mode_lbl, 1, 0)
        self.options_layout.addWidget(self.pan_mode_rbtn, 1, 1)
        self.options_layout.addWidget(self.rect_mode_rbtn, 1, 2)
        self.options_layout.addWidget(self.cmap_scale_lbl, 2, 0, 1, 1)
        self.options_layout.addWidget(self.cmap_linear_rbtn, 2, 1)
        self.options_layout.addWidget(self.cmap_log_rbtn, 2, 2)
        self.options_layout.addWidget(self.cmap_linear_pctl_lbl, 3, 0)
        self.options_layout.addWidget(self.cmap_linear_slider, 3, 1, 1, 2)

        # Link widgets to actions
        self.live_browse_btn.clicked.connect(self.openDirectory)
        self.live_clear_btn.clicked.connect(self.clear)
        self.live_file_list.itemClicked.connect(self.loadLiveImage)
        self.live_plot_btn.clicked.connect(self.simLivePlotting)

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

        self.crosshair_mouse_chkbox.stateChanged.connect(self.toggleMouseCrosshair)
        self.crosshair_roi_chkbox.stateChanged.connect(self.toggleROICrosshair)
        self.pan_mode_rbtn.toggled.connect(self.toggleMouseMode)
        self.rect_mode_rbtn.toggled.connect(self.toggleMouseMode)
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

    def toggleMouseCrosshair(self, state):
        # Turn mouse crosshair on/off
        if state == 2:
            self.main_window.image_widget.v_line.setVisible(True)
            self.main_window.image_widget.h_line.setVisible(True)
        else:
            self.main_window.image_widget.v_line.setVisible(False)
            self.main_window.image_widget.h_line.setVisible(False)

    # --------------------------------------------------------------------------

    def toggleROICrosshair(self, state):
        # Turn roi (viewbox) crosshair on/off
        if state == 2:
            self.main_window.image_widget.roi_v_line.setVisible(True)
            self.main_window.image_widget.roi_h_line.setVisible(True)
        else:
            self.main_window.image_widget.roi_v_line.setVisible(False)
            self.main_window.image_widget.roi_h_line.setVisible(False)

    # --------------------------------------------------------------------------

    def toggleMouseMode(self):
        button = self.sender()
        # Toggles between pan and rectangle mouse controls
        if button.text() == "Pan":
            self.main_window.image_widget.view.setMouseMode(pg.ViewBox.PanMode)
        else:
            self.main_window.image_widget.view.setMouseMode(pg.ViewBox.RectMode)

    # --------------------------------------------------------------------------

    def toggleCmapScale(self):
        button = self.sender()
        # Toggles between log and linear scaling
        if button.text() == "Logarithmic":
            self.main_window.image_widget.cmap_scale = "Log"
            self.main_window.image_widget.displayImage(self.image)
            self.cmap_linear_slider.setEnabled(False)
        else:
            self.main_window.image_widget.cmap_scale = "Linear"
            self.main_window.image_widget.displayImage(self.image)
            self.cmap_linear_slider.setEnabled(True)

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
        self.roi_gbox = QtGui.QGroupBox("ROI")
        self.peak_gbox = QtGui.QGroupBox("Peak")

        # Add GroupBoxes to widget
        self.addWidget(self.mouse_gbox, row=0, col=0, rowspan=1)
        self.addWidget(self.image_gbox, row=1, col=0, rowspan=1)
        self.addWidget(self.roi_gbox, row=0, col=1, rowspan=2)
        self.addWidget(self.peak_gbox, row=0, col=2, rowspan=2)

        # Create/add layouts
        self.mouse_layout = QtGui.QGridLayout()
        self.image_layout = QtGui.QGridLayout()
        self.roi_layout = QtGui.QGridLayout()
        self.peak_layout = QtGui.QGridLayout()
        self.mouse_gbox.setLayout(self.mouse_layout)
        self.image_gbox.setLayout(self.image_layout)
        self.roi_gbox.setLayout(self.roi_layout)
        self.peak_gbox.setLayout(self.peak_layout)

    # --------------------------------------------------------------------------

    def setupComponents(self):
        # Create mouse widgets
        self.mouse_x_lbl = QtGui.QLabel("x Position:")
        self.mouse_x_txtbox = QtGui.QLineEdit()
        self.mouse_x_txtbox.setReadOnly(True)
        self.mouse_y_lbl = QtGui.QLabel("y Position:")
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
        self.image_cmap_pctl_lbl = QtGui.QLabel("Cmap Pctl:")
        self.image_cmap_pctl_txtbox = QtGui.QLineEdit()
        self.image_cmap_pctl_txtbox.setReadOnly(True)

        # Create roi widgets
        self.roi_center_x_lbl = QtGui.QLabel("Center x:")
        self.roi_center_x_txtbox = QtGui.QLineEdit()
        self.roi_center_x_txtbox.setReadOnly(True)
        self.roi_center_y_lbl = QtGui.QLabel("Center y:")
        self.roi_center_y_txtbox = QtGui.QLineEdit()
        self.roi_center_y_txtbox.setReadOnly(True)
        self.roi_width_lbl = QtGui.QLabel("Width:")
        self.roi_width_txtbox = QtGui.QLineEdit()
        self.roi_width_txtbox.setReadOnly(True)
        self.roi_height_lbl = QtGui.QLabel("Height:")
        self.roi_height_txtbox = QtGui.QLineEdit()
        self.roi_height_txtbox.setReadOnly(True)

        # Create peak widgets
        self.peak_center_x_lbl = QtGui.QLabel("Center x:")
        self.peak_center_x_txtbox = QtGui.QLineEdit()
        self.peak_center_x_txtbox.setReadOnly(True)
        self.peak_center_y_lbl = QtGui.QLabel("Center y:")
        self.peak_center_y_txtbox = QtGui.QLineEdit()
        self.peak_center_y_txtbox.setReadOnly(True)
        self.peak_width_lbl = QtGui.QLabel("Width:")
        self.peak_width_txtbox = QtGui.QLineEdit()
        self.peak_width_txtbox.setReadOnly(True)
        self.peak_height_lbl = QtGui.QLabel("Height:")
        self.peak_height_txtbox = QtGui.QLineEdit()
        self.peak_height_txtbox.setReadOnly(True)

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

        self.roi_layout.addWidget(self.roi_center_x_lbl, 0, 0)
        self.roi_layout.addWidget(self.roi_center_x_txtbox, 0, 1)
        self.roi_layout.addWidget(self.roi_center_y_lbl, 1, 0)
        self.roi_layout.addWidget(self.roi_center_y_txtbox, 1, 1)
        self.roi_layout.addWidget(self.roi_width_lbl, 2, 0)
        self.roi_layout.addWidget(self.roi_width_txtbox, 2, 1)
        self.roi_layout.addWidget(self.roi_height_lbl, 3, 0)
        self.roi_layout.addWidget(self.roi_height_txtbox, 3, 1)

        self.peak_layout.addWidget(self.peak_center_x_lbl, 0, 0)
        self.peak_layout.addWidget(self.peak_center_x_txtbox, 0, 1)
        self.peak_layout.addWidget(self.peak_center_y_lbl, 1, 0)
        self.peak_layout.addWidget(self.peak_center_y_txtbox, 1, 1)
        self.peak_layout.addWidget(self.peak_width_lbl, 2, 0)
        self.peak_layout.addWidget(self.peak_width_txtbox, 2, 1)
        self.peak_layout.addWidget(self.peak_height_lbl, 3, 0)
        self.peak_layout.addWidget(self.peak_height_txtbox, 3, 1)


# ==============================================================================

class ImageWidget(pg.PlotWidget):

    """
    - Image display
    - Avg intensity calculation
    """

    def __init__ (self, parent):
        super(ImageWidget, self).__init__(parent)
        self.main_window = parent

        self.hideAxis("left")
        self.hideAxis("bottom")
        self.setAspectLocked(True)

        self.view = self.getViewBox()
        self.image_item = pg.ImageItem()
        self.addItem(self.image_item)

        self.cmap_scale = "Linear"
        self.cmap_linear_norm_pctl = 1.0

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
            norm = colors.LogNorm()
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

        # Autofocuses on figure
        #self.view.enableAutoRange()

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
