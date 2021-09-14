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

from rsMap3D.config.rsmap3dconfigparser import RSMap3DConfigParser
from rsMap3D.datasource.Sector33SpecDataSource import Sector33SpecDataSource
from rsMap3D.datasource.DetectorGeometryForXrayutilitiesReader import DetectorGeometryForXrayutilitiesReader as detReader
from rsMap3D.datasource.InstForXrayutilitiesReader import InstForXrayutilitiesReader as instrReader
from rsMap3D.gui.rsm3dcommonstrings import BINARY_OUTPUT
from rsMap3D.mappers.gridmapper import QGridMapper
from rsMap3D.mappers.output.vtigridwriter import VTIGridWriter
from rsMap3D.transforms.unitytransform3d import UnityTransform3D
from rsMap3D.utils.srange import srange
import vtk
from vtk.util import numpy_support as npSup
import xrayutilities as xu

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

        # For mapping pixels to HKL
        self.mapping_dialog = MappingParametersDialog()

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

class OptionsWidget(QtGui.QWidget):

    def __init__ (self, parent):
        super(OptionsWidget, self).__init__(parent)
        self.main_widget = parent

        self.setEnabled(False)

        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)

        self.map_hkl_btn = QtGui.QPushButton("Map Pixels to HKL")

        self.crosshair_chkbox = QtGui.QCheckBox("Crosshair")
        self.crosshair_colorbtn = pg.ColorButton()

        self.bkgrd_color_lbl = QtGui.QLabel("Bkgrd Color:")
        self.bkgrd_black_rbtn = QtGui.QRadioButton("Black")
        self.bkgrd_black_rbtn.setChecked(True)
        self.bkgrd_white_rbtn = QtGui.QRadioButton("White")
        self.bkgrd_color_group = QtGui.QButtonGroup()
        self.bkgrd_color_group.addButton(self.bkgrd_black_rbtn)
        self.bkgrd_color_group.addButton(self.bkgrd_white_rbtn)

        self.colormap_scale_lbl = QtGui.QLabel("Colormap Scale:")
        self.colormap_linear_rbtn = QtGui.QRadioButton("Linear")
        self.colormap_log_rbtn = QtGui.QRadioButton("Log")
        self.colormap_log_rbtn.setChecked(True)
        self.colormap_scale_group = QtGui.QButtonGroup()
        self.colormap_scale_group.addButton(self.colormap_linear_rbtn)
        self.colormap_scale_group.addButton(self.colormap_log_rbtn)

        self.layout.addWidget(self.map_hkl_btn, 0, 0, 1, 3)
        self.layout.addWidget(self.crosshair_chkbox, 1, 0)
        self.layout.addWidget(self.crosshair_colorbtn, 1, 1, 1, 2)
        self.layout.addWidget(self.bkgrd_color_lbl, 2, 0)
        self.layout.addWidget(self.bkgrd_black_rbtn, 2, 1)
        self.layout.addWidget(self.bkgrd_white_rbtn, 2, 2)
        self.layout.addWidget(self.colormap_scale_lbl, 3, 0)
        self.layout.addWidget(self.colormap_linear_rbtn, 3, 1)
        self.layout.addWidget(self.colormap_log_rbtn, 3, 2)

        self.map_hkl_btn.clicked.connect(self.showMappingDialog)
        self.crosshair_chkbox.stateChanged.connect(self.toggleCrosshair)
        self.crosshair_colorbtn .sigColorChanged.connect(self.changeCrosshairColor)
        self.bkgrd_color_group.buttonToggled.connect(self.toggleBackgroundColor)
        self.colormap_scale_group.buttonToggled.connect(self.toggleColormapScale)

    # --------------------------------------------------------------------------

    def showMappingDialog(self):
        self.main_widget.mapping_dialog.show()
        self.main_widget.mapping_dialog.finished.connect(self.mapPixelsToHKL)

    # --------------------------------------------------------------------------

    def mapPixelsToHKL(self):
        dialog = self.main_widget.mapping_dialog

        instr_config_path = dialog.instrument_config_name
        det_config_path = dialog.detector_config_name
        ub = np.fromstring(dialog.ub, sep=" ").reshape((3,3))
        mu = dialog.mu
        eta = dialog.eta
        chi = dialog.chi
        phi = dialog.phi
        nu = dialog.nu
        delta = dialog.delta
        energy = dialog.energy

        qx, qy, qz = MappingLogic.createLiveScanArea(instr_config_path,
            det_config_path, mu=mu, eta=eta, chi=chi, phi=phi, nu=nu,
            delta=delta, ub=ub, energy=energy)

        self.main_widget.analysis_widget.updateHKLMap(qx, qy, qz)

    # --------------------------------------------------------------------------

    def toggleCrosshair(self, state):
        if state == 2:
            self.main_widget.image_widget.v_line.setVisible(True)
            self.main_widget.image_widget.h_line.setVisible(True)
        else:
            self.main_widget.image_widget.v_line.setVisible(False)
            self.main_widget.image_widget.h_line.setVisible(False)

    # --------------------------------------------------------------------------

    def changeCrosshairColor(self):
        color = self.crosshair_colorbtn.color()

        self.main_widget.image_widget.v_line.setPen(pg.mkPen(color))
        self.main_widget.image_widget.h_line.setPen(pg.mkPen(color))

    # --------------------------------------------------------------------------

    def toggleBackgroundColor(self):
        btn = self.sender().checkedButton()

        if btn.text() == "Black":
            self.main_widget.image_widget.setBackground("default")
        else:
            self.main_widget.image_widget.setBackground("w")

    # --------------------------------------------------------------------------

    def toggleColormapScale(self):
        btn = self.sender().checkedButton()

        if btn.text() == "Log":
            self.main_widget.image_widget.colormap_scale = "log"
        else:
            self.main_widget.image_widget.colormap_scale = "linear"

        self.main_widget.image_widget.displayImage(self.main_widget.image_widget.image)

