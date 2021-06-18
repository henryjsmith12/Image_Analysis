"""
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

# ==============================================================================

from pyqtgraph.Qt import QtGui
from pyqtgraph.dockarea import *

from source.widgets import * # Local

# ==============================================================================

class MainWindow(QtGui.QMainWindow):

    """
    Contains docked widgets and components of app.

    - OptionsWidget: Image selection modes and plotting options.

    - AnalysisWidget: ROI controls and mouse/image information.

    - ImageWidget: Plot window for image and ROI's.
    """

    def __init__ (self, parent=None):
        super(MainWindow, self).__init__(parent)

        # Customizable dock area
        self.dock_area = DockArea()
        self.setCentralWidget(self.dock_area)

        # Window attributes
        self.setMinimumSize(900, 600)
        self.setGeometry(100, 100, 1250, 900)
        self.setWindowTitle("Image Analysis")

        self.createDocks()
        self.createWidgets()

    # --------------------------------------------------------------------------

    def createDocks(self):
        # Docked widgets for main window
        self.options_dock = Dock("Options", size=(100, 300))
        self.analysis_dock = Dock("Analysis", size=(300, 100))
        self.image_dock = Dock("Image", size=(300, 300))

        # Add/organize docks
        self.dock_area.addDock(self.options_dock, "left")
        self.dock_area.addDock(self.image_dock, "right", self.options_dock)
        self.dock_area.addDock(self.analysis_dock, "bottom", self.image_dock)

    # --------------------------------------------------------------------------

    def createWidgets(self):
        # Create widgets and setup widget components
        self.options_widget = OptionsWidget(self) # File options widget
        self.options_widget.setupComponents() # Options (sub)widget creation
        self.analysis_widget = AnalysisWidget(self) # Image analysis/info widget
        self.analysis_widget.setupComponents() # Analysis (sub)widgets
        self.image_widget = ImageWidget(self) # Image widget with sample image

        # Add widgets to dock objects
        self.options_dock.addWidget(self.options_widget)
        self.analysis_dock.addWidget(self.analysis_widget)
        self.image_dock.addWidget(self.image_widget)

# ==============================================================================
