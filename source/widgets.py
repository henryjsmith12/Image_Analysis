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
        self.file_list.itemDoubleClicked.connect(self.loadFile)


    def openDirectory(self):
        # Find directory with image files
        self.directory = QtGui.QFileDialog.getExistingDirectory(self, "Open Folder")

        # List of files in directory
        files = os.listdir(self.directory)

        # Display file names in list
        self.file_list.clear()
        self.file_list.addItems(files)


    def clearFileList(self):
        self.file_list.clear()


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


    def displayImage(self, file_path):
        self.image = plt.imread(file_path, format="RGB")
        self.setImage(self.image)

        view = self.getView()
        view.setXLink(self.main_window.x_plot_widget)
        view.setYLink(self.main_window.y_plot_widget)

        cols = self.image.mean(axis=0)
        rows = self.image.mean(axis=1)


# ==============================================================================

class XPlotWidget(pg.PlotWidget):

    """
    - Plots x-values vs average intensity
    - Axes linked to ImageWidget and YPlotWidget
    """

    def __init__ (self, parent):
        super(XPlotWidget, self).__init__(parent)
        self.main_window = parent


# ==============================================================================

class YPlotWidget(pg.PlotWidget):

    """
    - Plots y-values vs average intensity
    - Axes linked to ImageWidget and XPlotWidget
    """

    def __init__ (self, parent):
        super(YPlotWidget, self).__init__(parent)
        self.main_window = parent


# ==============================================================================

class XYZPlotWidget(pg.PlotWidget):

    """
    3D view of x vs y vs intensity
    """

    def __init__ (self, parent):
        super(XYZPlotWidget, self).__init__(parent)
        self.main_window = parent
