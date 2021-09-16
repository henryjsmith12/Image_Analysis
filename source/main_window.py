"""
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

# ==============================================================================

from pyqtgraph.Qt import QtGui

from source.live_widget import *
from source.post_widget import *

# ==============================================================================

class MainWindow(QtGui.QMainWindow):
    """
    Creates the main window, which houses:
    - A tab widget that houses widget tabs
    - A menu bar that allows users to add new widget tabs
    """

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

        # Signals
        self.new_menu_action.triggered.connect(self.newWidgetTab) # Opens dialog
        self.tab_widget.tabCloseRequested.connect(lambda index: \
            self.tab_widget.removeTab(index)) # Remove tab

        # Tabs open on initial startup (default)
        self.tab_widget.addTab(LivePlottingWidget(), "Live Plotting")
        self.tab_widget.addTab(PostPlottingWidget(), "Post Plotting")

    # --------------------------------------------------------------------------

    def newWidgetTab(self):
        """
        - Opens new widget dialog
        - Creates instance of selected widget
        - Houses widget in tab
        """

        dialog = WidgetSelectionDialog()
        tab = None

        if dialog.result() == 1:
            if dialog.widget_type == "Live Plotting":
                tab = LivePlottingWidget()
            elif dialog.widget_type == "Post Plotting":
                tab = PostPlottingWidget()

            self.tab_widget.addTab(tab, dialog.widget_name)

# ==============================================================================

class WidgetSelectionDialog(QtGui.QDialog):
    """
    Dialog that allows user to:
    - Select type of new widget
    - Select name for new widget tab
    """

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

        # Signals
        self.ok_btn.clicked.connect(self.acceptDialog)
        self.widget_type_cbox.currentTextChanged.connect(lambda text: \
            self.widget_name_txtbox.setText(text))

        self.exec_()

    # --------------------------------------------------------------------------

    def acceptDialog(self):
        """
        - Creates new widget tab
        - Triggered by clicking ok_btn
        """
        
        if self.widget_type_cbox.currentText() != "":
            self.widget_type = self.widget_type_cbox.currentText()
            self.widget_name = self.widget_name_txtbox.text()
            self.accept()

# ==============================================================================