# ==============================================================================

class ImageWidget(pg.PlotWidget):

    def __init__ (self, parent):
        super(ImageWidget, self).__init__(parent)
        self.main_widget = parent

        # Image within image widget
        self.image_item = pg.ImageItem()
        self.addItem(self.image_item)

        # Larger y-values towards bottom
        self.invertY(True)

        self.view = self.getViewBox()
        self.scene_point = None
        self.colormap_scale = "log"

        # Crosshair
        self.v_line = pg.InfiniteLine(angle=90, movable=False)
        self.h_line = pg.InfiniteLine(angle=0, movable=False)
        self.v_line.setVisible(False)
        self.h_line.setVisible(False)
        self.addItem(self.v_line, ignoreBounds=True)
        self.addItem(self.h_line, ignoreBounds=True)

    # --------------------------------------------------------------------------

    def displayImage(self, image):
        self.image = image
        # Normalize image with logarithmic colormap
        colormap_max = np.amax(self.image)
        if self.colormap_scale == "log":
            norm = colors.LogNorm(vmax=colormap_max)
        else:
            norm = colors.Normalize(vmax=colormap_max)
        norm_image = norm(self.image)
        color_image = plt.cm.jet(norm_image)

        # Set image to image item
        self.image_item.setImage(color_image)

        self.view.scene().sigMouseMoved.connect(self.updateMouse)

        self.updateMouse()
        self.main_widget.analysis_widget.updateImageInfo(image)
        self.main_widget.analysis_widget.updateMaxInfo(image)

        if not self.main_widget.options_widget.isEnabled():
            self.main_widget.options_widget.setEnabled(True)

    # --------------------------------------------------------------------------

    def updateMouse(self, scene_point=None):
        if scene_point != None:
            self.scene_point = scene_point
        if self.scene_point != None:
            self.view_point = self.view.mapSceneToView(self.scene_point)

            # x and y values of mouse
            x, y = self.view_point.x(), self.view_point.y()
        else:
            return

        # Crosshair
        self.v_line.setPos(x)
        self.h_line.setPos(y)

        self.main_widget.analysis_widget.updateMouseInfo(self.image, x, y)

# ==============================================================================

