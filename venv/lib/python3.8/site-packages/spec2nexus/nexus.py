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


"""Converts SPEC data files and scans into NeXus HDF5 files"""

# this is the main code for the *spec2nexus* application

__url__ = "http://spec2nexus.readthedocs.org/en/latest/spec2nexus.html"

import os
import sys

if __name__ == "__main__":
    # put us on the path for developers
    path = os.path.join("..", os.path.dirname(__file__))
    sys.path.insert(0, os.path.abspath(path))

from . import spec
from . import writer


hdf5_extension = ".hdf5"


# -------------------------------------------------------------------------------------------


REPORTING_QUIET = "quiet"
REPORTING_STANDARD = "standard"
REPORTING_VERBOSE = "verbose"
SCAN_LIST_ALL = "all"


def get_user_parameters():
    """configure user's command line parameters from sys.argv"""
    # global hdf5_extension
    import argparse
    from spec2nexus._version import get_versions

    version = get_versions()["version"]
    doc = __doc__.strip().splitlines()[0]
    doc += "\n  URL: " + __url__
    doc += "\n  v" + version
    parser = argparse.ArgumentParser(prog="spec2nexus", description=doc)
    parser.add_argument(
        "infile", action="store", nargs="+", help="SPEC data file name(s)"
    )
    msg = "NeXus HDF5 output file extension"
    msg += ", default = %s" % hdf5_extension
    parser.add_argument(
        "-e",
        "--hdf5-extension",
        action="store",
        dest="hdf5_extension",
        help=msg,
        default=hdf5_extension,
    )
    parser.add_argument(
        "-f",
        "--force-overwrite",
        action="store_true",
        dest="force_write",
        help="overwrite output file if it exists",
        default=False,
    )
    parser.add_argument(
        "-v", "--version", action="version", version=version
    )
    msg = "specify which scans to save"
    msg += ", such as: -s all  or  -s 1  or  -s 1,2,3-5  (no spaces!)"
    msg += ", default = %s" % SCAN_LIST_ALL
    parser.add_argument(
        "-s",
        "--scan",
        nargs=1,
        # action='append',
        dest="scan_list",
        default=SCAN_LIST_ALL,
        help=msg,
    )
    #     parser.add_argument('-t',
    #                         '--tree-only',
    #                         action='store_true',
    #                         dest='tree_only',
    #                         help='print NeXus/HDF5 node tree (does not save to a file)',
    #                         default=False)

    group = parser.add_mutually_exclusive_group()
    group.set_defaults(reporting_level=REPORTING_STANDARD)
    msg = "suppress all program output (except errors)"
    msg += ", do not use with --verbose option"
    group.add_argument(
        "--quiet",
        dest="reporting_level",
        action="store_const",
        const=REPORTING_QUIET,
        help=msg,
    )
    msg = "print more program output"
    msg += ", do not use with --quiet option"
    group.add_argument(
        "--verbose",
        dest="reporting_level",
        action="store_const",
        const=REPORTING_VERBOSE,
        help=msg,
    )

    return parser.parse_args()


def parse_scan_list_spec(scan_list_spec):
    """parses the argument of the -s option, returns a scan number list"""
    # can this be simpler?
    sl = scan_list_spec[0].split(",")

    scan_list = []
    for item in sl:
        sublist = item.split("-")
        if len(sublist) == 1:
            scan_list.append(int(sublist[0]))
        elif len(sublist) == 2:
            scan_list += range(int(sublist[0]), int(sublist[1]) + 1)
        else:
            raise ValueError("improper scan list specifier: " + sublist)

    sl = []
    for item in sorted(scan_list):
        if item not in sl:
            sl.append(item)

    return sl


def pick_scans(all_scans, opt_scan_list):
    """
    edit opt_scan_list for the scans to be converted

    To be converted, a scan number must be first specified in opt_scan_list
    and then all_scans is checked to make sure that scan exists.
    The final list is returned.
    """
    if opt_scan_list == SCAN_LIST_ALL:
        scan_list = all_scans
    else:
        scan_list = map(str, opt_scan_list)
        # for item in scan_list:
        #     if str(item) not in all_scans:
        #         scan_list.remove(item)
        scan_list = [item for item in scan_list if str(item) in all_scans]
    return scan_list


def main():
    """entry point for command-line interface"""

    user_parms = get_user_parameters()

    spec_data_file_name_list = user_parms.infile

    if user_parms.scan_list != SCAN_LIST_ALL:
        user_parms.scan_list = parse_scan_list_spec(user_parms.scan_list)

    if not user_parms.hdf5_extension.startswith(os.extsep):
        user_parms.hdf5_extension = os.extsep + user_parms.hdf5_extension

    for spec_data_file_name in spec_data_file_name_list:
        if not os.path.exists(spec_data_file_name):
            msg = "File not found: " + spec_data_file_name
            print(msg)
            continue

        if user_parms.reporting_level in (
            REPORTING_STANDARD,
            REPORTING_VERBOSE,
        ):
            print("reading SPEC data file: " + spec_data_file_name)
        spec_data = spec.SpecDataFile(spec_data_file_name)

        all_scans = spec_data.getScanNumbers()
        scan_list = list(pick_scans(all_scans, user_parms.scan_list))
        if user_parms.reporting_level in (REPORTING_VERBOSE):
            print("  discovered %d scans" % len(spec_data.scans.keys()))
            print(
                "  converting scan number(s): "
                + ", ".join(map(str, scan_list))
            )

        basename = os.path.splitext(spec_data_file_name)[0]
        nexus_output_file_name = basename + user_parms.hdf5_extension
        if user_parms.force_write or not os.path.exists(
            nexus_output_file_name
        ):
            out = writer.Writer(spec_data)
            out.save(nexus_output_file_name, scan_list)
            if user_parms.reporting_level in (
                REPORTING_STANDARD,
                REPORTING_VERBOSE,
            ):
                print("wrote NeXus HDF5 file: " + nexus_output_file_name)


if __name__ == "__main__":
    main()
