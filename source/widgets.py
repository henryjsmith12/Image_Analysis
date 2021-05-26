"""
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

# ==============================================================================

import pyqtgraph as pg
import pyqtgraph.opengl as gl
import matplotlib.pyplot as plt
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import os
import sys
from scipy import ndimage
import threading
import _thread

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

        # Create options widgets
        self.hist_chkbox = QtGui.QCheckBox("Histogram")
        self.reset_btn = QtGui.QPushButton("Reset View")
        #self.live_plot_btn = QtGui.QPushButton("Simulate Live Plotting")
        self.scale_lbl = QtGui.QLabel("Scale:")
        self.linear_scale_rbtn = QtGui.QRadioButton("Linear")
        self.linear_scale_rbtn.setChecked(True)
        self.log_scale_rbtn = QtGui.QRadioButton("Logarithmic")


        # Add widgets to GroupBoxes
        self.files_layout.addWidget(self.browse_btn, 0, 0)
        self.files_layout.addWidget(self.clear_btn, 0, 1)
        self.files_layout.addWidget(self.file_list, 1, 0, 4, 2)
        self.options_layout.addWidget(self.hist_chkbox, 0, 0, 1, 2)
        self.options_layout.addWidget(self.reset_btn, 0, 2, 1, 3)
        #self.options_layout.addWidget(self.live_plot_btn, 1, 0, 1, 2)
        self.options_layout.addWidget(self.scale_lbl, 1, 0, 1, 1)
        self.options_layout.addWidget(self.linear_scale_rbtn, 1, 1, 1, 2)
        self.options_layout.addWidget(self.log_scale_rbtn, 1, 3, 1, 2)

        # Link widgets to actions
        self.browse_btn.clicked.connect(self.openDirectory)
        self.clear_btn.clicked.connect(self.clear)
        self.file_list.itemClicked.connect(self.loadFile)
        self.hist_chkbox.stateChanged.connect(self.toggleHistogram)
        self.reset_btn.clicked.connect(self.resetView)
        #self.live_plot_btn.clicked.connect(self.simLivePlotting)
        self.linear_scale_rbtn.toggled.connect(self.toggleScale)
        self.log_scale_rbtn.toggled.connect(self.toggleScale)

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

    # --------------------------------------------------------------------------

    def loadFile(self, file):
        #Concatenate directory and file names
        self.file_path = f"{self.directory}/{file.text()}"
        self.main_window.image_widget.displayImage(self.file_path)
        self.options_gbox.setEnabled(True)

    # --------------------------------------------------------------------------

    def toggleHistogram(self, state):
        # Turn histogram on/off
        if state == 2:
            self.main_window.image_widget.ui.histogram.show()
        else:
            self.main_window.image_widget.ui.histogram.hide()

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

class ImageWidget(pg.ImageView):

    """
    - Image display
    - Interactive intensity control
    """

    def __init__ (self, parent):
        super(ImageWidget, self).__init__(parent)
        self.main_window = parent

        # Delete unnecessary features
        self.ui.roiBtn.hide()
        self.ui.menuBtn.hide()
        self.ui.histogram.hide()

    # --------------------------------------------------------------------------

    def displayImage(self, file_path):
        # Read and set image file
        self.image = plt.imread(file_path)
        self.setImage(ndimage.rotate(self.image, 90))

        # For 3D plotting
        self.mean_image = self.image[:,:,:-1].mean(axis=2)

        # Get viewing window
        self.view = self.getView()
        self.view.setLimits(
            xMin=0,
            xMax=(self.image.shape[0] + 50),
            yMin=0,
            yMax=(self.image.shape[1] + 50)
        )

        # Link view to profile plots
        self.view.setXLink(self.main_window.x_plot_widget)
        self.view.setYLink(self.main_window.y_plot_widget)
        self.main_window.y_plot_widget.invertY(True)

        # Dynamically update plots when viewing window changes
        self.view.sigRangeChanged.connect(self.updatePlots)

        self.updatePlots()

    # --------------------------------------------------------------------------

    def updatePlots(self):
        col_avgs, row_avgs = self.calculateAvgIntensity()

        # Clear plots
        self.main_window.x_plot_widget.clear()
        self.main_window.y_plot_widget.clear()
        #self.main_window.xyz_plot_widget.clear()

        # Display new plots
        self.main_window.x_plot_widget.plot(col_avgs)
        self.main_window.y_plot_widget.plot(x=row_avgs, y=range(len(row_avgs)))
        #self.main_window.xyz_plot_widget.plot(self.mean_image)

    # --------------------------------------------------------------------------

    def calculateAvgIntensity(self):
        """
        ** Avg intensity for viewing window (worse performance)

        # Coords visible in viewing window
        self.view_range = self.view.viewRange()

        # Limits of viewing window
        x_min, x_max = max(int(self.view_range[0][0]), 0), int(self.view_range[0][1])
        y_min, y_max = max(int(self.view_range[1][0]), 0), int(self.view_range[1][1])

        # Embed block of image into array of zeros
        # Able to take avg intensity of that part
        view_image = np.zeros(self.image.shape, dtype=np.int)
        im_part = self.image[x_min:x_max, y_min:y_max]
        if 0 in im_part.shape:
            return
        view_image[x_min:x_min + im_part.shape[0], y_min:y_min + im_part.shape[1]] = im_part
        """

        # Plotting for better performance
        view_image = self.image

        # Mean of columns/rows
        cols = view_image.mean(axis=1)
        rows = view_image.mean(axis=0)

        # RGBA to grayscale conversion
        # Calculate avg intensity (0-255) of each row/column
        col_avgs = 0.299 * cols[:,0] + 0.587 * cols[:,1] + 0.114 * cols[:,2]
        row_avgs = 0.299 * rows[:,0] + 0.587 * rows[:,1] + 0.114 * rows[:,2]

        return col_avgs, row_avgs

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
