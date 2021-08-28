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
        self.createWidgets()

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

        self.image_selection_dock.addWidget(self.image_selection_widget)
        self.options_dock.addWidget(self.options_widget)
        self.analysis_dock.addWidget(self.analysis_widget)
        self.image_dock.addWidget(self.image_widget)

# ==============================================================================

class ImageSelectionWidget(QtGui.QWidget):

    def __init__ (self, parent):
        super(ImageSelectionWidget, self).__init__(parent)
        self.main_widget = parent

        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)

        self.scan_btn = QtGui.QPushButton("Set Scan")
        self.scan_txtbox = QtGui.QLineEdit()
        self.scan_txtbox.setReadOnly(True)
        self.image_list = QtGui.QListWidget()
        self.current_image_lbl = QtGui.QLabel("Current Image:")
        self.current_image_txtbox = QtGui.QLineEdit()
        self.current_image_txtbox.setReadOnly(True)
        self.play_btn = QtGui.QPushButton("Play")

        self.layout.addWidget(self.scan_btn, 0, 0)
        self.layout.addWidget(self.scan_txtbox, 0, 1)
        self.layout.addWidget(self.image_list, 1, 0, 4, 2)
        self.layout.addWidget(self.current_image_lbl, 5, 0)
        self.layout.addWidget(self.current_image_txtbox, 5, 1)
        self.layout.addWidget(self.play_btn, 6, 0, 1, 2)

        self.scan_btn.clicked.connect(self.setScanDirectory)
        self.image_list.itemClicked.connect(self.loadImage)
        self.play_btn.clicked.connect(self.playScan)

    # --------------------------------------------------------------------------

    def setScanDirectory(self):
        self.scan_path = QtGui.QFileDialog.getExistingDirectory(self,
            "Open Scan Directory")

        if self.scan_path != "":
            for file in os.listdir(self.scan_path):
                if not file.endswith((".tif", ".tiff")):
                    return

            # Basename: self.scan_txtbox.setText(os.path.basename(self.scan_path))
            self.scan_txtbox.setText(self.scan_path)
            self.scan_images = sorted(os.listdir(self.scan_path))

            self.image_list.clear()
            self.image_list.addItems(self.scan_images)

    # --------------------------------------------------------------------------

    def loadImage(self, list_item):
        image_basename = list_item.text()
        image_path = f"{self.scan_path}/{image_basename}"
        image = np.rot90(tiff.imread(image_path), 1)

        self.main_widget.image_widget.displayImage(image)
        self.current_image_txtbox.setText(image_basename)

    # --------------------------------------------------------------------------

    def playScan(self):
        for i in range(self.image_list.count()):
            self.loadImage(self.image_list.item(i))
            QtGui.QApplication.processEvents()

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
