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
Fallback handling for any SPEC data file control lines not recognized by other handlers
"""

from collections import OrderedDict
import six

from ..eznx import makeGroup
from ..plugin import AutoRegister, ControlLineHandler
from ..spec import UNRECOGNIZED_KEY, SpecDataFileHeader, SpecDataFileScan


@six.add_metaclass(AutoRegister)
class UnrecognizedControlLine(ControlLineHandler):

    """unrecognized control line"""

    key = UNRECOGNIZED_KEY
    scan_attributes_defined = ["_unrecognized"]

    def process(self, text, spec_obj, *args, **kws):
        " "
        if not hasattr(spec_obj, "_unrecognized"):
            spec_obj._unrecognized = []
        spec_obj._unrecognized.append(text)
        if isinstance(spec_obj, SpecDataFileHeader) or isinstance(
            spec_obj, SpecDataFileScan
        ):
            spec_obj.addH5writer(self.key, self.writer)

    def writer(self, h5parent, writer, scan, nxclass=None, *args, **kws):
        """write the data in a NeXus group named ``unrecognized``"""
        desc = "SPEC data file control lines not otherwise recognized"
        nxclass = "NXnote"
        i = 0
        success = False
        while not success:
            i += 1
            nm = "unrecognized_" + str(i)
            if nm not in h5parent.keys():
                group = makeGroup(h5parent, nm, nxclass, description=desc)
                success = True
        dd = OrderedDict()
        for i, value in enumerate(scan._unrecognized):
            dd["u" + str(i)] = value
        writer.save_dict(group, dd)
