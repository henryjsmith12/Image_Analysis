"""
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

# ==============================================================================

import pyqtgraph as pg
import pyqtgraph.opengl as gl
import matplotlib.pyplot as plt
from matplotlib import cm
from PIL import Image
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import os
import sys
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
        self.crosshair_chkbox = QtGui.QCheckBox("Crosshair")
        self.reset_btn = QtGui.QPushButton("Reset View")
        self.live_plot_btn = QtGui.QPushButton("Simulate Live Plotting")

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

        self.options_layout.addWidget(self.crosshair_chkbox, 0, 0, 1, 2)
        self.options_layout.addWidget(self.reset_btn, 0, 2, 1, 3)
        self.options_layout.addWidget(self.live_plot_btn, 4, 0, 1, 2)
        self.options_layout.addWidget(self.scale_lbl, 1, 0, 1, 1)
        self.options_layout.addWidget(self.linear_scale_rbtn, 1, 1)
        self.options_layout.addWidget(self.log_scale_rbtn, 1, 2)
        self.options_layout.addWidget(self.mouse_mode_lbl, 2, 0)
        self.options_layout.addWidget(self.pan_mode_rbtn, 2, 1)
        self.options_layout.addWidget(self.rect_mode_rbtn, 2, 2)

        # Link widgets to actions
        self.browse_btn.clicked.connect(self.openDirectory)
        self.clear_btn.clicked.connect(self.clear)
        self.file_list.itemClicked.connect(self.loadFile)
        self.crosshair_chkbox.stateChanged.connect(self.toggleCrosshair)
        self.reset_btn.clicked.connect(self.resetView)
        self.live_plot_btn.clicked.connect(self.simLivePlotting)
        self.linear_scale_rbtn.toggled.connect(self.toggleScale)
        self.log_scale_rbtn.toggled.connect(self.toggleScale)
        self.pan_mode_rbtn.toggled.connect(self.toggleMouseMode)
        self.rect_mode_rbtn.toggled.connect(self.toggleMouseMode)

    # --------------------------------------------------------------------------

    def openDirectory(self):
        # Find directory with image files
        self.directory = QtGui.QFileDialog.getExistingDirectory(self, "Open Folder")

        # List of files
        files = sorted(os.listdir(self.directory))

        # Display files
        self.file_list.clear()
        self.file_list.addItems(files)

    # --------------------------------------------------------------------------

    def clear(self):
        self.file_list.clear()
        self.main_window.image_widget.clear()
        self.main_window.x_plot_widget.clear()
        self.main_window.y_plot_widget.clear()
        self.current_file_txtbox.setText("")

    # --------------------------------------------------------------------------

    def loadFile(self, file):
        #Concatenate directory and file names
        self.file_path = f"{self.directory}/{file.text()}"
        self.main_window.image_widget.displayImage(self.file_path)
        self.current_file_txtbox.setText(file.text())
        self.options_gbox.setEnabled(True)

    # --------------------------------------------------------------------------

    def toggleCrosshair(self, state):
        # Turn histogram on/off
        if state == 2:
            self.main_window.image_widget.v_line.setVisible(True)
            self.main_window.image_widget.h_line.setVisible(True)
        else:
            self.main_window.image_widget.v_line.setVisible(False)
            self.main_window.image_widget.h_line.setVisible(False)

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

        if button.text() == "Pan":
            self.main_window.image_widget.view.setMouseMode(pg.ViewBox.PanMode)
        else:
            self.main_window.image_widget.view.setMouseMode(pg.ViewBox.RectMode)

    # --------------------------------------------------------------------------

    def simLivePlotting(self):
        for i in range(self.file_list.count()):
            self.loadFile(self.file_list.item(i))
            QtGui.QApplication.processEvents()


# ==============================================================================

class AnalysisWidget(pg.LayoutWidget):

    """
    ROI values, peak values, etc.
    """

    def __init__ (self, parent):
        super(AnalysisWidget, self).__init__(parent)
        self.main_window = parent

    # --------------------------------------------------------------------------

    def setupComponents(self):
        ...


# ==============================================================================

class ImageWidget(pg.PlotWidget):

    """
    - Image display
    - Interactive intensity control
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

        # Create crosshair
        self.v_line = pg.InfiniteLine(angle=90, movable=False)
        self.h_line = pg.InfiniteLine(angle=0, movable=False)
        self.v_line.setVisible(False)
        self.h_line.setVisible(False)
        self.addItem(self.v_line, ignoreBounds=True)
        self.addItem(self.h_line, ignoreBounds=True)

    # --------------------------------------------------------------------------

    def displayImage(self, file_path):

        # Read and set image file
        self.image = ndimage.rotate(tiff.imread(file_path), 90)
        color_image = (plt.cm.jet(self.image) * 2**32).astype(int)
        self.image_item.setImage(color_image)

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

        self.view.scene().sigMouseMoved.connect(self.updateCrosshair)

        self.updatePlots()

    # --------------------------------------------------------------------------

    def updatePlots(self):
        try:
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

        x_min, x_max = int(self.view_range[0][0]), int(self.view_range[0][1])
        y_min, y_max = int(self.view_range[1][0]), int(self.view_range[1][1])

        image_in_view = self.image[x_min:x_max, y_min:y_max]

        if 0 in image_in_view.shape:
            return
        cols = image_in_view.mean(axis=1)
        rows = image_in_view.mean(axis=0)

        x_curve = np.zeros((self.image.shape[0]))
        y_curve = np.zeros((self.image.shape[1]))
        x_curve[x_min:x_min + image_in_view.shape[0]] = cols
        y_curve[y_min:y_min + image_in_view.shape[1]] = rows

        return x_curve, y_curve

    # --------------------------------------------------------------------------

    def updateCrosshair(self, scene_point):
        #mouse_point = self.view.
        view_point = self.view.mapSceneToView(scene_point)
        print(view_point)

        self.v_line.setPos(view_point.x())
        self.h_line.setPos(view_point.y())


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

class XYZPlotWidget(gl.GLViewWidget):

    """
    3D view of x vs y vs intensity
    """

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
