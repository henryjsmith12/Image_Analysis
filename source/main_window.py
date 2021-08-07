"""
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

# ==============================================================================

from pyqtgraph.Qt import QtGui
from pyqtgraph.dockarea import *

from source.gui_widgets import *

# ==============================================================================

class MainWindow(QtGui.QMainWindow):

    """
    Contains docked widgets and components of main window.

    - OptionsWidget: Image selection modes and plotting options.

    - AnalysisWidget: ROI controls and mouse/image information.

    - ImageWidget: Plot window for image and ROI's.

    - ROIWidget: Contains average intensity plots for ROI's.

    - AdvancedROIWidget: Contains plot that can be customized to show
        relationships between ROI's
    """

    def __init__ (self, parent=None):
        super(MainWindow, self).__init__(parent)

        # Customizable dock area
        self.dock_area = DockArea()
        self.setCentralWidget(self.dock_area)

        # Window attributes
        self.setMinimumSize(1400, 800)
        self.setGeometry(0, 50, 1450, 800)
        self.setWindowTitle("Image Analysis")

        self.createDocks()
        self.createWidgets()

    # --------------------------------------------------------------------------

    def createDocks(self):

        """
        Creates dock widgets and adds them to the main window.
        """

        # Docked widgets for main window
        self.options_dock = Dock("Options", size=(100, 300), hideTitle=True)
        self.analysis_dock = Dock("Analysis", size=(300, 50), hideTitle=True)
        self.image_dock = Dock("Image", size=(300, 350))
        self.roi_plots_dock = Dock("ROI", size=(300, 350))
        self.advanced_roi_plot_dock = Dock("Advanced ROI", size=(300, 350))

        # Dock organization
        self.dock_area.addDock(self.options_dock, "left")
        self.dock_area.addDock(self.image_dock, "right", self.options_dock)
        self.dock_area.addDock(self.roi_plots_dock, "right", self.options_dock)
        self.dock_area.addDock(self.advanced_roi_plot_dock, "right", self.options_dock)
        self.dock_area.addDock(self.analysis_dock, "bottom", self.image_dock)
        self.dock_area.moveDock(self.analysis_dock, "bottom", self.roi_plots_dock)
        self.dock_area.moveDock(self.analysis_dock, "bottom", self.advanced_roi_plot_dock)
        self.dock_area.moveDock(self.image_dock, "above", self.advanced_roi_plot_dock)
        self.dock_area.moveDock(self.roi_plots_dock, "above", self.advanced_roi_plot_dock)
        self.dock_area.moveDock(self.image_dock, "above", self.roi_plots_dock)

    # --------------------------------------------------------------------------

    def createWidgets(self):

        """
        Creates widgets and adds them to their respective dock.
        """

        # Create widgets and set up widget components
        self.options_widget = OptionsWidget(self)
        self.options_widget.setupComponents()
        self.analysis_widget = AnalysisWidget(self)
        self.analysis_widget.setupComponents()
        self.roi_plots_widget = ROIPlotsWidget(self)
        self.image_widget = ImageWidget(self)
        self.advanced_roi_plot_widget = AdvancedROIPlotWidget(self)

        # Add widgets to docks
        self.options_dock.addWidget(self.options_widget)
        self.analysis_dock.addWidget(self.analysis_widget)
        self.image_dock.addWidget(self.image_widget)
        self.roi_plots_dock.addWidget(self.roi_plots_widget)
        self.advanced_roi_plot_dock.addWidget(self.advanced_roi_plot_widget)

# ==============================================================================
