"""
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

# ==============================================================================

import pyqtgraph as pg

from source.main_window import MainWindow # Local

# ==============================================================================

app = pg.mkQApp("Image Analysis")
window = MainWindow() # Inherits from pg.QtGui.QMainWindow
window.show()
pg.mkQApp().exec_()
