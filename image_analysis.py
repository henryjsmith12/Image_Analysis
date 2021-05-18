"""
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

# ==============================================================================

import pyqtgraph as pg

# Local
from source.main_window import MainWindow

# ==============================================================================

app = pg.mkQApp("Image Analysis")
window = MainWindow()
window.show()
pg.mkQApp().exec_()
