"""
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

# ==============================================================================

from pyqtgraph.Qt import QtGui, QtCore

# ==============================================================================

class DataSourceDialogWidget(QtGui.QDialog):

    """
    Creates modal dialog widget for the user to choose directories and files as
    their data source.
    """

    def __init__ (self):
        super().__init__()

        self.setWindowModality(QtCore.Qt.ApplicationModal)

        # Holds values from textboxes/checkbox
        self.spec_name = ""
        self.detector_config_name = ""
        self.instrument_config_name = ""
        self.process_data = False
        self.ok = False

        # Creates widgets
        self.spec_lbl = QtGui.QLabel("spec File:")
        self.spec_txtbox = QtGui.QLineEdit()
        self.spec_txtbox.setReadOnly(True)
        self.spec_btn = QtGui.QPushButton("Browse")
        self.detector_lbl = QtGui.QLabel("Det. Config:")
        self.detector_txtbox = QtGui.QLineEdit()
        self.detector_txtbox.setReadOnly(True)
        self.detector_btn = QtGui.QPushButton("Browse")
        self.instrument_lbl = QtGui.QLabel("Instr. Config:")
        self.instrument_txtbox = QtGui.QLineEdit()
        self.instrument_txtbox.setReadOnly(True)
        self.instrument_btn = QtGui.QPushButton("Browse")
        self.dialog_btnbox = QtGui.QDialogButtonBox()
        self.dialog_btnbox.addButton("OK", QtGui.QDialogButtonBox.AcceptRole)

        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)

        # Adds widgets to layout
        self.layout.addWidget(self.spec_lbl, 0, 0)
        self.layout.addWidget(self.spec_txtbox, 0, 1, 1, 3)
        self.layout.addWidget(self.spec_btn, 0, 4)
        self.layout.addWidget(self.detector_lbl, 1, 0)
        self.layout.addWidget(self.detector_txtbox, 1, 1, 1, 3)
        self.layout.addWidget(self.detector_btn, 1, 4)
        self.layout.addWidget(self.instrument_lbl, 2, 0)
        self.layout.addWidget(self.instrument_txtbox, 2, 1, 1, 3)
        self.layout.addWidget(self.instrument_btn, 2, 4)
        self.layout.addWidget(self.dialog_btnbox, 3, 3, 1, 2)

        # Connects widgets to functions
        self.spec_btn.clicked.connect(self.selectSpecFile)
        self.detector_btn.clicked.connect(self.selectDetectorConfigFile)
        self.instrument_btn.clicked.connect(self.selectInstrumentConfigFile)
        self.dialog_btnbox.accepted.connect(self.accept)

        # Runs dialog widget
        self.exec_()

    # --------------------------------------------------------------------------

    def selectSpecFile(self):
        spec = QtGui.QFileDialog.getOpenFileName(self, "", "", "spec Files (*.spec)")
        self.spec_name = spec[0]
        self.spec_txtbox.setText(spec[0])

    # --------------------------------------------------------------------------

    def selectDetectorConfigFile(self):
        detector = QtGui.QFileDialog.getOpenFileName(self, "", "", "xml Files (*.xml)")
        self.detector_config_name = detector[0]
        self.detector_txtbox.setText(detector[0])

    # --------------------------------------------------------------------------

    def selectInstrumentConfigFile(self):
        instrument = QtGui.QFileDialog.getOpenFileName(self, "", "", "xml Files (*.xml)")
        self.instrument_config_name = instrument[0]
        self.instrument_txtbox.setText(instrument[0])

    # --------------------------------------------------------------------------

    def setDataProcessingStatus(self):

        """
        Changes the enabled status of certain widgets based on the checkbox's state.
        """

        checkbox = self.sender()

        if checkbox.checkState():
            self.process_data = True
            self.spec_btn.setEnabled(True)
            self.detector_btn.setEnabled(True)
            self.instrument_btn.setEnabled(True)
        else:
            self.process_data = False
            self.spec_btn.setEnabled(False)
            self.detector_btn.setEnabled(False)
            self.instrument_btn.setEnabled(False)

# ==============================================================================

class ConversionParametersDialogWidget(QtGui.QDialog):

    def __init__ (self):
        super().__init__()

        self.setWindowModality(QtCore.Qt.ApplicationModal)

        self.detector_dir_1 = ""
        self.detector_dir_2 = ""
        self.cch_1 = 0.0
        self.cch_2 = 0.0
        self.nch_1 = 0
        self.nch_2 = 0
        self.distance = 0.0
        self.p_width_1 = 0.0
        self.p_width_2 = 0.0
        self.chpdeg_1 = 0.0
        self.chpdeg_2 = 0.0
        self.detrot = 0.0
        self.tiltazimuth = 0.0
        self.tilt = 0.0
        self.nav = [1, 1]
        self.roi = []
        self.ub_matrix = []
        self.mu = 0.0
        self.eta = 0.0
        self.chi = 0.0
        self.phi = 0.0
        self.nu = 0.0
        self.delta = 0.0

        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)

        self.detector_dir_1_lbl = QtGui.QLabel("Detector Direction 1:")
        self.detector_dir_1_cbox = QtGui.QComboBox()
        self.detector_dir_1_cbox.addItems(["x+", "x-", "y+", "y-", "z+", "z-"])
        self.detector_dir_2_lbl = QtGui.QLabel("Detector Direction 2:")
        self.detector_dir_2_cbox = QtGui.QComboBox()
        self.detector_dir_2_cbox.addItems(["x+", "x-", "y+", "y-", "z+", "z-"])
        self.center_pixel_lbl = QtGui.QLabel("Center Pixel:")
        self.center_pixel_1_sbox = QtGui.QDoubleSpinBox()
        self.center_pixel_1_sbox.setRange(-10000.0, 10000.0)
        self.center_pixel_2_sbox = QtGui.QDoubleSpinBox()
        self.center_pixel_2_sbox.setRange(-10000.0, 10000.0)
        self.number_pixels_1_lbl = QtGui.QLabel("# Pixels (Direction 1):")
        self.number_pixels_1_sbox = QtGui.QSpinBox()
        self.number_pixels_1_sbox.setMaximum(10000)
        self.number_pixels_2_lbl = QtGui.QLabel("# Pixels (Direction 2):")
        self.number_pixels_2_sbox = QtGui.QSpinBox()
        self.number_pixels_2_sbox.setMaximum(10000)
        self.distance_lbl = QtGui.QLabel("Distance:")
        self.distance_sbox = QtGui.QDoubleSpinBox()
        self.distance_sbox.setMaximum(10000.0)
        self.pixel_size_lbl = QtGui.QLabel("Pixel Size:")
        self.pixel_width_1_sbox = QtGui.QDoubleSpinBox()
        self.pixel_width_2_sbox = QtGui.QDoubleSpinBox()
        self.channels_per_degree_1_lbl = QtGui.QLabel("Channels/Degree (Direction 1):")
        self.channels_per_degree_1_sbox = QtGui.QDoubleSpinBox()
        self.channels_per_degree_2_lbl = QtGui.QLabel("Channels/Degree (Direction 2):")
        self.channels_per_degree_2_sbox = QtGui.QDoubleSpinBox()
        self.detector_rotation_angle_lbl = QtGui.QLabel("Detector Rotation Angle (deg):")
        self.detector_rotation_angle_sbox = QtGui.QDoubleSpinBox()
        self.detector_rotation_angle_sbox.setMaximum(360.0)
        self.tilt_azimuth_angle_lbl = QtGui.QLabel("Azimuth Angle (deg):")
        self.tilt_azimuth_angle_sbox = QtGui.QDoubleSpinBox()
        self.tilt_azimuth_angle_sbox.setMaximum(360.0)
        self.tilt_angle_lbl = QtGui.QLabel("Tilt Angle (deg):")
        self.tilt_angle_sbox = QtGui.QDoubleSpinBox()
        self.tilt_angle_sbox.setMaximum(360.0)
        self.nav_lbl = QtGui.QLabel("Nav (Tuple/Array):")
        self.nav_txtbox = QtGui.QLineEdit()
        self.roi_lbl = QtGui.QLabel("ROI (Tuple/Array):")
        self.roi_txtbox = QtGui.QLineEdit()
        self.ub_matrix_lbl = QtGui.QLabel("UB Matrix:")
        self.ub_matrix_txtedit = QtGui.QPlainTextEdit()
        self.mu_lbl = QtGui.QLabel("Mu (deg):")
        self.mu_sbox = QtGui.QDoubleSpinBox()
        self.mu_sbox.setMaximum(360.0)
        self.eta_lbl = QtGui.QLabel("Eta (deg):")
        self.eta_sbox = QtGui.QDoubleSpinBox()
        self.eta_sbox.setMaximum(360.0)
        self.chi_lbl = QtGui.QLabel("Chi (deg):")
        self.chi_sbox = QtGui.QDoubleSpinBox()
        self.chi_sbox.setMaximum(360.0)
        self.phi_lbl = QtGui.QLabel("Phi (deg):")
        self.phi_sbox = QtGui.QDoubleSpinBox()
        self.phi_sbox.setMaximum(360.0)
        self.nu_lbl = QtGui.QLabel("Nu (deg):")
        self.nu_sbox = QtGui.QDoubleSpinBox()
        self.nu_sbox.setMaximum(360.0)
        self.delta_lbl = QtGui.QLabel("Delta (deg):")
        self.delta_sbox = QtGui.QDoubleSpinBox()
        self.delta_sbox.setMaximum(360.0)
        self.import_btn = QtGui.QPushButton("Import UB Matrix/Diff. Angles")
        self.dialog_btnbox = QtGui.QDialogButtonBox()
        self.dialog_btnbox.addButton("OK", QtGui.QDialogButtonBox.AcceptRole)

        self.layout.addWidget(self.detector_dir_1_lbl, 0, 0, 1, 2)
        self.layout.addWidget(self.detector_dir_1_cbox, 0, 2)
        self.layout.addWidget(self.detector_dir_2_lbl, 1, 0, 1, 2)
        self.layout.addWidget(self.detector_dir_2_cbox, 1, 2)
        self.layout.addWidget(self.center_pixel_lbl, 2, 0)
        self.layout.addWidget(self.center_pixel_1_sbox, 2, 1)
        self.layout.addWidget(self.center_pixel_2_sbox, 2, 2)
        self.layout.addWidget(self.number_pixels_1_lbl, 3, 0, 1, 2)
        self.layout.addWidget(self.number_pixels_1_sbox, 3, 2)
        self.layout.addWidget(self.number_pixels_2_lbl, 4, 0, 1, 2)
        self.layout.addWidget(self.number_pixels_2_sbox, 4, 2)
        self.layout.addWidget(self.distance_lbl, 5, 0, 1, 2)
        self.layout.addWidget(self.distance_sbox, 5, 2)
        self.layout.addWidget(self.pixel_size_lbl, 6, 0)
        self.layout.addWidget(self.pixel_width_1_sbox, 6, 1)
        self.layout.addWidget(self.pixel_width_2_sbox, 6, 2)
        self.layout.addWidget(self.channels_per_degree_1_lbl, 7, 0, 1, 2)
        self.layout.addWidget(self.channels_per_degree_1_sbox, 7, 2)
        self.layout.addWidget(self.channels_per_degree_2_lbl, 8, 0, 1, 2)
        self.layout.addWidget(self.channels_per_degree_2_sbox, 8, 2)
        self.layout.addWidget(self.detector_rotation_angle_lbl, 9, 0, 1, 2)
        self.layout.addWidget(self.detector_rotation_angle_sbox, 9, 2)
        self.layout.addWidget(self.tilt_azimuth_angle_lbl, 10, 0, 1, 2)
        self.layout.addWidget(self.tilt_azimuth_angle_sbox, 10, 2)
        self.layout.addWidget(self.tilt_angle_lbl, 11, 0, 1, 2)
        self.layout.addWidget(self.tilt_angle_sbox, 11, 2)
        self.layout.addWidget(self.nav_lbl, 12, 0)
        self.layout.addWidget(self.nav_txtbox, 12, 1, 1, 2)
        self.layout.addWidget(self.roi_lbl, 13, 0)
        self.layout.addWidget(self.roi_txtbox, 13, 1, 1, 2)
        self.layout.addWidget(self.ub_matrix_lbl, 14, 0)
        self.layout.addWidget(self.ub_matrix_txtedit, 14, 1, 1, 2)
        self.layout.addWidget(self.mu_lbl, 15, 0)
        self.layout.addWidget(self.mu_sbox, 15, 1, 1, 2)
        self.layout.addWidget(self.eta_lbl, 16, 0)
        self.layout.addWidget(self.eta_sbox, 16, 1, 1, 2)
        self.layout.addWidget(self.chi_lbl, 17, 0)
        self.layout.addWidget(self.chi_sbox, 17, 1, 1, 2)
        self.layout.addWidget(self.phi_lbl, 18, 0)
        self.layout.addWidget(self.phi_sbox, 18, 1, 1, 2)
        self.layout.addWidget(self.nu_lbl, 19, 0)
        self.layout.addWidget(self.nu_sbox, 19, 1, 1, 2)
        self.layout.addWidget(self.delta_lbl, 20, 0)
        self.layout.addWidget(self.delta_sbox, 20, 1, 1, 2)
        self.layout.addWidget(self.import_btn, 21, 0)
        self.layout.addWidget(self.dialog_btnbox, 21, 2)

        self.dialog_btnbox.accepted.connect(self.accept)

        # Runs dialog widget
        self.exec_()

    # --------------------------------------------------------------------------

    def accept(self):

        """
        Overrides (built-in) PyQt5 function.
        """

        self.detector_dir_1 = self.detector_dir_1_cbox.currentText()
        self.detector_dir_2 = self.detector_dir_2_cbox.currentText()
        self.cch_1 = self.center_pixel_1_sbox.value()
        self.cch_2 = self.center_pixel_2_sbox.value()
        self.nch_1 = self.number_pixels_1_sbox.value()
        self.nch_2 = self.number_pixels_2_sbox.value()
        self.distance = self.distance_sbox.value()
        self.p_width_1 = self.pixel_width_1_sbox.value()
        self.p_width_2 = self.pixel_width_2_sbox.value()
        self.chpdeg_1 = self.channels_per_degree_1_sbox.value()
        self.chpdeg_2 = self.channels_per_degree_2_sbox.value()
        self.detrot = self.detector_rotation_angle_sbox.value()
        self.tiltazimuth = self.tilt_azimuth_angle_sbox.value()
        self.tilt = self.tilt_angle_sbox.value()
        self.nav = self.nav_txtbox.text()
        self.roi = self.roi_txtbox.text()
        self.ub_matrix = self.ub_matrix_txtedit.text()
        self.mu = self.mu_sbox.value()
        self.eta = self.eta_sbox.value()
        self.chi = self.chi_sbox.value()
        self.phi = self.phi_sbox.value()
        self.nu = self.nu_sbox.value()
        self.delta = self.delta_sbox.value() 

        print("ACCEPTED")

# ==============================================================================
