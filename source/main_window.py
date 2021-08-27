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

    def __init__ (self, parent=None):
        super(MainWindow, self).__init__(parent)

        # Window attributes
        self.setMinimumSize(1400, 800)
        self.setGeometry(0, 50, 1450, 800)
        self.setWindowTitle("Image Analysis")

        # Tab widget
        self.tab_widget = QtGui.QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.setCentralWidget(self.tab_widget)

        # Menu bar
        self.menu_bar = self.menuBar()
        self.menu_bar.setNativeMenuBar(False)
        self.file_menu_item = self.menu_bar.addMenu(" File")
        self.new_menu_action = self.file_menu_item.addAction("New")
        self.help_menu_item = self.menu_bar.addMenu(" Help")

        self.new_menu_action.triggered.connect(self.newWidgetTab)

    # --------------------------------------------------------------------------

    def newWidgetTab(self):

        dialog = WidgetSelectionDialog()

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

        # Create widgets and set up components
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

class WidgetSelectionDialog(QtGui.QDialog):

    def __init__ (self):
        super().__init__()

        self.setWindowModality(QtCore.Qt.ApplicationModal)

        self.widget_type_lbl = QtGui.QLabel("Widget Type:")
        self.widget_type_cbox = QtGui.QComboBox()
        self.widget_type_cbox.addItems(["", "Live Plotting", "Post Plotting"])
        self.widget_name_lbl = QtGui.QLabel("Tab Name:")
        self.widget_name_txtbox = QtGui.QLineEdit()
        self.ok_btn = QtGui.QPushButton("OK")

        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)

        self.layout.addWidget(self.widget_type_lbl, 0, 0)
        self.layout.addWidget(self.widget_type_cbox, 0, 1)
        self.layout.addWidget(self.widget_name_lbl, 1, 0)
        self.layout.addWidget(self.widget_name_txtbox, 1, 1)
        self.layout.addWidget(self.ok_btn, 2, 1)

        self.ok_btn.clicked.connect(self.acceptDialog)

        # Changes widget tab name to generic placeholder name
        self.widget_type_cbox.currentTextChanged.connect(lambda text: \
            self.widget_name_txtbox.setText(text))

        self.exec_()

    def acceptDialog(self):

        if self.widget_type_cbox.currentText() != "":
            self.widget_type = self.widget_type_cbox.currentText()
            self.widget_name = self.widget_name_txtbox.text()
            self.accept()

# ==============================================================================
