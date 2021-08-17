"""
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

# ==============================================================================

from pyqtgraph.Qt import QtGui, QtCore

# ==============================================================================

class DataSourceDialogWidget(QtGui.QDialog):

    """
    Creates modal dialog widget where the user can select data source files.
    """

    def __init__ (self):
        super().__init__()

        self.setWindowModality(QtCore.Qt.ApplicationModal)

        self.spec_name = ""
        self.detector_config_name = ""
        self.instrument_config_name = ""
        self.pixel_count_nx = ""
        self.pixel_count_ny = ""
        self.pixel_count_nz = ""

        # Create widgets
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
        self.pixel_count_lbl = QtGui.QLabel("Pixel Count:")
        self.pixel_count_nx_sbox = QtGui.QSpinBox(maximum=1000, minimum=1)
        self.pixel_count_nx_sbox.setValue(200)
        self.pixel_count_ny_sbox = QtGui.QSpinBox(maximum=1000, minimum=1)
        self.pixel_count_ny_sbox.setValue(200)
        self.pixel_count_nz_sbox = QtGui.QSpinBox(maximum=1000, minimum=1)
        self.pixel_count_nz_sbox.setValue(200)
        self.dialog_btnbox = QtGui.QDialogButtonBox()
        self.dialog_btnbox.addButton("OK", QtGui.QDialogButtonBox.AcceptRole)

        # Create layout
        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)

        # Add widgets to layout
        self.layout.addWidget(self.spec_lbl, 0, 0)
        self.layout.addWidget(self.spec_txtbox, 0, 1, 1, 3)
        self.layout.addWidget(self.spec_btn, 0, 4)
        self.layout.addWidget(self.detector_lbl, 1, 0)
        self.layout.addWidget(self.detector_txtbox, 1, 1, 1, 3)
        self.layout.addWidget(self.detector_btn, 1, 4)
        self.layout.addWidget(self.instrument_lbl, 2, 0)
        self.layout.addWidget(self.instrument_txtbox, 2, 1, 1, 3)
        self.layout.addWidget(self.instrument_btn, 2, 4)
        self.layout.addWidget(self.pixel_count_lbl, 3, 0)
        self.layout.addWidget(self.pixel_count_nx_sbox, 3, 1)
        self.layout.addWidget(self.pixel_count_ny_sbox, 3, 2)
        self.layout.addWidget(self.pixel_count_nz_sbox, 3, 3)
        self.layout.addWidget(self.dialog_btnbox, 4, 3, 1, 2)

        # Connect widgets to functions
        self.spec_btn.clicked.connect(self.selectSpecFile)
        self.detector_btn.clicked.connect(self.selectDetectorConfigFile)
        self.instrument_btn.clicked.connect(self.selectInstrumentConfigFile)
        self.dialog_btnbox.accepted.connect(self.accept)

        # Run dialog widget
        self.exec_()

    # --------------------------------------------------------------------------

    def selectSpecFile(self):

        """
        Allows user to select .spec file.
        """

        spec = QtGui.QFileDialog.getOpenFileName(self, "", "", "spec Files (*.spec)")
        self.spec_txtbox.setText(spec[0])

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

    def accept(self):

        """
        Sets class variables to values in dialog and closes the dialog window.
        """

        self.spec_name = self.spec_txtbox.text()
        self.detector_config_name = self.detector_txtbox.text()
        self.instrument_config_name = self.instrument_txtbox.text()
        self.pixel_count_nx = self.pixel_count_nx_sbox.value()
        self.pixel_count_ny = self.pixel_count_ny_sbox.value()
        self.pixel_count_nz = self.pixel_count_nz_sbox.value()
        self.close()

# ==============================================================================

class ConversionParametersDialogWidget(QtGui.QDialog):

    """
    Creates modal dialog widget where the user can select hkl conversion parameters.
    """

    def __init__ (self):
        super().__init__()

        self.setWindowModality(QtCore.Qt.ApplicationModal)

        self.detector_config_name = ""
        self.instrument_config_name = ""
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
        self.delta_sbox.setMaximum(360.0)
        self.energy_lbl = QtGui.QLabel("Energy:")
        self.energy_sbox = QtGui.QSpinBox()
        self.energy_sbox.setMaximum(100000)
        self.import_btn = QtGui.QPushButton("Import UB Matrix/Diff. Angles")
        self.dialog_btnbox = QtGui.QDialogButtonBox()
        self.dialog_btnbox.addButton("OK", QtGui.QDialogButtonBox.AcceptRole)

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
        self.layout.addWidget(self.dialog_btnbox, 10, 2)

        # Connect widgets to functions
        self.detector_btn.clicked.connect(self.selectDetectorConfigFile)
        self.instrument_btn.clicked.connect(self.selectInstrumentConfigFile)
        self.dialog_btnbox.accepted.connect(self.accept)

        # Runs dialog widget
        self.exec_()

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

    def accept(self):

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

class AdvancedROIDialogWidget(QtGui.QDialog):

    def __init__ (self):
        super().__init__()

        self.setWindowModality(QtCore.Qt.ApplicationModal)

        self.first_roi = ""
        self.operator = ""
        self.second_roi = ""

        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)

        self.first_roi_cbox = QtGui.QComboBox()
        self.first_roi_cbox.addItems(["", "ROI 1", "ROI 2", "ROI 3", "ROI 4"])
        self.operator_cbox = QtGui.QComboBox()
        self.operator_cbox.addItems(["-"])
        self.second_roi_cbox = QtGui.QComboBox()
        self.second_roi_cbox.addItems(["", "ROI 1", "ROI 2", "ROI 3", "ROI 4"])
        self.dialog_btnbox = QtGui.QDialogButtonBox()
        self.dialog_btnbox.addButton("OK", QtGui.QDialogButtonBox.AcceptRole)

        self.layout.addWidget(self.first_roi_cbox, 0, 0)
        self.layout.addWidget(self.operator_cbox, 0, 1)
        self.layout.addWidget(self.second_roi_cbox, 0, 2)
        self.layout.addWidget(self.dialog_btnbox, 1, 2)

        self.dialog_btnbox.accepted.connect(self.accept)

        # Runs dialog widget
        self.exec_()

    # --------------------------------------------------------------------------

    def accept(self):
        self.first_roi = self.first_roi_cbox.currentText()
        self.operator = self.operator_cbox.currentText()
        self.second_roi = self.second_roi_cbox.currentText()
        self.close()


# ==============================================================================
