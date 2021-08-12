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
**#MD** : Bluesky metadata from apstools SpecWriterCallback.

EXAMPLE::

    #MD APSTOOLS_VERSION = 1.1.0
    #MD BLUESKY_VERSION = 1.5.2
    #MD EPICS_CA_MAX_ARRAY_BYTES = 1280000
    #MD EPICS_HOST_ARCH = linux-x86_64
    #MD OPHYD_VERSION = 1.3.2
    #MD beamline_id = APS USAXS 9-ID-C
    #MD datetime = 2019-04-19 10:04:44.400750
    #MD login_id = usaxs@usaxscontrol.xray.aps.anl.gov
    #MD pid = 27062
    #MD proposal_id = testing Bluesky installation
    #MD purpose = tuner
    #MD tune_md = {'width': -0.004, 'initial_position': 8.824885, 'time_iso8601': '2019-04-19 10:04:44.402643'}
    #MD tune_parameters = {'num': 31, 'width': -0.004, 'initial_position': 8.824885, 'peak_choice': 'com', 'x_axis': 'm_stage_r', 'y_axis': 'I0_USAXS'}
"""

from collections import OrderedDict
import six

from .. import eznx
from ..plugin import AutoRegister, ControlLineHandler


@six.add_metaclass(AutoRegister)
class MD_apstools(ControlLineHandler):

    """**#MD** -- Bluesky metadata from apstools SpecWriterCallback"""

    key = r"#MD\w*"
    scan_attributes_defined = ["MD"]

    def process(self, text, scan, *args, **kws):
        """read #MD lines from SPEC data file"""
        if not hasattr(scan, "MD"):
            scan.MD = OrderedDict()

        p = text.find("=")
        if p > len("# MD "):
            # f"#MD {key} = {value}"
            key = text.split()[1]
            value = text[p + 1 :].strip()
        else:
            # badly-formed #MD control line
            key = "MD_line_%d" % (len(scan.MD) + 1)
            value = text.strip()
        scan.MD[key] = value
        scan.addH5writer(self.key, self.writer)

    def writer(self, h5parent, writer, scan, nxclass=None, *args, **kws):
        """Describe how to store this data in an HDF5 NeXus file"""
        nxclass = "NXcollection"
        if hasattr(scan, "MD") and len(scan.MD) > 0:
            desc = "Bluesky metadata (as written by apstools.SpecWriterCallback)"
            group = eznx.makeGroup(
                h5parent, "bluesky_metadata", nxclass, description=desc
            )
            writer.save_dict(group, scan.MD)
