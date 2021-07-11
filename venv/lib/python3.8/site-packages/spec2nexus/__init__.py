# -*- coding: iso-8859-1 -*-

"""command-line tool to convert SPEC data files to NeXus HDF5"""

# -----------------------------------------------------------------------------
# :author:    Pete R. Jemian
# :email:     prjemian@gmail.com
# :copyright: (c) 2014-2020, Pete R. Jemian
#
# Distributed under the terms of the Creative Commons Attribution 4.0 International Public License.
#
# The full license is in the file LICENSE.txt, distributed with this software.
# -----------------------------------------------------------------------------


__author__ = "Pete R. Jemian"
__email__ = "prjemian@gmail.com"
__copyright__ = "2014-2020, Pete R. Jemian"

__package_name__ = "spec2nexus"

__license_url__ = "http://creativecommons.org/licenses/by/4.0/deed.en_US"
__license__ = "Creative Commons Attribution 4.0 International Public License (see LICENSE file)"
__description__ = (
    "Converts SPEC data files and scans into NeXus HDF5 files"
)
__author_name__ = __author__
__author_email__ = __email__
__url__ = u"http://spec2nexus.readthedocs.org"
__keywords__ = [
    "SPEC",
    "diffraction",
    "data acquisition",
    "NeXus",
    "HDF5",
    "MatPlotLib",
]

from ._requirements import learn_requirements

__install_requires__ = learn_requirements()
del learn_requirements

__classifiers__ = [
    "Development Status :: 5 - Production/Stable",
    "Environment :: Console",
    "Intended Audience :: Science/Research",
    "License :: Freely Distributable",
    "License :: Public Domain",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Topic :: Scientific/Engineering",
    "Topic :: Scientific/Engineering :: Astronomy",
    "Topic :: Scientific/Engineering :: Bio-Informatics",
    "Topic :: Scientific/Engineering :: Chemistry",
    "Topic :: Scientific/Engineering :: Information Analysis",
    "Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator",
    "Topic :: Scientific/Engineering :: Mathematics",
    "Topic :: Scientific/Engineering :: Physics",
    "Topic :: Scientific/Engineering :: Visualization",
    "Topic :: Software Development",
    "Topic :: Utilities",
]

from ._version import get_versions

__version__ = get_versions()["version"]
del get_versions
