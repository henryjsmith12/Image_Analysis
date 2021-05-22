"""
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

# ==============================================================================

import pyqtgraph as pg
import matplotlib.pyplot as plt
from pyqtgraph.Qt import QtGui
import numpy as np
import os
import sys

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

        # Add GroupBoxes to widget
        self.addWidget(self.options_gbox, row=0, col=0)
        self.addWidget(self.files_gbox, row=1, col=0)

        # Create/add layouts
        self.options_layout = QtGui.QGridLayout()
        self.files_layout = QtGui.QGridLayout()
        self.options_gbox.setLayout(self.options_layout)
        self.files_gbox.setLayout(self.files_layout)

    # --------------------------------------------------------------------------

    def setupComponents(self):
        # Create options widgets
        ...

        # Create file widgets
        self.browse_btn = QtGui.QPushButton("Browse")
        self.clear_btn = QtGui.QPushButton("Clear")
        self.file_list = QtGui.QListWidget()

        # Add widgets to GroupBoxes
        self.files_layout.addWidget(self.browse_btn, 0, 0)
        self.files_layout.addWidget(self.clear_btn, 0, 1)
        self.files_layout.addWidget(self.file_list, 1, 0, 4, 2)

        # Link widgets to actions
        self.browse_btn.clicked.connect(self.openDirectory)
        self.clear_btn.clicked.connect(self.clearFileList)
        self.file_list.itemClicked.connect(self.loadFile)

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

    def clearFileList(self):
        self.file_list.clear()

    # --------------------------------------------------------------------------

    def loadFile(self, file):
        #Concatenate directory and file names
        file_path = f"{self.directory}/{file.text()}"
        self.main_window.image_widget.displayImage(file_path)


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

    # --------------------------------------------------------------------------

    def displayImage(self, file_path):

        # Read and set image file
        self.image = plt.imread(file_path)
        self.setImage(self.image)

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

        # First plot
        self.updatePlots()

    # --------------------------------------------------------------------------

    def updatePlots(self):
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

        # Mean of columns/rows
        cols = view_image.mean(axis=1)
        rows = view_image.mean(axis=0)

        # RGBA to grayscale conversion
        # Calculate avg intensity (0-255) of each row/column
        col_avgs = 0.299 * cols[:,0] + 0.587 * cols[:,1] + 0.114 * cols[:,2]
        row_avgs = 0.299 * rows[:,0] + 0.587 * rows[:,1] + 0.114 * rows[:,2]

        # Clear previous plots
        self.main_window.x_plot_widget.clear()
        self.main_window.y_plot_widget.clear()

        # Display new plots
        self.main_window.x_plot_widget.plot(col_avgs)
        self.main_window.y_plot_widget.plot(row_avgs, range(len(row_avgs)))


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

class XYZPlotWidget(pg.PlotWidget):

    """
    3D view of x vs y vs intensity
    """

    def __init__ (self, parent):
        super(XYZPlotWidget, self).__init__(parent)
        self.main_window = parent


# ==============================================================================
