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


"""(internal library) Parses SPEC data using spec2nexus.eznx API (only requires h5py)"""


import h5py
import numpy as np

from . import eznx
from . import spec
from . import utils


# see: http://download.nexusformat.org/doc/html/classes/base_classes/index.html
# CONTAINER_CLASS = 'NXlog'          # information that is recorded against time
CONTAINER_CLASS = "NXnote"  # any additional freeform information not covered by the other base classes
# CONTAINER_CLASS = 'NXparameters'   # Container for parameters, usually used in processing or analysis
# CONTAINER_CLASS = 'NXcollection'    # Use NXcollection to gather together any set of terms


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


class Writer(object):

    """
    writes out scans from SPEC data file to NeXus HDF5 file

    :param obj spec_data: instance of :class:`~spec2nexus.spec.SpecDataFile`
    """

    def __init__(self, spec_data):
        self.spec = spec_data

    def save(self, hdf_file, scan_list=None):
        """
        save the information in this SPEC data file to a NeXus HDF5 file

        Each scan in scan_list will be converted to a **NXentry** group.
        Scan data will be placed in a **NXdata** group where the attribute **signal=1** is the
        last column and the corresponding attribute **axes=<name of the first column>**.
        There are variations on this for 2-D and higher dimensionality data, such as mesh scans.

        In general, the tree structure of the NeXus HDF5 file is::

            hdf5_file: NXroot
                @default="S1"
                definition="NXspecdata"
                # attributes
                S1:NXentry
                    @default="data"
                    # attributes and metadata fields
                    data:NXdata
                        @signal=<name of signal field>
                        @axes=<name(s) of axes of signal>
                        @<axis>_indices=<list of indices in "axis1">
                        <signal_is_the_last_column>:NX_NUMBER[number of points] = ... data ...
                            @signal=1
                            @axes='<axis_is_name_of_first_column>'
                            @<axis>_indices=<list of indices in "axis1" used as dimension scales of the "signal">
                        <axis_is_name_of_first_column>:NX_NUMBER[number of points] = ... data ...
                        # other columns from the scan

        :param str hdf_file: name of NeXus/HDF5 file to be written
        :param [int] scanlist: list of scan numbers to be read
        """
        scan_list = scan_list or []
        root = eznx.makeFile(hdf_file, **self.root_attributes())
        pick_first_entry = True
        for key in scan_list:
            nxentry = eznx.makeGroup(root, "S" + str(key), "NXentry")
            eznx.makeDataset(
                nxentry,
                "definition",
                "NXspecdata",
                description="NeXus application definition (status pending)",
            )
            self.save_scan(nxentry, self.spec.getScan(key))
            if pick_first_entry:
                pick_first_entry = False
                eznx.addAttributes(root, default="S" + str(key))
            if "data" not in nxentry:
                # NXentry MUST have a NXdata group with data for default plot
                nxdata = eznx.makeGroup(
                    nxentry,
                    "data",
                    "NXdata",
                    signal="no_y_data",
                    axes="no_x_data",
                    no_x_data_indices=[0,],
                )
                eznx.makeDataset(
                    nxdata,
                    "no_x_data",
                    (0, 1),
                    units="none",
                    long_name="no data points in this scan",
                )
                eznx.makeDataset(
                    nxdata,
                    "no_y_data",
                    (0, 1),
                    units="none",
                    long_name="no data points in this scan",
                )
        root.close()  # be CERTAIN to close the file

    def root_attributes(self):
        """*internal*: returns the attributes to be written to the root element as a dict"""
        from spec2nexus._version import get_versions

        version = get_versions()["version"]
        header0 = self.spec.headers[0]
        dd = dict(
            spec2nexus_version=version,
            SPEC_file=self.spec.specFile,
            SPEC_epoch=header0.epoch,
            SPEC_date=utils.iso8601(header0.date),
            SPEC_comments="\n".join(header0.comments),
            SPEC_num_headers=len(self.spec.headers),
            h5py_version=h5py.__version__,
            HDF5_Version=h5py.version.hdf5_version,
            numpy_version=h5py.version.numpy.version.full_version,
        )
        try:
            c = header0.comments[0]
            user = c[c.find("User = ") :].split("=")[1].strip()
            dd["SPEC_user"] = user
        except Exception:
            pass
        return dd

    def save_scan(self, nxentry, scan):
        """*internal*: save the data from each SPEC scan to its own NXentry group"""
        scan.interpret()  # ensure interpretation is complete
        eznx.addAttributes(nxentry, default="data")
        eznx.write_dataset(nxentry, "title", str(scan))
        eznx.write_dataset(nxentry, "scan_number", scan.scanNum)
        eznx.write_dataset(nxentry, "command", scan.scanCmd)
        for func in scan.header.h5writers.values():
            # ask the header plugins to save their part
            func(nxentry, self, scan.header, nxclass=CONTAINER_CLASS)
        for func in scan.h5writers.values():
            # ask the scan plugins to save their part
            func(nxentry, self, scan, nxclass=CONTAINER_CLASS)

    def save_dict(self, group, data):
        """*internal*: store a dictionary"""
        for k, v in data.items():
            self.write_ds(group, k, v)

    def save_data(self, nxdata, scan):
        """*internal*: store the scan data"""
        scan_type = scan.scanCmd.split()[0]

        if scan_type in ("mesh", "hklmesh"):
            # hklmesh  H 1.9 2.1 100  K 1.9 2.1 100  -800000
            signal, axes = self.mesh(nxdata, scan)
        elif scan_type in ("hscan", "kscan", "lscan", "hklscan"):
            # hklscan  1.00133 1.00133  1.00133 1.00133  2.85 3.05  200 -400000
            signal = self.oneD(nxdata, scan)[0]
            axes = []
            h_0, h_N, k_0, k_N, l_0, l_N = scan.scanCmd.split()[1:7]
            if h_0 != h_N:
                axes.append("H")
            if k_0 != k_N:
                axes.append("K")
            if l_0 != l_N:
                axes.append("L")
            axes = ":".join(axes)
        else:
            signal, axes = self.oneD(nxdata, scan)

        # these locations suggested to NIAC, easier to parse than attached to dataset!
        # if len(signal) == 0:
        #     pass

        # Syntax of axes attribute (http://wiki.nexusformat.org/2014_axes_and_uncertainties):
        #  @axes="H:K"       INCOREECT
        #  @axes="H", "K"    CORRECT
        if axes.find(":") >= 0:

            def fixer(s):
                # h5py requires list of strings to be encoded
                # see: https://stackoverflow.com/questions/23220513/storing-a-list-of-strings-to-a-hdf5-dataset-from-python
                return s.encode("ascii", "ignore")

            axes = list(map(fixer, axes.split(":")))
        eznx.addAttributes(nxdata, signal=signal, axes=axes)
        indices = [
            0,
        ]  # 0-based reference
        if isinstance(axes, str):
            eznx.addAttributes(nxdata, **{axes + "_indices": indices})
        else:
            for axis_name in axes:
                axis_name = axis_name.decode("utf-8")
                # assume here that "axis_name" has rank=1
                # if scan.data[axis_name] != 1:
                #     pass    # TODO: and do what?
                k = "%s%s" % (axis_name, "_indices")
                eznx.addAttributes(nxdata, **{k: indices})

    def oneD(self, nxdata, scan):
        """*internal*: generic data parser for 1-D column data, returns signal and axis"""
        for column in scan.L:
            self.write_ds(nxdata, column, scan.data[column])

        signal = utils.clean_name(scan.column_last)  # primary Y axis
        axis = utils.clean_name(scan.column_first)  # primary X axis
        self.mca_spectra(nxdata, scan, axis)  # records any MCA data
        return signal, axis

    def mca_spectra(self, nxdata, scan, primary_axis_label):
        """*internal*: parse for optional 2-D MCA spectra"""
        if spec.MCA_DATA_KEY in scan.data:
            # calibration for all spectra
            a, b, c = 0, 0, 0
            if hasattr(scan, "MCA"):
                mca = scan.MCA
                if "CALIB" in mca:
                    a = mca["CALIB"].get("a", 0)
                    b = mca["CALIB"].get("b", 0)
                    c = mca["CALIB"].get("c", 0)
            if a == b and b == c and a == 0:
                a, b, c = 1, 0, 0

            # save each spectrum
            for key, spectrum in sorted(
                scan.data[spec.MCA_DATA_KEY].items()
            ):
                ds_name = "_" + key + "_"
                axes = primary_axis_label + ":" + ds_name + "channel_"
                self.write_ds(
                    nxdata, ds_name, spectrum, axes=axes, units="counts"
                )

                # save calibrated channel data for each spectrum, in case spectra are different lengths
                # _mca_     _mca_channel_
                # _mca1_    _mca1_channel_
                # _mca2_    _mca2_channel_
                # ...
                channels = np.arange(1, len(spectrum[0]) + 1, dtype=int)
                _mca_x_ = a + channels * (b + channels * c)
                self.write_ds(
                    nxdata, ds_name + "channel_", channels, units="channel"
                )
                self.write_ds(
                    nxdata, ds_name + "channel_scaled_x", _mca_x_, units=""
                )

    def mesh(self, nxdata, scan):
        """*internal*: data parser for 2-D mesh and hklmesh"""
        # TODO: refactor to use NeXus data model: signal, axes, data

        # 2-D parser: http://www.certif.com/spec_help/mesh.html
        # mesh motor1 start1 end1 intervals1 motor2 start2 end2 intervals2 time
        # 2-D parser: http://www.certif.com/spec_help/hklmesh.html
        #  hklmesh Q1 start1 end1 intervals1 Q2 start2 end2 intervals2 time
        # mesh:    data/33id_spec.dat  scan 22
        # hklmesh: data/33bm_spec.dat  scan 17

        (
            label1,
            _start1,
            _end1,
            intervals1,
            label2,
            _start2,
            _end2,
            intervals2,
            _time,
        ) = scan.scanCmd.split()[1:]
        if label1 not in scan.data:
            label1 = scan.L[0]  # mnemonic v. name
        if label2 not in scan.data:
            label2 = scan.L[1]  # mnemonic v. name
        axis1 = scan.data.get(label1)
        axis2 = scan.data.get(label2)
        intervals1, intervals2 = map(int, (intervals1, intervals2))
        # unused: start1, end1, start2, end2, time = map(float, (start1, end1, start2, end2, time))
        if (
            len(axis1) < intervals1
        ):  # stopped scan before second row started
            signal, axes = self.oneD(nxdata, scan)  # fallback support
        else:
            axis1 = axis1[0 : intervals1 + 1]
            axis2 = [
                axis2[row]
                for row in range(len(axis2))
                if row % (intervals1 + 1) == 0
            ]

            column_labels = scan.L
            column_labels.remove(label1)  # special handling
            column_labels.remove(label2)  # special handling
            if scan.scanCmd.startswith("hkl"):
                # find the reciprocal space axis held constant
                label3 = [
                    key
                    for key in ("H", "K", "L")
                    if key not in (label1, label2)
                ][0]
                axis3 = scan.data.get(label3)[0]
                self.write_ds(nxdata, label3, axis3)

            self.write_ds(nxdata, label1, axis1)  # 1-D array
            self.write_ds(nxdata, label2, axis2)  # 1-D array

            # build 2-D data objects (do not build label1, label2, [or label3] as 2-D objects)
            data_shape = [len(axis1), len(axis2)]
            for label in column_labels:
                if label not in nxdata:
                    axis = np.array(scan.data.get(label))
                    self.write_ds(
                        nxdata, label, utils.reshape_data(axis, data_shape)
                    )
                # else:
                #     pass

            signal = utils.clean_name(scan.column_last)
            axes = ":".join([label1, label2])

        if spec.MCA_DATA_KEY in scan.data:  # 3-D array(s)
            # save each spectrum
            for key, spectrum in sorted(
                scan.data[spec.MCA_DATA_KEY].items()
            ):
                num_channels = len(spectrum[0])
                data_shape.append(num_channels)
                mca = np.array(spectrum)
                data = utils.reshape_data(mca, data_shape)
                channels = range(1, num_channels + 1)
                ds_name = "_" + key + "_"
                self.write_ds(
                    nxdata,
                    ds_name,
                    data,
                    axes=axes + ":" + ds_name + "channel_",
                    units="counts",
                )
                self.write_ds(
                    nxdata, ds_name + "channel_", channels, units="channel"
                )

        return signal, axes

    def write_ds(self, group, label, data, **attr):
        """*internal*: writes a dataset to the HDF5 file, records the SPEC name as an attribute"""
        clean_name = utils.clean_name(label)
        eznx.write_dataset(
            group, clean_name, data, spec_name=label, **attr
        )