class AnalysisWidget(pg.LayoutWidget):

    def __init__ (self, parent):
        super(AnalysisWidget, self).__init__(parent)
        self.main_widget = parent

        self.image_gbox = QtGui.QGroupBox("Image")
        self.mouse_gbox = QtGui.QGroupBox("Mouse")
        self.max_gbox = QtGui.QGroupBox("Max")

        self.addWidget(self.image_gbox, row=0, col=0)
        self.addWidget(self.mouse_gbox, row=0, col=1)
        self.addWidget(self.max_gbox, row=0, col=2)

        self.image_layout = QtGui.QGridLayout()
        self.mouse_layout = QtGui.QGridLayout()
        self.max_layout = QtGui.QGridLayout()

        self.image_gbox.setLayout(self.image_layout)
        self.mouse_gbox.setLayout(self.mouse_layout)
        self.max_gbox.setLayout(self.max_layout)

        self.image_pixel_count_x_lbl = QtGui.QLabel("Pixel Count (x):")
        self.image_pixel_count_x_txtbox = QtGui.QLineEdit()
        self.image_pixel_count_x_txtbox.setReadOnly(True)
        self.image_pixel_count_y_lbl = QtGui.QLabel("Pixel Count (y):")
        self.image_pixel_count_y_txtbox = QtGui.QLineEdit()
        self.image_pixel_count_y_txtbox.setReadOnly(True)

        self.mouse_x_lbl = QtGui.QLabel("x Pos:")
        self.mouse_x_txtbox = QtGui.QLineEdit()
        self.mouse_x_txtbox.setReadOnly(True)
        self.mouse_y_lbl = QtGui.QLabel("y Pos:")
        self.mouse_y_txtbox = QtGui.QLineEdit()
        self.mouse_y_txtbox.setReadOnly(True)
        self.mouse_intensity_lbl = QtGui.QLabel("Intensity:")
        self.mouse_intensity_txtbox = QtGui.QLineEdit()
        self.mouse_intensity_txtbox.setReadOnly(True)
        self.mouse_h_lbl = QtGui.QLabel("H:")
        self.mouse_h_txtbox = QtGui.QLineEdit()
        self.mouse_h_txtbox.setReadOnly(True)
        self.mouse_k_lbl = QtGui.QLabel("K:")
        self.mouse_k_txtbox = QtGui.QLineEdit()
        self.mouse_k_txtbox.setReadOnly(True)
        self.mouse_l_lbl = QtGui.QLabel("L:")
        self.mouse_l_txtbox = QtGui.QLineEdit()
        self.mouse_l_txtbox.setReadOnly(True)

        self.max_x_lbl = QtGui.QLabel("x Pos:")
        self.max_x_txtbox = QtGui.QLineEdit()
        self.max_x_txtbox.setReadOnly(True)
        self.max_y_lbl = QtGui.QLabel("y Pos:")
        self.max_y_txtbox = QtGui.QLineEdit()
        self.max_y_txtbox.setReadOnly(True)
        self.max_intensity_lbl = QtGui.QLabel("Intensity:")
        self.max_intensity_txtbox = QtGui.QLineEdit()
        self.max_intensity_txtbox.setReadOnly(True)
        self.max_h_lbl = QtGui.QLabel("H:")
        self.max_h_txtbox = QtGui.QLineEdit()
        self.max_h_txtbox.setReadOnly(True)
        self.max_k_lbl = QtGui.QLabel("K:")
        self.max_k_txtbox = QtGui.QLineEdit()
        self.max_k_txtbox.setReadOnly(True)
        self.max_l_lbl = QtGui.QLabel("L:")
        self.max_l_txtbox = QtGui.QLineEdit()
        self.max_l_txtbox.setReadOnly(True)

        self.image_layout.addWidget(self.image_pixel_count_x_lbl, 0, 0)
        self.image_layout.addWidget(self.image_pixel_count_x_txtbox, 0, 1)
        self.image_layout.addWidget(self.image_pixel_count_y_lbl, 1, 0)
        self.image_layout.addWidget(self.image_pixel_count_y_txtbox, 1, 1)

        self.mouse_layout.addWidget(self.mouse_x_lbl, 0, 0)
        self.mouse_layout.addWidget(self.mouse_x_txtbox, 0, 1)
        self.mouse_layout.addWidget(self.mouse_y_lbl, 1, 0)
        self.mouse_layout.addWidget(self.mouse_y_txtbox, 1, 1)
        self.mouse_layout.addWidget(self.mouse_intensity_lbl, 2, 0)
        self.mouse_layout.addWidget(self.mouse_intensity_txtbox, 2, 1)
        self.mouse_layout.addWidget(self.mouse_h_lbl, 3, 0)
        self.mouse_layout.addWidget(self.mouse_h_txtbox, 3, 1)
        self.mouse_layout.addWidget(self.mouse_k_lbl, 4, 0)
        self.mouse_layout.addWidget(self.mouse_k_txtbox, 4, 1)
        self.mouse_layout.addWidget(self.mouse_l_lbl, 5, 0)
        self.mouse_layout.addWidget(self.mouse_l_txtbox, 5, 1)

        self.max_layout.addWidget(self.max_x_lbl, 0, 0)
        self.max_layout.addWidget(self.max_x_txtbox, 0, 1)
        self.max_layout.addWidget(self.max_y_lbl, 1, 0)
        self.max_layout.addWidget(self.max_y_txtbox, 1, 1)
        self.max_layout.addWidget(self.max_intensity_lbl, 2, 0)
        self.max_layout.addWidget(self.max_intensity_txtbox, 2, 1)
        self.max_layout.addWidget(self.max_h_lbl, 3, 0)
        self.max_layout.addWidget(self.max_h_txtbox, 3, 1)
        self.max_layout.addWidget(self.max_k_lbl, 4, 0)
        self.max_layout.addWidget(self.max_k_txtbox, 4, 1)
        self.max_layout.addWidget(self.max_l_lbl, 5, 0)
        self.max_layout.addWidget(self.max_l_txtbox, 5, 1)

        # For mapping to HKL
        self.mapped = False

    # --------------------------------------------------------------------------

    def updateImageInfo(self, image):
        self.image_pixel_count_x_txtbox.setText(str(image.shape[0]))
        self.image_pixel_count_y_txtbox.setText(str(image.shape[1]))

    # --------------------------------------------------------------------------

    def updateMouseInfo(self, image, x, y):
        self.mouse_x_txtbox.setText(str(x))
        self.mouse_y_txtbox.setText(str(y))

        if image.shape[0] >= x >= 0 and image.shape[1] >= y >= 0:
            self.mouse_intensity_txtbox.setText(str(image[int(x), int(y)]))

            if self.mapped == True:
                self.mouse_h_txtbox.setText(str(self.qx[int(x)][int(y)]))
                self.mouse_k_txtbox.setText(str(self.qy[int(x)][int(y)]))
                self.mouse_l_txtbox.setText(str(self.qz[int(x)][int(y)]))
        else:
            self.mouse_intensity_txtbox.setText("")
            self.mouse_h_txtbox.setText("")
            self.mouse_k_txtbox.setText("")
            self.mouse_l_txtbox.setText("")

    # --------------------------------------------------------------------------

    def updateMaxInfo(self, image):
        max = np.amax(image)
        x, y = np.unravel_index(image.argmax(), image.shape)
        self.max_x_txtbox.setText(str(x))
        self.max_y_txtbox.setText(str(y))
        self.max_intensity_txtbox.setText(str(max))

        if self.mapped == True:
            self.max_h_txtbox.setText(str(self.qx[int(x)][int(y)]))
            self.max_k_txtbox.setText(str(self.qy[int(x)][int(y)]))
            self.max_l_txtbox.setText(str(self.qz[int(x)][int(y)]))

    # --------------------------------------------------------------------------

    def updateHKLMap(self, qx, qy, qz):
        self.mapped = True
        self.qx, self.qy, self.qz = qx, qy, qz
        self.main_widget.image_widget.displayImage(self.main_widget.image_widget.image)

