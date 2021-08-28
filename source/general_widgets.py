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

        # Image within image widget
        self.image_item = pg.ImageItem()
        self.addItem(self.image_item)

        self.setBackground("default")

        # Larger y-values towards bottom
        self.invertY(True)

    # --------------------------------------------------------------------------

    def displayImage(self, image):
        # Normalize image with logarithmic colormap
        colormap_max = np.amax(image)
        norm = colors.LogNorm(vmax=colormap_max)
        norm_image = norm(image)
        color_image = plt.cm.jet(norm_image)

        # Set image to image item
        self.image_item.setImage(color_image)


# ==============================================================================

class ROIWidget(pg.ROI):

    def __init__ (self, parent):
        super(ROIWidget, self).__init__(parent)
        self.parent = parent

# ==============================================================================
