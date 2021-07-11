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
**#H** & **#V** - Metadata in SPEC data files as defined by APS UNICAT

Handles the UNICAT control lines which write additional metadata
in the scans using #H/#V pairs of labels/values.
"""


import re
import six

from .. import eznx
from ..plugin import AutoRegister, ControlLineHandler
from ..utils import strip_first_word


@six.add_metaclass(AutoRegister)
class UNICAT_MetadataMnemonics(ControlLineHandler):

    """
    **#H** -- UNICAT metadata names (numbered rows: #H0, #H1, ...)

    Individual metadata names are expected to be single-word strings
    but may be multi-word strings as long as the words in the string
    are separated by only one space.  The delimiter between metadata
    names is two consecutive spaces.  A tab (``\\t``) character is also
    acceptable but should be avoided.

    IN-MEMORY REPRESENTATION

    * (SpecDataFileHeader) : **H** : labels
    * (SpecDataFileScan): **metadata** : {labels: values}

    HDF5/NeXus REPRESENTATION

    * *NXnote* group named **metadata** below the
      *NXentry* group, such as **/entry/metadata**

      * datasets created from dictionary <scan>.metadata

    """

    key = r"#H\d+"
    scan_attributes_defined = ["H"]

    def process(self, text, spec_obj, *args, **kws):
        row_text = strip_first_word(text)
        labels = re.split(r"  +", row_text)
        spec_obj.H.append(labels)


@six.add_metaclass(AutoRegister)
class UNICAT_MetadataValues(ControlLineHandler):

    """
    **#V** -- UNICAT metadata values (numbered rows: #V0, #V1, ...)

    Individual metadata values are expected to be numbers but may
    be multi-word strings as long as the words in the string are
    separated by only one space.  The delimiter between metadata
    values is two consecutive spaces.  A tab (``'\\t'``) character is
    also acceptable but should be avoided.

    All numerical values will be converted into floating point
    numbers.  Only if that conversion fails, the text of the value
    will be reported verbatim.

    IN-MEMORY REPRESENTATION

    * (SpecDataFileScan): **V** : values
    * (SpecDataFileScan): **metadata** : {labels: values}

    HDF5/NeXus REPRESENTATION

    * *NXnote* group named **metadata** below the
      *NXentry* group, such as **/entry/metadata**

      * datasets created from dictionary <scan>.metadata

    """

    key = r"#V\d+"
    scan_attributes_defined = ["V", "metadata"]

    def process(self, text, scan, *args, **kws):
        index = len(scan.V)
        row_text = strip_first_word(text)
        for delimiter in (r" " * 2, r" "):
            values = re.split(delimiter, row_text)
            if len(scan.header.H[index]) == len(values):
                break

        scan.V.append(values)
        scan.addPostProcessor("unicat_metadata", self.postprocess)

    def postprocess(self, scan, *args, **kws):
        """
        interpret the UNICAT metadata (mostly floating point) from the scan header

        :param SpecDataFileScan scan: data from a single SPEC scan (instance of SpecDataFileScan)
        """
        scan.metadata = {}
        if not hasattr(scan.header, "H"):
            msg = "No matching #H line(s) for scan %d" % scan.scanNum
            raise KeyError(msg)
        for row, values in enumerate(scan.V):
            if (row + 1) > len(scan.header.H):
                msg = "No matching #H%d line for #V%d in scan %d" % (
                    row,
                    row,
                    scan.scanNum,
                )
                raise KeyError(msg)
            for col, val in enumerate(values):
                if (col + 1) > len(scan.header.H[row]):
                    msg = (
                        "No matching label in #H%d line for #V%d, column %d in scan %d"
                        % (row, row, col, scan.scanNum)
                    )
                    raise KeyError(msg)
                label = scan.header.H[row][col]
                try:
                    scan.metadata[label] = float(val)
                except ValueError:
                    scan.metadata[label] = val
        scan.addH5writer(self.key, self.writer)

    def writer(self, h5parent, writer, scan, nxclass=None, *args, **kws):
        """Describe how to store this data in an HDF5 NeXus file"""
        if hasattr(scan, "metadata") and len(scan.metadata) > 0:
            desc = "SPEC metadata (UNICAT-style #H & #V lines)"
            group = eznx.makeGroup(
                h5parent, "metadata", nxclass, description=desc
            )
            writer.save_dict(group, scan.metadata)

            # link it to the NXinstrument group
            nxinstrument = eznx.openGroup(
                h5parent, "instrument", "NXinstrument"
            )
            eznx.makeLink(h5parent, group, nxinstrument.name + "/metadata")
