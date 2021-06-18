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
    Contains controls to view and customize images and alter the viewing window.

    - Live mode: A directory of image file names is displayed and the user can
        view an image by clicking on its name. The user can also view all images
        in an automated loop by clicking on "Simulate Live Plotting". The refresh
        rate can be changed with the spinbox adjacent to the button.

    - Remote mode: A 3d array of image data is created from a directory of images.
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
        self.remote_image_gbox = QtGui.QGroupBox("Remote")
        self.image_mode_tabs.addTab(self.live_image_gbox, "Live")
        self.image_mode_tabs.addTab(self.remote_image_gbox, "Remote")
        self.options_gbox = QtGui.QGroupBox("Plotting Options")

        # Disable Options GroupBox until file selected
        self.options_gbox.setEnabled(False)

        # Add GroupBoxes to widget
        self.addWidget(self.image_mode_tabs, row=0, col=0)
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

        """
        - Creates subwidgets
        - Adds subwidgets to widget
        - Connects subwidgets to functions
        """

        # Create live mode widgets
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

        # Create remote mode widgets
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
        self.options_layout.addWidget(self.roi_color_btn, 0, 1)
        self.options_layout.addWidget(self.crosshair_mouse_chkbox, 1, 0)
        self.options_layout.addWidget(self.crosshair_color_btn, 1, 1)
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
        self.roi_color_btn.sigColorChanged.connect(self.changeROIColor)
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
        - Selects directory for both live and remote modes
        - Loads data for remote mode
        """

        # Find directory with image files
        self.directory = QtGui.QFileDialog.getExistingDirectory(self, "Open Folder")

        # (Alphabetically) Sorted list of files
        self.image_files = sorted(os.listdir(self.directory))

        # For remote mode plotting
        self.image_data = []

        # Live mode
        if self.live_image_gbox is self.image_mode_tabs.currentWidget():
            # Clear current directory and display new directory
            # Images can be view by clicking name
            self.live_file_list.clear()
            self.live_file_list.addItems(self.image_files)

        # Remote mode
        else:
            # Display directory name in textbox
            self.remote_current_directory_txtbox.setText(self.directory)
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
            self.remote_x_slider.setMaximum(self.image_data.shape[0] - 1)
            self.remote_x_spinbox.setRange(0, self.image_data.shape[0] - 1)
            self.remote_y_slider.setMaximum(self.image_data.shape[1] - 1)
            self.remote_y_spinbox.setRange(0, self.image_data.shape[1] - 1)
            self.remote_z_slider.setMaximum(self.image_data.shape[2] - 1)
            self.remote_z_spinbox.setRange(0, self.image_data.shape[2] - 1)

            # 3d array loaded into viewing window
            self.loadRemoteImage()

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

    def loadRemoteImage(self):

        """
        Loads image to viewing window.
        """

        # x
        if self.remote_x_direction_rbtn.isChecked():
            self.remote_x_spinbox.setValue(int(self.remote_x_slider.value()))
            x_slice = int(self.remote_x_slider.value())
            self.image = self.image_data[x_slice, :, :]
        # y
        elif self.remote_y_direction_rbtn.isChecked():
            self.remote_y_spinbox.setValue(int(self.remote_y_slider.value()))
            y_slice = int(self.remote_y_slider.value())
            self.image = self.image_data[:, y_slice, :]
        # z
        else:
            self.remote_z_spinbox.setValue(int(self.remote_z_slider.value()))
            z_slice = int(self.remote_z_slider.value())
            self.image = self.image_data[:, :, z_slice]

        # Sets image
        self.main_window.image_widget.displayImage(self.image)

        # Enable options
        self.options_gbox.setEnabled(True)

    # --------------------------------------------------------------------------

    def toggleSliceDirection(self):

        """
        Toggles direction of data slice for remote mode plotting.
        """

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

        # Loads new image into viewing window
        self.loadRemoteImage()

    # --------------------------------------------------------------------------

    def changeSliderValue(self, value):

        """
        Toggles data slice for remote mode plotting.
        """

        spinbox = self.sender()

        if spinbox == self.remote_x_spinbox:
            self.remote_x_slider.setValue(value)
        elif spinbox == self.remote_y_spinbox:
            self.remote_y_slider.setValue(value)
        else:
            self.remote_z_slider.setValue(value)

        # No need to call loadRemoteImage()
        # Connected with valueChanged signal that calls loadRemoteImage()

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

    def changeROIColor(self):

        """
        Changes color for ROI boxes.
        """

        color = self.roi_color_btn.color()

        self.main_window.image_widget.roi1.setPen(pg.mkPen(color, width=2))
        self.main_window.image_widget.roi2.setPen(pg.mkPen(color, width=2))
        self.main_window.image_widget.roi3.setPen(pg.mkPen(color, width=2))
        self.main_window.image_widget.roi4.setPen(pg.mkPen(color, width=2))

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
        self.setAspectLocked(True)
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
        self.roi1 = ROIWidget([200, 100], [40, 40], self.main_window.analysis_widget.roi1_layout)
        self.roi2 = ROIWidget([205, 105], [30, 30], self.main_window.analysis_widget.roi2_layout)
        self.roi3 = ROIWidget([210, 110], [20, 20], self.main_window.analysis_widget.roi3_layout)
        self.roi4 = ROIWidget([215, 115], [10, 10], self.main_window.analysis_widget.roi4_layout)
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

    def displayImage(self, image):

        """
        Adds image to plot window with correct options.
        """

        self.image = image

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

class ROIWidget(pg.ROI):

    """
    Contains ROI for viewing window and layout for its respective groupbox in the
    analysis widget.
    """

    def __init__ (self, position, size, layout):
        super().__init__(position, size=size)

        self.pen = pg.mkPen(width=2)
        self.setPen(self.pen)

        # For vertical, horizontal, and diagonal scaling
        self.addScaleHandle([0.5, 0], [0.5, 0.5])
        self.addScaleHandle([0, 0.5], [0.5, 0.5])
        self.addScaleHandle([0, 0], [0.5, 0.5])

        # Intially hide the ROI
        self.hide()

        self.layout = layout

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

        # Adds subwidgets to layout
        self.layout.addWidget(self.x_lbl, 0, 0)
        self.layout.addWidget(self.x_spinbox, 0, 1)
        self.layout.addWidget(self.y_lbl, 1, 0)
        self.layout.addWidget(self.y_spinbox, 1, 1)
        self.layout.addWidget(self.width_lbl, 2, 0)
        self.layout.addWidget(self.width_spinbox, 2, 1)
        self.layout.addWidget(self.height_lbl, 3, 0)
        self.layout.addWidget(self.height_spinbox, 3, 1)

        # Connects subwidgets to signals
        self.sigRegionChanged.connect(self.updateAnalysis)
        self.visibleChanged.connect(self.updateAnalysis)
        self.width_spinbox.valueChanged.connect(self.updateSize)
        self.height_spinbox.valueChanged.connect(self.updateSize)
        self.x_spinbox.valueChanged.connect(self.updatePosition)
        self.y_spinbox.valueChanged.connect(self.updatePosition)

        # Keeps track of whether textboxes or roi was updated last
        # Helps avoid infinite loop of updating
        # Acts like a semaphore of sorts
        self.updating = ""

    # --------------------------------------------------------------------------

    def updateAnalysis(self):

        """
        Updates spinboxes in analysis widget.
        """

        if self.updating != "roi":
            self.updating = "analysis"
            self.x_spinbox.setValue(self.pos()[0] + self.size()[0] / 2)
            self.y_spinbox.setValue(self.pos()[1] + self.size()[1] / 2)
            self.width_spinbox.setValue(self.size()[0])
            self.height_spinbox.setValue(self.size()[1])
            self.updating = ""

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
