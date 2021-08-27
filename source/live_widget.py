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

class LivePlottingWidget(QtGui.QWidget):

    def __init__ (self):
        super().__init__()

        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)

        self.dock_area = DockArea()
        self.createDocks()

        self.layout.addWidget(self.dock_area)

    # --------------------------------------------------------------------------

    def createDocks(self):

        self.image_selection_dock = Dock("Image Selection", size=(100, 100), hideTitle=True)
        self.options_dock = Dock("Options", size=(100, 100), hideTitle=True)
        self.analysis_dock = Dock("Analysis", size=(200, 100), hideTitle=True)
        self.image_dock = Dock("Image", size=(200, 100), hideTitle=True)

        self.dock_area.addDock(self.image_selection_dock)
        self.dock_area.addDock(self.options_dock, "bottom", self.image_selection_dock)
        self.dock_area.addDock(self.analysis_dock, "right", self.options_dock)
        self.dock_area.addDock(self.image_dock, "top", self.analysis_dock)
        self.dock_area.moveDock(self.image_dock, "right", self.image_selection_dock)

    # --------------------------------------------------------------------------

    def createWidgets(self):

        self.image_selection_widget = ImageSelectionWidget(self)
        self.options_widget = OptionsWidget(self)
        self.analysis_widget = AnalysisWidget(self)
        self.image_widget = ImageWidget(self)

# ==============================================================================

class ImageSelectionWidget(pg.LayoutWidget):

    def __init__ (self):
        super(ImageSelectionWidget, self).__init__(parent)
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