# ==============================================================================

class MappingParametersDialog(QtGui.QDialog):

    def __init__ (self):
        super().__init__()

        self.setWindowModality(QtCore.Qt.ApplicationModal)

        self.detector_config_name = ""
        self.instrument_config_name = ""
        self.ub_matrix = []
        self.mu = 0.0
        self.eta = 0.0
        self.chi = 0.0
        self.phi = 0.0
        self.nu = 0.0
        self.delta = 0.0
        self.energy = 0

        # Create widgets
        self.detector_lbl = QtGui.QLabel("Det. Config:")
        self.detector_txtbox = QtGui.QLineEdit()
        self.detector_txtbox.setReadOnly(True)
        self.detector_btn = QtGui.QPushButton("Browse")
        self.instrument_lbl = QtGui.QLabel("Instr. Config:")
        self.instrument_txtbox = QtGui.QLineEdit()
        self.instrument_txtbox.setReadOnly(True)
        self.instrument_btn = QtGui.QPushButton("Browse")
        self.ub_matrix_lbl = QtGui.QLabel("UB Matrix:")
        self.ub_matrix_txtedit = QtGui.QPlainTextEdit()
        self.mu_lbl = QtGui.QLabel("Mu (deg):")
        self.mu_sbox = QtGui.QDoubleSpinBox()
        self.mu_sbox.setMaximum(360.0)
        self.mu_sbox.setMinimum(-360.0)
        self.eta_lbl = QtGui.QLabel("Eta (deg):")
        self.eta_sbox = QtGui.QDoubleSpinBox()
        self.eta_sbox.setMaximum(360.0)
        self.eta_sbox.setMinimum(-360.0)
        self.chi_lbl = QtGui.QLabel("Chi (deg):")
        self.chi_sbox = QtGui.QDoubleSpinBox()
        self.chi_sbox.setMaximum(360.0)
        self.chi_sbox.setMinimum(-360.0)
        self.phi_lbl = QtGui.QLabel("Phi (deg):")
        self.phi_sbox = QtGui.QDoubleSpinBox()
        self.phi_sbox.setMaximum(360.0)
        self.phi_sbox.setMinimum(-360.0)
        self.nu_lbl = QtGui.QLabel("Nu (deg):")
        self.nu_sbox = QtGui.QDoubleSpinBox()
        self.nu_sbox.setMaximum(360.0)
        self.nu_sbox.setMinimum(-360.0)
        self.delta_lbl = QtGui.QLabel("Delta (deg):")
        self.delta_sbox = QtGui.QDoubleSpinBox()
        self.delta_sbox.setMaximum(360.0)
        self.delta_sbox.setMinimum(-360.0)
        self.energy_lbl = QtGui.QLabel("Energy:")
        self.energy_sbox = QtGui.QSpinBox()
        self.energy_sbox.setMaximum(100000)
        self.ok_btn = QtGui.QPushButton("OK")

        # Create layout
        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)

        # Add widgets to layout
        self.layout.addWidget(self.detector_lbl, 0, 0)
        self.layout.addWidget(self.detector_txtbox, 0, 1)
        self.layout.addWidget(self.detector_btn, 0, 2)
        self.layout.addWidget(self.instrument_lbl, 1, 0)
        self.layout.addWidget(self.instrument_txtbox, 1, 1)
        self.layout.addWidget(self.instrument_btn, 1, 2)
        self.layout.addWidget(self.ub_matrix_lbl, 2, 0)
        self.layout.addWidget(self.ub_matrix_txtedit, 2, 1, 1, 2)
        self.layout.addWidget(self.mu_lbl, 3, 0)
        self.layout.addWidget(self.mu_sbox, 3, 2)
        self.layout.addWidget(self.eta_lbl, 4, 0)
        self.layout.addWidget(self.eta_sbox, 4, 2)
        self.layout.addWidget(self.chi_lbl, 5, 0)
        self.layout.addWidget(self.chi_sbox, 5, 2)
        self.layout.addWidget(self.phi_lbl, 6, 0)
        self.layout.addWidget(self.phi_sbox, 6, 2)
        self.layout.addWidget(self.nu_lbl, 7, 0)
        self.layout.addWidget(self.nu_sbox, 7, 2)
        self.layout.addWidget(self.delta_lbl, 8, 0)
        self.layout.addWidget(self.delta_sbox, 8, 2)
        self.layout.addWidget(self.energy_lbl, 9, 0)
        self.layout.addWidget(self.energy_sbox, 9, 2)
        self.layout.addWidget(self.ok_btn, 10, 2)

        # Connect widgets to functions
        self.detector_btn.clicked.connect(self.selectDetectorConfigFile)
        self.instrument_btn.clicked.connect(self.selectInstrumentConfigFile)
        self.ok_btn.clicked.connect(self.acceptDialog)

    # --------------------------------------------------------------------------

    def selectDetectorConfigFile(self):

        """
        Allows user to select a detector configuration .xml file.
        """

        detector = QtGui.QFileDialog.getOpenFileName(self, "", "", "xml Files (*.xml)")
        self.detector_txtbox.setText(detector[0])

    # --------------------------------------------------------------------------

    def selectInstrumentConfigFile(self):

        """
        Allows user to select an instrument configuration .xml file.
        """

        instrument = QtGui.QFileDialog.getOpenFileName(self, "", "", "xml Files (*.xml)")
        self.instrument_txtbox.setText(instrument[0])

    # --------------------------------------------------------------------------

    def acceptDialog(self):

        """
        Sets class variables to values in dialog and closes the dialog window.
        """

        self.detector_config_name = self.detector_txtbox.text()
        self.instrument_config_name = self.instrument_txtbox.text()
        self.ub = self.ub_matrix_txtedit.toPlainText()
        self.mu = self.mu_sbox.value()
        self.eta = self.eta_sbox.value()
        self.chi = self.chi_sbox.value()
        self.phi = self.phi_sbox.value()
        self.nu = self.nu_sbox.value()
        self.delta = self.delta_sbox.value()
        self.energy = self.energy_sbox.value()
        self.close()

