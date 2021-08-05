"""
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

# ==============================================================================

from setuptools import setup

# ==============================================================================

setup(
    name='Image_Analysis',
    version='0.0.0',
    description='A lightweight option for viewing scan data.',
    author='Henry Smith',
    author_email='smithh@anl.gov',
    url='https://github.com/henryjsmith12/Image_Analysis',
    install_requires=['pyqtgraph',
                      'matplotlib',
                      'numpy',
                      'rsMap3D',
                      'scipy',
                      'tifffile',
                      'vtk',
                      'xrayutilities',
                      ],
    license='See LICENSE File',
    platforms='any',
)
