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

        dock_area = DockArea()
        self.setCentralWidget(dock_area)

        self.setMinimumSize(900, 600)
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowTitle("Image Analysis")

        # Docked widgets for main window
        options_dock = Dock("Options", size=(200, 200))
        analysis_dock = Dock("Analysis", size=(200, 200))
        image_dock = Dock("Image", size=(200, 200))
        x_plot_dock = Dock("x Plot", size=(200, 200))
        y_plot_dock = Dock("y Plot", size=(200, 200))
        xyz_plot_dock = Dock("3D Plot", size=(200, 200))

        # Add/organize docks
        dock_area.addDock(options_dock, "left")
        dock_area.addDock(analysis_dock, "right", options_dock)
        dock_area.addDock(image_dock, "top", analysis_dock)
        dock_area.addDock(x_plot_dock, "top", image_dock)
        dock_area.addDock(y_plot_dock, "top", analysis_dock)
        dock_area.addDock(xyz_plot_dock, "top", y_plot_dock)
        dock_area.moveDock(xyz_plot_dock, "right", x_plot_dock)
        dock_area.moveDock(y_plot_dock, "right", image_dock)

        options_widget = OptionsWidget() # File options widget
        options_widget.setupComponents()

        analysis_dock_widget = AnalysisWidget() # Image analysis/info widget

        image_widget = ImageWidget() # Image widget with sample image

        x_plot_widget = XPlotWidget() # Plot x-value vs average intensity

        y_plot_widget = YPlotWidget() # Plot y-value vs average intensity

        xyz_plot_widget = XYZPlotWidget() # Plots 3D model

        # Add widgets to docks
        options_dock.addWidget(options_widget)
        analysis_dock.addWidget(analysis_dock_widget)
        image_dock.addWidget(image_widget)
        x_plot_dock.addWidget(x_plot_widget)
        y_plot_dock.addWidget(y_plot_widget)
        xyz_plot_dock.addWidget(xyz_plot_widget)