# ==============================================================================

class MappingLogic():

    def createLiveScanArea(instrument_config_name, detector_config_name, mu, eta,
        chi, phi, nu, delta, ub, energy):

        d_reader = detReader(detector_config_name)
        i_reader = instrReader(instrument_config_name)

        sample_circle_dir = i_reader.getSampleCircleDirections()
        det_circle_dir = i_reader.getDetectorCircleDirections()
        primary_beam_dir = i_reader.getPrimaryBeamDirection()

        q_conv = xu.experiment.QConversion(sample_circle_dir, det_circle_dir, primary_beam_dir)

        inplane_ref_dir = i_reader.getInplaneReferenceDirection()
        sample_norm_dir = i_reader.getSampleSurfaceNormalDirection()

        hxrd = xu.HXRD(inplane_ref_dir, sample_norm_dir, en=energy, qconv=q_conv)

        detector = d_reader.getDetectors()[0]
        pixel_dir_1 = d_reader.getPixelDirection1(detector)
        pixel_dir_2 = d_reader.getPixelDirection2(detector)
        c_ch_1 = d_reader.getCenterChannelPixel(detector)[0]
        c_ch_2 = d_reader.getCenterChannelPixel(detector)[1]
        n_ch_1 = d_reader.getNpixels(detector)[0]
        n_ch_2 = d_reader.getNpixels(detector)[1]
        pixel_width_1 = d_reader.getSize(detector)[0] / d_reader.getNpixels(detector)[0]
        pixel_width_2 = d_reader.getSize(detector)[1] / d_reader.getNpixels(detector)[1]
        distance = d_reader.getDistance(detector)
        roi = [0, n_ch_1, 0, n_ch_2]

        hxrd.Ang2Q.init_area(pixel_dir_1, pixel_dir_2, cch1=c_ch_1, cch2=c_ch_2,
            Nch1=n_ch_1, Nch2=n_ch_2, pwidth1=pixel_width_1, pwidth2=pixel_width_2,
            distance=distance, roi=roi)

        qx,qy,qz = hxrd.Ang2Q.area(mu,eta,chi,phi,nu,delta,UB=ub)

        return qx, qy, qz
