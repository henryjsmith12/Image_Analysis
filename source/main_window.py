"""
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

# ==============================================================================

import pyqtgraph as pg
from pyqtgraph.Qt import QtGui
from pyqtgraph.dockarea import *
import numpy as np
import matplotlib.pyplot as plt

# Local
from source.widgets import *

# ==============================================================================

class MainWindow(QtGui.QMainWindow):

    """
    - Initializes main window
    - Creates/adds docked widgets
    """

    def __init__ (self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.dock_area = DockArea()
        self.setCentralWidget(self.dock_area)

        self.setMinimumSize(900, 600)
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowTitle("Image Analysis")

        # Docked widgets for main window
        self.options_dock = Dock("Options", size=(200, 200))
        self.analysis_dock = Dock("Analysis", size=(200, 200))
        self.image_dock = Dock("Image", size=(200, 200))
        self.x_plot_dock = Dock("x Plot", size=(200, 200))
        self.y_plot_dock = Dock("y Plot", size=(200, 200))
        self.xyz_plot_dock = Dock("3D Plot", size=(200, 200))

        # Add/organize docks
        self.dock_area.addDock(self.options_dock, "left")
        self.dock_area.addDock(self.analysis_dock, "right", self.options_dock)
        self.dock_area.addDock(self.image_dock, "top", self.analysis_dock)
        self.dock_area.addDock(self.x_plot_dock, "top", self.image_dock)
        self.dock_area.addDock(self.y_plot_dock, "top", self.analysis_dock)
        self.dock_area.addDock(self.xyz_plot_dock, "top", self.y_plot_dock)
        self.dock_area.moveDock(self.xyz_plot_dock, "right", self.x_plot_dock)
        self.dock_area.moveDock(self.y_plot_dock, "right", self.image_dock)

        # Create widgets and setup widget components
        self.options_widget = OptionsWidget() # File options widget
        self.options_widget.setupComponents()
        self.analysis_widget = AnalysisWidget() # Image analysis/info widget
        self.analysis_widget.setupComponents()
        self.image_widget = ImageWidget() # Image widget with sample image
        self.x_plot_widget = XPlotWidget() # Plot x-value vs average intensity
        self.y_plot_widget = YPlotWidget() # Plot y-value vs average intensity
        self.xyz_plot_widget = XYZPlotWidget() # Plots 3D model

        # Add widgets to docks
        self.options_dock.addWidget(self.options_widget)
        self.analysis_dock.addWidget(self.analysis_widget)
        self.image_dock.addWidget(self.image_widget)
        self.x_plot_dock.addWidget(self.x_plot_widget)
        self.y_plot_dock.addWidget(self.y_plot_widget)
        self.xyz_plot_dock.addWidget(self.xyz_plot_widget)
