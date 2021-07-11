#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Writes a simple NeXus HDF5 file using h5py with links.

This example is based on ``writer_2_1`` of the NeXus Manual:
http://download.nexusformat.org/doc/html/examples/h5py/index.html
"""

from spec2nexus import eznx


HDF5_FILE = "eznx_example.hdf5"

I_v_TTH_DATA = """
17.92608    1037
17.92558    2857
17.92508    23819
17.92458    49087
17.92408    66802
17.92358    66206
17.92308    64129
17.92258    56795
17.92208    29315
17.92158    6622
17.92108    1321
"""
# ---------------------------

tthData, countsData = zip(
    *[map(float, _.split()) for _ in I_v_TTH_DATA.strip().splitlines()]
)

f = eznx.makeFile(HDF5_FILE)  # create the HDF5 NeXus file
f.attrs["default"] = "entry"

nxentry = eznx.makeGroup(f, "entry", "NXentry", default="data")
nxinstrument = eznx.makeGroup(nxentry, "instrument", "NXinstrument")
nxdetector = eznx.makeGroup(nxinstrument, "detector", "NXdetector")

tth = eznx.makeDataset(nxdetector, "two_theta", tthData, units="degrees")
counts = eznx.makeDataset(nxdetector, "counts", countsData, units="counts")

nxdata = eznx.makeGroup(
    nxentry,
    "data",
    "NXdata",
    signal=1,
    axes="two_theta",
    two_theta_indices=0,
)
eznx.makeLink(nxdetector, tth, nxdata.name + "/two_theta")
eznx.makeLink(nxdetector, counts, nxdata.name + "/counts")

f.close()  # be CERTAIN to close the file
