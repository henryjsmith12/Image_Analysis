"""
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

# ==============================================================================

import matplotlib.colors as colors
import matplotlib.pyplot as plt
import numpy as np
import os
import pyqtgraph as pg
from pyqtgraph.dockarea import *
from pyqtgraph.Qt import QtGui, QtCore
from rsMap3D.datasource.DetectorGeometryForXrayutilitiesReader import DetectorGeometryForXrayutilitiesReader as detReader
from rsMap3D.datasource.InstForXrayutilitiesReader import InstForXrayutilitiesReader as instrReader
from spec2nexus import spec
import tifffile as tiff
import xrayutilities as xu

# ==============================================================================

class MappingWidget(QtGui.QWidget):
    """
    Revamped LivePlottingWidget. Allows users to:
    - View scan images
    - Create cubic reciprocal space maps (RSM's) using .spec and config files
    """

    def __init__ (self):
        super().__init__()

        # Main widgets
        self.scan_control_widget = ScanControlWidget(self)
        self.image_widget = ImageWidget(self)
        self.options_widget = OptionsWidget(self)
        self.options_widget.setEnabled(False)
        self.analysis_widget = AnalysisWidget(self)
        self.analysis_widget.setEnabled(False)
        self.rsm_dialog = RSMDialog()

        # Main Widget Docks
        self.dock_area = DockArea()
        self.scan_control_dock = Dock("Scan Control", size=(100, 300), hideTitle=True)
        self.options_dock = Dock("Options", size=(100, 100), hideTitle=True)
        self.analysis_dock = Dock("Analysis", size=(300, 100), hideTitle=True)
        self.image_dock = Dock("Image", size=(300, 300), hideTitle=True)
        self.scan_control_dock.addWidget(self.scan_control_widget)
        self.options_dock.addWidget(self.options_widget)
        self.analysis_dock.addWidget(self.analysis_widget)
        self.image_dock.addWidget(self.image_widget)
        self.dock_area.addDock(self.scan_control_dock)
        self.dock_area.addDock(self.options_dock, "bottom", self.scan_control_dock)
        self.dock_area.addDock(self.analysis_dock, "right", self.options_dock)
        self.dock_area.addDock(self.image_dock, "top", self.analysis_dock)
        self.dock_area.moveDock(self.image_dock, "right", self.scan_control_dock)

        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.dock_area)

# ==============================================================================

class ScanControlWidget(QtGui.QWidget):
    """
    Controls current scan directory. Allows user to:
    - select a specific scan image
    - play through all images in scan
    - create a reciprocal space map
    """
    
    def __init__ (self, parent):
        super().__init__()

        # MappingWidget object
        self.parent = parent

        # Parameters to create a RSM
        self.rsm_params = {
            "Chi": 0, 
            "Delta": 0, 
            "Eta": 0, 
            "Mu": 0, 
            "Nu": 0, 
            "Phi": 0,
            "Energy": 0,
            "UB_Matrix": None
        }

        # Reciprocal Space Map to be set later
        self.rsm = None

        # Absolute path for current image in view
        self.current_image_path = ""

        # Widget contents
        self.select_scan_btn = QtGui.QPushButton("Select Scan")
        self.select_scan_txt = QtGui.QLineEdit()
        self.select_scan_txt.setReadOnly(True)
        self.scan_images_list_widget = QtGui.QListWidget()
        self.current_image_lbl = QtGui.QLabel("Current Image:")
        self.current_image_txt = QtGui.QLineEdit()
        self.current_image_txt.setReadOnly(True)
        self.play_scan_btn = QtGui.QPushButton("Play Scan")
        self.play_scan_btn.setEnabled(False)
        self.rsm_btn = QtGui.QPushButton("Create Reciprocal Space Map")
        self.rsm_btn.setEnabled(False)

        # Layout
        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.select_scan_btn, 0, 0)
        self.layout.addWidget(self.select_scan_txt, 0, 1)
        self.layout.addWidget(self.scan_images_list_widget, 1, 0, 4, 2)
        self.layout.addWidget(self.current_image_lbl, 5, 0)
        self.layout.addWidget(self.current_image_txt, 5, 1)
        self.layout.addWidget(self.play_scan_btn, 6, 0, 1, 2)
        self.layout.addWidget(self.rsm_btn, 7, 0, 1, 2)

        # Signals
        self.select_scan_btn.clicked.connect(self.selectScan)
        self.scan_images_list_widget.itemClicked.connect(self.selectImage)
        self.play_scan_btn.clicked.connect(self.playScan)
        self.rsm_btn.clicked.connect(self.openRSMDialog)

    # --------------------------------------------------------------------------

    def selectScan(self):
        """
        - Sets scan to view
        - Enables other widgets after set
        """

        self.scan_path = QtGui.QFileDialog.getExistingDirectory(self, \
            "Select Scan Directory")
        
        if self.scan_path != "":
            for file in os.listdir(self.scan_path):
                if not file.endswith((".tif", ".tiff")):
                    error_mbx = QtGui.QMessageBox()
                    error_mbx.setText("Directory must include only .tif/.tiff images.")
                    error_mbx.setStandardButtons(QtGui.QMessageBox.Ok)
                    error_mbx.exec_()
                    return

            self.scan_number = int(os.path.basename(self.scan_path)[1:])
            self.select_scan_txt.setText(self.scan_path)
            self.scan_images = sorted(os.listdir(self.scan_path))

            self.scan_images_list_widget.clear()
            self.scan_images_list_widget.addItems(self.scan_images)

            self.play_scan_btn.setEnabled(True)
            self.rsm_btn.setEnabled(True)
            self.parent.options_widget.setEnabled(True)
            self.parent.analysis_widget.setEnabled(True)

    # --------------------------------------------------------------------------

    def selectImage(self, image_list_item):
        """
        - Calls ImageWidget function to display currently selected image
        - Creates new RSM
        - Calls AnalysisWidget function to display new max info
        """

        current_image_basename = image_list_item.text()
        self.current_image_path = f"{self.scan_path}/{current_image_basename}"
        self.current_image_txt.setText(current_image_basename)
        self.current_image_index = self.scan_images.index(current_image_basename)

        # Rotated to match dimensions of RSM
        image = np.rot90(tiff.imread(self.current_image_path), 1)
        self.parent.image_widget.displayImage(image)
        self.createRSM()
        self.parent.analysis_widget.updateMaxInfo()

    # --------------------------------------------------------------------------

    def playScan(self):
        """
        Loops through scan images
        """

        for i in range(self.scan_images_list_widget.count()):
            self.selectImage(self.scan_images_list_widget.item(i))
            # Refreshes GUI; inefficient
            QtGui.QApplication.processEvents()

    # --------------------------------------------------------------------------

    def openRSMDialog(self):
        """
        Opens dialog to set .spec and config files
        """

        self.parent.rsm_dialog.show()
        self.parent.rsm_dialog.closed.connect(self.createRSM)

    # --------------------------------------------------------------------------

    def createRSM(self):
        """
        Creates reciprocal space map from given information
        """
        # .spec/config dialog
        rsm_dialog = self.parent.rsm_dialog

        # Checks if image and all necessary files are set
        if rsm_dialog.files_set and self.current_image_path != "":

            # Files from dialog
            self.spec_path = rsm_dialog.spec_path
            self.detector_path = rsm_dialog.detector_path
            self.instrument_path = rsm_dialog.instrument_path

            # .spec file object
            spec_file = spec.SpecDataFile(self.spec_path)

            # Specific scan
            scan = spec_file.getScan(self.scan_number)

            # Specific point (from current image)
            point = int(self.current_image_index)

            # Retrieves motor angles from .spec file
            for param in self.rsm_params.keys():
                if param in scan.positioner:
                    self.rsm_params[param] = scan.positioner[param]

            # UB Matrix
            ub_list = scan.G["G3"].split(" ")
            self.rsm_params["UB_Matrix"] = np.reshape(ub_list, (3, 3)).astype(np.float64)

            # Energy value (originally in keV, converted to eV)
            for line in scan.raw.split("\n"):
                if line.startswith("#U"):
                    self.rsm_params["Energy"] = float(line.split(" ")[1]) * 1000
                    break
            
            # Retrieves value of any point-dependent parameter
            for i in range(len(scan.L)):
                label = scan.L[i]
                if label in self.rsm_params.keys():
                    self.rsm_params[label] = scan.data[label][point]
            try:
                self.rsm = MappingLogic.createLiveScanArea(
                    self.instrument_path,
                    self.detector_path, 
                    mu=self.rsm_params["Mu"], 
                    eta=self.rsm_params["Eta"], 
                    chi=self.rsm_params["Chi"], 
                    phi=self.rsm_params["Phi"], 
                    nu=self.rsm_params["Nu"],
                    delta=self.rsm_params["Delta"], 
                    ub=self.rsm_params["UB_Matrix"], 
                    energy=self.rsm_params["Energy"]
                )

                self.parent.analysis_widget.updateRSMParameters()
                self.parent.analysis_widget.updateMaxInfo()
                self.parent.image_widget.updateMouse()

            except Exception as ex:
                error_mbx = QtGui.QMessageBox()
                error_mbx.setText(str(ex))
                error_mbx.setStandardButtons(QtGui.QMessageBox.Ok)
                error_mbx.exec_()

# ==============================================================================

class RSMDialog(QtGui.QWidget):
    """
    Dialog to select:
    - .spec data file
    - Instrument configuration file
    - Detector configuration file
    """
    
    closed = QtCore.pyqtSignal()

    def __init__ (self):
        super().__init__()

        self.spec_path = ""
        self.detector_path = ""
        self.instrument_path = ""

        self.files_set = False

        self.spec_lbl = QtGui.QLabel(".spec File:")
        self.spec_txt = QtGui.QLineEdit()
        self.spec_txt.setReadOnly(True)
        self.spec_btn = QtGui.QPushButton("Browse")
        self.detector_lbl = QtGui.QLabel("Det. Config:")
        self.detector_txt = QtGui.QLineEdit()
        self.detector_txt.setReadOnly(True)
        self.detector_btn = QtGui.QPushButton("Browse")
        self.instrument_lbl = QtGui.QLabel("Instr. Config:")
        self.instrument_txt = QtGui.QLineEdit()
        self.instrument_txt.setReadOnly(True)
        self.instrument_btn = QtGui.QPushButton("Browse")
        self.ok_btn = QtGui.QPushButton("OK")
        self.ok_btn.setDefault(True)

        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.spec_lbl, 0, 0)
        self.layout.addWidget(self.spec_txt, 0, 1)
        self.layout.addWidget(self.spec_btn, 0, 2)
        self.layout.addWidget(self.detector_lbl, 1, 0)
        self.layout.addWidget(self.detector_txt, 1, 1)
        self.layout.addWidget(self.detector_btn, 1, 2)
        self.layout.addWidget(self.instrument_lbl, 2, 0)
        self.layout.addWidget(self.instrument_txt, 2, 1)
        self.layout.addWidget(self.instrument_btn, 2, 2)
        self.layout.addWidget(self.ok_btn, 3, 2)

        # Signals
        self.spec_btn.clicked.connect(self.selectSpecFile)
        self.detector_btn.clicked.connect(self.selectDetectorConfigFile)
        self.instrument_btn.clicked.connect(self.selectInstrumentConfigFile)
        self.ok_btn.clicked.connect(self.acceptDialog)

    # --------------------------------------------------------------------------

    def selectSpecFile(self):
        spec = QtGui.QFileDialog.getOpenFileName(self, "", "", "spec Files (*.spec)")
        self.spec_txt.setText(spec[0])
        self.spec_path = spec[0]

    # --------------------------------------------------------------------------

    def selectDetectorConfigFile(self):
        detector = QtGui.QFileDialog.getOpenFileName(self, "", "", "xml Files (*.xml)")
        self.detector_txt.setText(detector[0])
        self.detector_path = detector[0]

    # --------------------------------------------------------------------------

    def selectInstrumentConfigFile(self):
        instrument = QtGui.QFileDialog.getOpenFileName(self, "", "", "xml Files (*.xml)")
        self.instrument_txt.setText(instrument[0])
        self.instrument_path = instrument[0]

    # --------------------------------------------------------------------------

    def acceptDialog(self):
        if "" not in [self.spec_path, self.detector_path, self.instrument_path]:
            self.files_set = True
        else:
            self.files_set = False
        self.closed.emit()
        self.close()

# ==============================================================================

class OptionsWidget(QtGui.QWidget):
    
    def __init__ (self, parent):
        super().__init__()

        self.parent = parent

        self.cmap_list = [
            "jet",
            "turbo",
            "plasma",
            "hot",
            "cool",
            "gray",
            "hsv",
            "nipy_spectral",
            "prism",
            "spring",
            "summer",
            "autumn"
        ]

        self.cmap_lbl = QtGui.QLabel("Colormap:")
        self.cmap_cbx = QtGui.QComboBox()
        self.cmap_cbx.addItems(self.cmap_list)
        self.cmap_scale_lbl = QtGui.QLabel("Cmap Scale:")
        self.cmap_scale_cbx = QtGui.QComboBox()
        self.cmap_scale_cbx.addItems(["Logarithmic", "Linear"])

        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.cmap_lbl, 0, 0)
        self.layout.addWidget(self.cmap_cbx, 0, 1)
        self.layout.addWidget(self.cmap_scale_lbl, 1, 0)
        self.layout.addWidget(self.cmap_scale_cbx, 1, 1)

        self.cmap_cbx.currentIndexChanged.connect(
            lambda x: self.parent.image_widget.displayImage(
                self.parent.image_widget.image
            )
        )

        self.cmap_scale_cbx.currentIndexChanged.connect(
            lambda x: self.parent.image_widget.displayImage(
                self.parent.image_widget.image
            )
        )

# ==============================================================================

class AnalysisWidget(QtGui.QWidget):

    def __init__ (self, parent):
        super().__init__()

        self.parent = parent

        self.mouse_gbx = QtGui.QGroupBox("Mouse Location")
        self.mouse_lbl_list = ["x Pos:", "y Pos:", "Intensity:", "H:", "K:", "L:"]
        self.mouse_lbls = [QtGui.QLabel(i) for i in self.mouse_lbl_list]
        self.mouse_txts = [QtGui.QLineEdit() for i in self.mouse_lbl_list]
        self.mouse_layout = QtGui.QGridLayout()
        self.mouse_gbx.setLayout(self.mouse_layout)
        for lbl, txt, i in zip(self.mouse_lbls, self.mouse_txts, range(len(self.mouse_lbls))):
            self.mouse_layout.addWidget(lbl, i, 0)
            self.mouse_layout.addWidget(txt, i, 1)
            txt.setReadOnly(True)

        self.max_gbx = QtGui.QGroupBox("Max Intensity")
        self.max_lbl_list = ["x Pos:", "y Pos:", "Intensity:", "H:", "K:", "L:"]
        self.max_lbls = [QtGui.QLabel(i) for i in self.max_lbl_list]
        self.max_txts = [QtGui.QLineEdit() for i in self.max_lbl_list]
        self.max_layout = QtGui.QGridLayout()
        self.max_gbx.setLayout(self.max_layout)
        for lbl, txt, i in zip(self.max_lbls, self.max_txts, range(len(self.max_lbls))):
            self.max_layout.addWidget(lbl, i, 0)
            self.max_layout.addWidget(txt, i, 1)
            txt.setReadOnly(True)

        self.rsm_params_gbx = QtGui.QGroupBox("RSM Parameters")
        self.rsm_params_lbl_list = [
            "Chi (deg):", "Delta (deg):", "Eta (deg):", "Mu (deg):", "Nu (deg):", "Phi (deg):", "Energy (eV):"
        ]
        self.rsm_params_lbls = [QtGui.QLabel(i) for i in self.rsm_params_lbl_list]
        self.rsm_params_txts = [QtGui.QLineEdit() for i in self.rsm_params_lbl_list]
        self.rsm_params_layout = QtGui.QGridLayout()
        self.rsm_params_gbx.setLayout(self.rsm_params_layout)
        for lbl, txt, i in zip(self.rsm_params_lbls, self.rsm_params_txts, range(len(self.rsm_params_lbls))):
            self.rsm_params_layout.addWidget(lbl, i, 0)
            self.rsm_params_layout.addWidget(txt, i, 1)
            txt.setReadOnly(True)

        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.mouse_gbx, 0, 0)
        self.layout.addWidget(self.max_gbx, 0, 1)
        self.layout.addWidget(self.rsm_params_gbx, 0, 2)

    # --------------------------------------------------------------------------

    def updateMouseInfo(self, point):
        image = self.parent.image_widget.image
        x, y = point
        
        self.mouse_txts[0].setText(str(x))
        self.mouse_txts[1].setText(str(y))
        
        if (0 <= x < image.shape[0]) and (0 <= y < image.shape[1]):
            intensity = image[int(x)][int(y)]
            self.mouse_txts[2].setText(str(intensity))
            rsm = self.parent.scan_control_widget.rsm
            if rsm is not None:
                self.mouse_txts[3].setText(str(rsm[0][int(x)][int(y)]))
                self.mouse_txts[4].setText(str(rsm[1][int(x)][int(y)]))
                self.mouse_txts[5].setText(str(rsm[2][int(x)][int(y)]))
        else:
            self.mouse_txts[2].setText("") 
            self.mouse_txts[3].setText("")
            self.mouse_txts[4].setText("")
            self.mouse_txts[5].setText("")

    # --------------------------------------------------------------------------

    def updateMaxInfo(self):
        image = self.parent.image_widget.image
        intensity = np.amax(image)
        x, y = np.unravel_index(image.argmax(), image.shape)
        
        self.max_txts[0].setText(str(x))
        self.max_txts[1].setText(str(y))
        self.max_txts[2].setText(str(intensity))

        rsm = self.parent.scan_control_widget.rsm
        if rsm is not None:
            self.max_txts[3].setText(str(rsm[0][int(x)][int(y)]))
            self.max_txts[4].setText(str(rsm[1][int(x)][int(y)]))
            self.max_txts[5].setText(str(rsm[2][int(x)][int(y)]))
        else:
            self.max_txts[3].setText("")
            self.max_txts[4].setText("")
            self.max_txts[5].setText("")

    # --------------------------------------------------------------------------

    def updateRSMParameters(self):
        rsm_params = self.parent.scan_control_widget.rsm_params
        for i in range(len(self.rsm_params_txts)):
            param = self.rsm_params_lbl_list[i].split(" ")[0]
            self.rsm_params_txts[i].setText(str(rsm_params[param]))

# ==============================================================================

class ImageWidget(pg.PlotWidget):
    
    def __init__ (self, parent):
        super(ImageWidget, self).__init__(parent)
        self.parent = parent

        # Image within image widget
        self.image = None
        self.image_item = pg.ImageItem()
        self.addItem(self.image_item)

        # Larger y-values towards bottom
        self.invertY(True)

        self.view = self.getViewBox()

        self.view.scene().sigMouseMoved.connect(self.updateMouse)

    # --------------------------------------------------------------------------

    def displayImage(self, image):
        self.image = image
        colormap_max = np.amax(self.image)
        norm = self.setColormapScale(colormap_max)
        norm_image = norm(self.image)
        color_image = self.setColormap(norm_image)

        self.image_item.setImage(color_image)

    # --------------------------------------------------------------------------

    def setColormap(self, image):
        cmap = self.parent.options_widget.cmap_cbx.currentText()

        if cmap == "jet":
            color_image = plt.cm.jet(image)
        elif cmap == "turbo":
            color_image = plt.cm.turbo(image)
        elif cmap == "plasma":
            color_image = plt.cm.plasma(image)
        elif cmap == "hot":
            color_image = plt.cm.hot(image)
        elif cmap == "cool":
            color_image = plt.cm.cool(image)
        elif cmap == "gray":
            color_image = plt.cm.gray(image)
        elif cmap == "hsv":
            color_image = plt.cm.hsv(image)
        elif cmap == "nipy_spectral":
            color_image = plt.cm.nipy_spectral(image)
        elif cmap == "prism":
            color_image = plt.cm.prism(image)
        elif cmap == "spring":
            color_image = plt.cm.spring(image)
        elif cmap == "summer":
            color_image = plt.cm.summer(image)
        elif cmap == "autumn":
            color_image = plt.cm.autumn(image)

        return color_image

    # --------------------------------------------------------------------------

    def setColormapScale(self, cmap_max):
        cmap_scale = self.parent.options_widget.cmap_scale_cbx.currentText()
        scale = None

        if cmap_scale == "Logarithmic":
            scale = colors.LogNorm(vmax=cmap_max)
        else:
            scale = colors.Normalize(vmax=cmap_max)

        return scale

    # --------------------------------------------------------------------------

    def updateMouse(self, scene_point=None): 
        if self.image is not None:
            if scene_point != None:
                self.scene_point = scene_point
            if self.scene_point != None:
                self.view_point = self.view.mapSceneToView(self.scene_point)

                # x and y values of mouse
                x, y = self.view_point.x(), self.view_point.y()
            else:
                return

            self.parent.analysis_widget.updateMouseInfo((x, y))

# ==============================================================================

class MappingLogic:

    def createLiveScanArea(instrument_config_name, detector_config_name, mu, eta, \
        chi, phi, nu, delta, ub, energy):

        """
        Creates a scan area to map pixels to reciprocal space coordinates
        """

        d_reader = detReader(detector_config_name) # Detector reader
        i_reader = instrReader(instrument_config_name) # Instrument reader

        # x+/-, y+/-, z+/-
        sample_circle_dir = i_reader.getSampleCircleDirections()
        det_circle_dir = i_reader.getDetectorCircleDirections()
        primary_beam_dir = i_reader.getPrimaryBeamDirection()

        """
        Object for the conversion of angular coordinates to momentum space for
        arbitrary goniometer geometries and X-ray energy. (from xru docs)
        """

        q_conv = xu.experiment.QConversion(sample_circle_dir, det_circle_dir, primary_beam_dir)

        # x+/-, y+/-, z+/-
        inplane_ref_dir = i_reader.getInplaneReferenceDirection()
        sample_norm_dir = i_reader.getSampleSurfaceNormalDirection()

        """
        Object describing high angle x-ray diffraction experiments and helps with
        calculating the angles of Bragg reflections as well as helps with analyzing
        measured data. (from xru docs)
        """

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

        return (qx, qy, qz)

# ==============================================================================
