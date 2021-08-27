"""
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

# ==============================================================================

import math
import matplotlib.colors as colors
import matplotlib.pyplot as plt
import numpy as np
import os
import pyqtgraph as pg
from pyqtgraph.dockarea import *
from pyqtgraph.Qt import QtGui, QtCore
from scipy import ndimage
import tifffile as tiff
import time
import warnings

from source.general_widgets import *

# ==============================================================================

class PostPlottingWidget(QtGui.QWidget):

    def __init__ (self):
        super().__init__()

        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)

        self.dock_area = DockArea()
        self.createDocks()

        self.layout.addWidget(self.dock_area)

    # --------------------------------------------------------------------------

    def createDocks(self):
        ...

    # --------------------------------------------------------------------------

    def createWidgets(self):
        ...

# ==============================================================================

class DataSelectionWidget(pg.LayoutWidget):

    def __init__ (self):
        super(DataSelectionWidget, self).__init__(parent)
        self.parent = parent

# ==============================================================================

class OptionsWidget(pg.LayoutWidget):

    def __init__ (self):
        super(OptionsWidget, self).__init__(parent)
        self.parent = parent

# ==============================================================================

class AnalysisWidget(pg.LayoutWidget):

    def __init__ (self):
        super(AnalysisWidget, self).__init__(parent)
        self.parent = parent

# ==============================================================================

class ROIAnalysisWidget(pg.LayoutWidget):

    def __init__ (self):
        super(ROIAnalysisWidget, self).__init__(parent)
        self.parent = parent

# ==============================================================================
