#!/usr/bin/env python
# -*- coding: utf-8 -*-

# -----------------------------------------------------------------------------
# :author:    Pete R. Jemian
# :email:     prjemian@gmail.com
# :copyright: (c) 2014-2020, Pete R. Jemian
#
# Distributed under the terms of the Creative Commons Attribution 4.0 International Public License.
#
# The full license is in the file LICENSE.txt, distributed with this software.
# -----------------------------------------------------------------------------

"""
**#UIM** : Image header information from EPICS areaDetector

:deprecated: in favor of UXML
"""

# TODO: for each ControlLineHandler, describe where data goes, both internally and in HDF5 file

"""
#UIM Image header information from areaDetector
#UIM UIMR: ROI information, UIMC: image counter setup
#UIM Center pixel: 206 85
#UIMR Name minX sizeX minY sizeY BgdWidth
#UIMR1  156 101 35 101 0
#UIMR2  196 21 60 51 0
#UIMR3  166 80 45 80 0
#UIMR4  126 160 5 160 0
#UIMC counter STATS# Value-PV
#UIMC1 imtot 5 Total
#UIMC2 immax 5 MaxValue
#UIMC3 imroi1 1 Net
#UIMC4 imroi2 2 Net
#UIMC5 imroi3 3 Net
#UIMC6 imroi4 4 Net
#UIMC7 imsca1 1 MaxValue
#UIMC8 imsca2 2 MaxValue
#UIMC9 imsca3 3 MaxValue
#UIMC10 imsca4 4 MaxValue
"""


import six
from ..plugin import AutoRegister, ControlLineHandler


@six.add_metaclass(AutoRegister)
class UIM_generic(ControlLineHandler):

    """**#UIM** -- various image header information"""

    key = r"#UIM\w*"
    scan_attributes_defined = ["UIM"]

    def process(self, text, spec_obj, *args, **kws):
        if not hasattr(spec_obj, "UIM"):
            spec_obj.UIM = []

        spec_obj.UIM.append(text)
