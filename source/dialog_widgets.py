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

        self.detector_direction_1 = ""
        self.detector_direction_2 = ""
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
        self.nav = []
        self.roi = []
        self.ub_matrix = []



        # Runs dialog widget
        self.exec_()
