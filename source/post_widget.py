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
        self.createWidgets()

        self.layout.addWidget(self.dock_area)

    # --------------------------------------------------------------------------

    def createDocks(self):
        self.data_selection_dock = Dock("Data Selection", size=(100, 100), hideTitle=True)
        self.options_dock = Dock("Options", size=(100, 100), hideTitle=True)
        self.analysis_dock = Dock("Analysis", size=(200, 100))
        self.roi_analysis_dock = Dock("ROI's", size=(200, 100))
        self.image_dock = Dock("Image", size=(200, 100), hideTitle=True)

        self.dock_area.addDock(self.data_selection_dock)
        self.dock_area.addDock(self.options_dock, "bottom", self.data_selection_dock)
        self.dock_area.addDock(self.analysis_dock, "right", self.options_dock)
        self.dock_area.addDock(self.roi_analysis_dock, "right", self.options_dock)
        self.dock_area.addDock(self.image_dock, "top", self.analysis_dock)
        self.dock_area.moveDock(self.image_dock, "right", self.data_selection_dock)
        self.dock_area.moveDock(self.analysis_dock, "above", self.roi_analysis_dock)

    # --------------------------------------------------------------------------

    def createWidgets(self):
        self.data_selection_widget = DataSelectionWidget(self)
        self.options_widget = OptionsWidget(self)
        self.analysis_widget = AnalysisWidget(self)
        self.roi_analysis_widget = ROIAnalysisWidget(self)
        self.image_widget = ImageWidget(self)

        self.data_selection_dock.addWidget(self.data_selection_widget)
        self.options_dock.addWidget(self.options_widget)
        self.analysis_dock.addWidget(self.analysis_widget)
        self.roi_analysis_dock.addWidget(self.roi_analysis_widget)
        self.image_dock.addWidget(self.image_widget)

# ==============================================================================

class DataSelectionWidget(pg.LayoutWidget):

    def __init__ (self, parent):
        super(DataSelectionWidget, self).__init__(parent)
        self.main_widget = parent

# ==============================================================================

class OptionsWidget(pg.LayoutWidget):

    def __init__ (self, parent):
        super(OptionsWidget, self).__init__(parent)
        self.main_widget = parent

# ==============================================================================

class AnalysisWidget(pg.LayoutWidget):

    def __init__ (self, parent):
        super(AnalysisWidget, self).__init__(parent)
        self.main_widget = parent

# ==============================================================================

class ROIAnalysisWidget(pg.LayoutWidget):

    def __init__ (self, parent):
        super(ROIAnalysisWidget, self).__init__(parent)
        self.main_widget = parent

# ==============================================================================
