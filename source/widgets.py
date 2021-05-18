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

        # GroupBox Sample
        gb1 = QtGui.QGroupBox("Plotting Options")
        gb2 = QtGui.QGroupBox("Image Files")

        self.addWidget(gb1, row=0, col=0)
        self.addWidget(gb2, row=1, col=0)


# ==============================================================================

class AnalysisWidget(pg.LayoutWidget):

    """
    ROI values, peak values, etc.
    """

    def __init__ (self, parent=None):
        super(AnalysisWidget, self).__init__(parent)


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
