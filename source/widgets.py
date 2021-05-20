"""
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

# ==============================================================================

import pyqtgraph as pg
import matplotlib.pyplot as plt
from pyqtgraph.Qt import QtGui

# ==============================================================================

class OptionsWidget(pg.LayoutWidget):

    """
    - File selector
    - List of image files
    - Plotting options
    """

    def __init__ (self, parent=None):
        super(OptionsWidget, self).__init__(parent)

        self.options_gb = QtGui.QGroupBox("Plotting Options")
        self.files_gb = QtGui.QGroupBox("Image Files")

        self.addWidget(self.options_gb, row=0, col=0)
        self.addWidget(self.files_gb, row=1, col=0)

        # Create/add layouts
        self.options_layout = QtGui.QGridLayout()
        self.files_layout = QtGui.QGridLayout()
        self.options_gb.setLayout(self.options_layout)
        self.files_gb.setLayout(self.files_layout)


    def setupComponents(self):

        # Create options widgets
        ...

        # Create file widgets
        self.open_file_btn = QtGui.QPushButton("Open File")
        self.clear_btn = QtGui.QPushButton("Clear")
        self.file_list = QtGui.QListWidget()

        # Add widgets to GroupBoxes
        self.files_layout.addWidget(self.open_file_btn, 0, 0)
        self.files_layout.addWidget(self.clear_btn, 0, 1)
        self.files_layout.addWidget(self.file_list, 1, 0, 4, 2)

        # Link widgets to actions
        self.open_file_btn.clicked.connect(self.openFile)
        self.clear_btn.clicked.connect(self.clearFileList)


    def openFile(self):
        ...


    def clearFileList(self):
        ...


# ==============================================================================

class AnalysisWidget(pg.LayoutWidget):

    """
    ROI values, peak values, etc.
    """

    def __init__ (self, parent=None):
        super(AnalysisWidget, self).__init__(parent)


    def setupComponents(self):
        ...


# ==============================================================================

class ImageWidget(pg.ImageView):

    """
    - Image display
    - Interactive intensity control
    """

    def __init__ (self, parent=None):
        super(ImageWidget, self).__init__(parent)

        image = plt.imread("S012/sio6smo6_1_S012_00001.tif")

        self.setImage(image)


# ==============================================================================

class XPlotWidget(pg.PlotWidget):

    """
    - Plots x-values vs average intensity
    - Axes linked to ImageWidget and YPlotWidget
    """

    def __init__ (self, parent=None):
        super(XPlotWidget, self).__init__(parent)


# ==============================================================================

class YPlotWidget(pg.PlotWidget):

    """
    - Plots y-values vs average intensity
    - Axes linked to ImageWidget and XPlotWidget
    """

    def __init__ (self, parent=None):
        super(YPlotWidget, self).__init__(parent)


# ==============================================================================

class XYZPlotWidget(pg.PlotWidget):

    """
    3D view of x vs y vs intensity
    """

    def __init__ (self, parent=None):
        super(XYZPlotWidget, self).__init__(parent)
