"""
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

# ==============================================================================

import pyqtgraph as pg
import pyqtgraph.opengl as gl
import matplotlib.pyplot as plt
from pyqtgraph.Qt import QtGui
import numpy as np
import os
from scipy import ndimage
import tifffile as tiff

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
        self.options_gbox = QtGui.QGroupBox("Plotting Options")
        self.files_gbox = QtGui.QGroupBox("Image Files")

        # Disable Options GroupBox until file selected
        self.options_gbox.setEnabled(False)

        # Add GroupBoxes to widget
        self.addWidget(self.files_gbox, row=0, col=0)
        self.addWidget(self.options_gbox, row=1, col=0)

        # Create/add layouts
        self.files_layout = QtGui.QGridLayout()
        self.options_layout = QtGui.QGridLayout()
        self.options_gbox.setLayout(self.options_layout)
        self.files_gbox.setLayout(self.files_layout)

    # --------------------------------------------------------------------------

    def setupComponents(self):
        # Create file widgets
        self.browse_btn = QtGui.QPushButton("Browse")
        self.clear_btn = QtGui.QPushButton("Clear")
        self.file_list = QtGui.QListWidget()
        self.current_file_lbl = QtGui.QLabel("Current Image:")
        self.current_file_txtbox = QtGui.QLineEdit()
        self.current_file_txtbox.setReadOnly(True)

        # Create options widgets
        self.live_plot_btn = QtGui.QPushButton("Simulate Live Plotting")
        self.reset_btn = QtGui.QPushButton("Reset View")

        self.crosshair_lbl = QtGui.QLabel("Crosshair:")
        self.crosshair_mouse_chkbox = QtGui.QCheckBox("Mouse")
        self.crosshair_roi_chkbox = QtGui.QCheckBox("ROI")

        self.scale_lbl = QtGui.QLabel("Scale:")
        self.scale_group = QtGui.QButtonGroup()
        self.linear_scale_rbtn = QtGui.QRadioButton("Linear")
        self.linear_scale_rbtn.setChecked(True)
        self.log_scale_rbtn = QtGui.QRadioButton("Logarithmic")
        self.scale_group.addButton(self.linear_scale_rbtn)
        self.scale_group.addButton(self.log_scale_rbtn)

        self.mouse_mode_lbl = QtGui.QLabel("Mouse Mode:")
        self.mouse_mode_group = QtGui.QButtonGroup()
        self.pan_mode_rbtn = QtGui.QRadioButton("Pan")
        self.pan_mode_rbtn.setChecked(True)
        self.rect_mode_rbtn = QtGui.QRadioButton("Rectangle")
        self.mouse_mode_group.addButton(self.pan_mode_rbtn)
        self.mouse_mode_group.addButton(self.rect_mode_rbtn)

        # Add widgets to GroupBoxes
        self.files_layout.addWidget(self.browse_btn, 0, 0, 1, 2)
        self.files_layout.addWidget(self.clear_btn, 0, 2, 1, 2)
        self.files_layout.addWidget(self.file_list, 1, 0, 4, 4)
        self.files_layout.addWidget(self.current_file_lbl, 5, 0)
        self.files_layout.addWidget(self.current_file_txtbox, 5, 1, 1, 3)

        self.options_layout.addWidget(self.live_plot_btn, 0, 0, 1, 2)
        self.options_layout.addWidget(self.reset_btn, 0, 2, 1, 3)

        self.options_layout.addWidget(self.crosshair_lbl, 1, 0, 1, 1)
        self.options_layout.addWidget(self.crosshair_mouse_chkbox, 1, 1)
        self.options_layout.addWidget(self.crosshair_roi_chkbox, 1, 2)

        self.options_layout.addWidget(self.scale_lbl, 2, 0, 1, 1)
        self.options_layout.addWidget(self.linear_scale_rbtn, 2, 1)
        self.options_layout.addWidget(self.log_scale_rbtn, 2, 2)

        self.options_layout.addWidget(self.mouse_mode_lbl, 3, 0)
        self.options_layout.addWidget(self.pan_mode_rbtn, 3, 1)
        self.options_layout.addWidget(self.rect_mode_rbtn, 3, 2)

        # Link widgets to actions
        self.browse_btn.clicked.connect(self.openDirectory)
        self.clear_btn.clicked.connect(self.clear)
        self.file_list.itemClicked.connect(self.loadFile)
        self.reset_btn.clicked.connect(self.resetView)
        self.crosshair_mouse_chkbox.stateChanged.connect(self.toggleMouseCrosshair)
        self.crosshair_roi_chkbox.stateChanged.connect(self.toggleROICrosshair)
        self.live_plot_btn.clicked.connect(self.simLivePlotting)
        self.linear_scale_rbtn.toggled.connect(self.toggleScale)
        self.log_scale_rbtn.toggled.connect(self.toggleScale)
        self.pan_mode_rbtn.toggled.connect(self.toggleMouseMode)
        self.rect_mode_rbtn.toggled.connect(self.toggleMouseMode)

    # --------------------------------------------------------------------------

    def openDirectory(self):
        # Find directory with image files
        self.directory = QtGui.QFileDialog.getExistingDirectory(self, "Open Folder")

        # Sorted list of files
        files = sorted(os.listdir(self.directory))

        # Display files
        self.file_list.clear()
        self.file_list.addItems(files)

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

    def loadFile(self, file):
        #Concatenate directory and file names
        self.file_path = f"{self.directory}/{file.text()}"

        self.main_window.image_widget.displayImage(self.file_path)
        self.current_file_txtbox.setText(file.text())

        # Enable options
        self.options_gbox.setEnabled(True)

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

    def resetView(self):
        self.main_window.image_widget.displayImage(self.file_path)

    # --------------------------------------------------------------------------

    def toggleScale(self):
        button = self.sender()
        # Toggles between log and linear scaling
        if button.text() == "Logarithmic":
            self.main_window.x_plot_widget.setLogMode(False, True)
            self.main_window.y_plot_widget.setLogMode(True, False)
        else:
            self.main_window.x_plot_widget.setLogMode(False, False)
            self.main_window.y_plot_widget.setLogMode(False, False)

    # --------------------------------------------------------------------------

    def toggleMouseMode(self):
        button = self.sender()
        # Toggles between pan and rectangle mouse controls
        if button.text() == "Pan":
            self.main_window.image_widget.view.setMouseMode(pg.ViewBox.PanMode)
        else:
            self.main_window.image_widget.view.setMouseMode(pg.ViewBox.RectMode)

    # --------------------------------------------------------------------------

    def simLivePlotting(self):
        # Loops through files in list
        for i in range(self.file_list.count()):
            self.loadFile(self.file_list.item(i))
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

        # Create image widgets
        self.image_width_lbl = QtGui.QLabel("Width:")
        self.image_width_txtbox = QtGui.QLineEdit()
        self.image_width_txtbox.setReadOnly(True)
        self.image_height_lbl = QtGui.QLabel("Height:")
        self.image_height_txtbox = QtGui.QLineEdit()
        self.image_height_txtbox.setReadOnly(True)

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

        self.image_layout.addWidget(self.image_width_lbl, 0, 0)
        self.image_layout.addWidget(self.image_width_txtbox, 0, 1)
        self.image_layout.addWidget(self.image_height_lbl, 1, 0)
        self.image_layout.addWidget(self.image_height_txtbox, 1, 1)

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

    def displayImage(self, file_path):
        # Read and set image file
        self.image = ndimage.rotate(tiff.imread(file_path), 90)
        color_image = (plt.cm.jet(self.image) * 2**32).astype(int)
        self.image_item.setImage(color_image)

        self.main_window.analysis_widget.image_width_txtbox.setText(str(self.image.shape[0]))
        self.main_window.analysis_widget.image_height_txtbox.setText(str(self.image.shape[1]))
        # For 3D plotting
        #self.mean_image = self.image[:,:,:-1].mean(axis=2)

        # Limit viewing window to only show image
        self.view.setLimits(
            xMin=0,
            xMax=(self.image.shape[0]),
            yMin=0,
            yMax=(self.image.shape[1])
        )
        # Autofocuses on figure
        #self.view.enableAutoRange()

        # Link view to profile plots
        self.view.setXLink(self.main_window.x_plot_widget)
        self.view.setYLink(self.main_window.y_plot_widget)
        #self.main_window.y_plot_widget.invertY(True)

        # Dynamically update plots when viewing window changes
        self.view.sigRangeChanged.connect(self.updatePlots)

        # Update crosshair information
        self.view.scene().sigMouseMoved.connect(self.updateMouseCrosshair)

        # Initial update of x & y intensity plots
        self.updatePlots()

    # --------------------------------------------------------------------------

    def updatePlots(self):
        # calculateAvgIntensity() will return nothing if viewing range is wrong
        try:
            # Average intensity of pixels in viewing window
            col_avgs, row_avgs = self.calculateAvgIntensity()

            # Clear plots
            self.main_window.x_plot_widget.clear()
            self.main_window.y_plot_widget.clear()
            #self.main_window.xyz_plot_widget.clear()

            # Display new plots
            self.main_window.x_plot_widget.plot(col_avgs)
            self.main_window.y_plot_widget.plot(x=row_avgs, y=range(len(row_avgs)))
            #self.main_window.xyz_plot_widget.plot(self.mean_image)

        except TypeError:
            return

    # --------------------------------------------------------------------------

    def calculateAvgIntensity(self):
        self.view_range = self.view.viewRange()

        # Max/min values of viewing window
        x_min, x_max = int(self.view_range[0][0]), int(self.view_range[0][1])
        y_min, y_max = int(self.view_range[1][0]), int(self.view_range[1][1])
        x_center = x_min + ((x_max - x_min) / 2)
        y_center = y_min + ((y_max - y_min) / 2)

        # Subarray of pixels within viewing window
        image_in_view = self.image[x_min:x_max, y_min:y_max]

        # Error that occurs during first plot
        # Not really sure why image_in_view would contain 0, but it does
        if 0 in image_in_view.shape:
            return

        # Update analysis textboxes
        self.main_window.analysis_widget.roi_center_x_txtbox.setText(str(x_center))
        self.main_window.analysis_widget.roi_center_y_txtbox.setText(str(y_center))
        self.main_window.analysis_widget.roi_width_txtbox.setText(str(image_in_view.shape[0]))
        self.main_window.analysis_widget.roi_height_txtbox.setText(str(image_in_view.shape[1]))

        # Mean of values in x & y directions
        # Each yield a 1-D array
        cols = image_in_view.mean(axis=1)
        rows = image_in_view.mean(axis=0)

        # 1-D arrays of zeros to embed mean arrays into
        x_curve = np.zeros((self.image.shape[0]))
        y_curve = np.zeros((self.image.shape[1]))

        # Embed mean arrays
        x_curve[x_min:x_min + image_in_view.shape[0]] = cols
        y_curve[y_min:y_min + image_in_view.shape[1]] = rows

        # 1-D arrays with lengths corresponding to original image
        return x_curve, y_curve

    # --------------------------------------------------------------------------

    def updateMouseCrosshair(self, scene_point):
        # View coordinates to plot coordinates
        view_point = self.view.mapSceneToView(scene_point)

        # Changes position of crosshair
        self.v_line.setPos(view_point.x())
        self.h_line.setPos(view_point.y())

        # Update analysis textboxes
        self.main_window.analysis_widget.mouse_x_txtbox.setText(str(int(view_point.x())))
        self.main_window.analysis_widget.mouse_y_txtbox.setText(str(int(view_point.y())))


# ==============================================================================

class XPlotWidget(pg.PlotWidget):

    """
    - Plots x-values vs average intensity
    - Axes linked to ImageWidget and YPlotWidget
    """

    def __init__ (self, parent):
        super(XPlotWidget, self).__init__(parent)
        self.main_window = parent

        self.setLabel("left", "Average Intensity")
        self.setLabel("bottom", "x")
        self.showGrid(x=True, y=True)
        self.setMouseEnabled(x=False, y=False)


# ==============================================================================

class YPlotWidget(pg.PlotWidget):

    """
    - Plots y-values vs average intensity
    - Axes linked to ImageWidget and XPlotWidget
    """

    def __init__ (self, parent):
        super(YPlotWidget, self).__init__(parent)
        self.main_window = parent

        self.setLabel("left", "y")
        self.setLabel("bottom", "Average Intensity")
        self.showGrid(x=True, y=True)
        self.setMouseEnabled(x=False, y=False)


# ==============================================================================

"""
Placeholder class for undecided dock in top-right corner of window
"""

class XYZPlotWidget(gl.GLViewWidget):

    def __init__ (self, parent):
        super(XYZPlotWidget, self).__init__(parent)
        self.main_window = parent

        #self.show()
        #g = gl.GLGridItem()
        #self.addItem(g)

    # --------------------------------------------------------------------------

    def plot(self, image):
        plot_item = gl.GLSurfacePlotItem(z=image, shader='shaded', color=(0.5, 0.5, 1, 1))
        self.addItem(plot_item)


# ==============================================================================
