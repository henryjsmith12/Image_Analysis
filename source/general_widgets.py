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

# ==============================================================================

class ImageWidget(pg.PlotWidget):

    def __init__ (self, parent):
        super(ImageWidget, self).__init__(parent)
        self.parent = parent

        self.setBackground("default")

# ==============================================================================

class ROIWidget(pg.ROI):

    def __init__ (self, parent):
        super(ROIWidget, self).__init__(parent)
        self.parent = parent

# ==============================================================================
