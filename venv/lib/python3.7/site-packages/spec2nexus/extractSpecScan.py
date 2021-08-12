#!/usr/bin/python

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
Save columns from SPEC data file scan(s) to TSV files

.. note:: TSV: tab-separated values

**Usage**::

  extractSpecScan.py /tmp/CeCoIn5 -s 5 -c HerixE Ana5 ICO-C
  extractSpecScan.py ./testdata/11_03_Vinod.dat   -s 2 12   -c USAXS.m2rp Monitor  I0

.. note:: sdpecified column names **MUST** appear in all chosen scans

Compatible with Python 2.7+
"""

from __future__ import print_function

__url__ = (
    "http://spec2nexus.readthedocs.org/en/latest/extractSpecScan.html"
)

import os
import sys
from . import spec


# -------------------------------------------------------------------------------------------


REPORTING_QUIET = "quiet"
REPORTING_STANDARD = "standard"
REPORTING_VERBOSE = "verbose"


# -------------------------------------------------------------------------------------------


def makeOutputFileName(specFile, scanNum):
    """
    return an output file name based on specFile and scanNum

    :param str specFile: name of existing SPEC data file to be read
    :param str scanNum: number of chosen SPEC scan

    append scanNum to specFile to get output file name
    (before file extension if present)

    Always add a file extension to the output file.
    If none is present, use ".dat".

    Examples:

    ===========  ========   ===============
    specFile     scanNum    outFile
    ===========  ========   ===============
    CeCoIn5      scan 5     CeCoIn5_5.dat
    CeCoIn5.dat  scan 77    CeCoIn5_77.dat
    CeCoIn5.dat  scan 5.1   CeCoIn5_5_1.dat
    ===========  ========   ===============
    """
    name_parts = os.path.splitext(specFile)
    scan_number = str(scanNum).replace(".", "_")
    outFile = name_parts[0] + "_" + scan_number + name_parts[1]
    return outFile


def expand_scan_range_terms(scans):
    # expand range of scan terms into individual scan numbers
    _scans_ = []
    for item in scans:
        if item.startswith("-"):
            _scans_.append(item)
        else:
            parts = item.split("-")
            if len(parts) == 1:
                _scans_.append(item)
            elif len(parts) == 2:
                _scans_ += [
                    str(k) for k in range(int(parts[0]), int(parts[1]) + 1)
                ]
            else:
                raise ValueError("scan specifier not recognized: " + item)
    return _scans_


def get_user_parameters():
    """configure user's command line parameters from sys.argv"""
    import argparse
    from spec2nexus._version import get_versions

    version = get_versions()["version"]

    doc = __doc__.strip().splitlines()[0]
    doc += "\n  URL: " + __url__
    doc += "\n  v" + version
    parser = argparse.ArgumentParser(
        prog="extractSpecScan", description=doc
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        help="print version number and exit",
        version=version,
    )

    msg = (
        "do not write column labels to output file (default: write labels)"
    )
    parser.add_argument(
        "--nolabels", action="store_true", help=msg, default=False
    )

    parser.add_argument(
        "spec_file", action="store", help="SPEC data file name(s)"
    )

    msg = "scan number(s) to be extracted (must specify at least one) a range is allowed: 8-12 (no whitespace around the '-')"
    parser.add_argument(
        "-s",
        "--scan",
        action="store",
        nargs="+",
        # type=int,
        required=True,
        help=msg,
    )

    msg = "column label(s) to be extracted (must specify at least one)"
    parser.add_argument(
        "-c",
        "--column",
        action="store",
        nargs="+",
        required=True,
        help=msg,
    )

    msg = "report scan Geometry (#G) header information"
    parser.add_argument("-G", action="store_true", default=False, help=msg)

    msg = "report scan Positioners (#O & #P) header information"
    parser.add_argument("-P", action="store_true", default=False, help=msg)

    msg = "report scan Q (#Q) header information"
    parser.add_argument("-Q", action="store_true", default=False, help=msg)

    msg = "report scan (UNICAT-style #H & #V) header information"
    parser.add_argument("-V", action="store_true", default=False, help=msg)

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

    args = parser.parse_args()

    args.scan = expand_scan_range_terms(args.scan)

    args.print_labels = not args.nolabels
    del args.nolabels

    return args


def main():
    """
    read the data file, find each scan, find the columns, save the data

    :param [str] cmdArgs: Namespace from argparse, returned from get_user_parameters()

    ..  such as:
      Namespace(column=['mr', 'I0', 'USAXS_PD'], print_labels=True, scan=[1, 6], spec_file=['data/APS_spec_data.dat'])

    .. note:: Each column label must match *exactly* the name of a label
       in each chosen SPEC scan number or the program will skip that particular scan

       If more than one column matches, the first match will be selected.

    example output::

        # mr    I0    USAXS_PD
        1.9475    65024    276
        1.9725    64845    352
        1.9975    65449    478

    """
    cmdArgs = get_user_parameters()

    if cmdArgs.reporting_level in (REPORTING_STANDARD, REPORTING_VERBOSE):
        print("program: " + sys.argv[0])
    # now open the file and read it
    specData = spec.SpecDataFile(cmdArgs.spec_file)
    if cmdArgs.reporting_level in (REPORTING_STANDARD, REPORTING_VERBOSE):
        print("read: " + cmdArgs.spec_file)

    for scanNum in cmdArgs.scan:
        outFile = makeOutputFileName(cmdArgs.spec_file, scanNum)
        scan = specData.getScan(scanNum)
        scan.interpret()  # force the plug-ins to be processed

        # get the column numbers corresponding to the column_labels
        column_numbers = []
        for label in cmdArgs.column:
            if label in scan.L:
                # report all columns in order specified on command-line
                column_numbers.append(scan.L.index(label))
            else:
                if cmdArgs.reporting_level in (REPORTING_VERBOSE):
                    msg = (
                        'column label "' + label + '" not found in scan #'
                    )
                    msg += str(scanNum) + " ... skipping"
                    print(msg)  # report all mismatched column labels

        if len(column_numbers) == len(
            cmdArgs.column
        ):  # must be perfect matches
            txt = []
            if cmdArgs.print_labels:
                txt.append("# " + "\t".join(cmdArgs.column))
            if len(scan.data) > 0:
                data = [scan.data[item] for item in cmdArgs.column]
                for data_row in zip(*data):
                    txt.append("\t".join(map(str, data_row)))
            else:
                # issue #45: no data lines in scan
                txt.append("# <no SPEC data points in this scan>")

            header_data = []
            if cmdArgs.G:
                for k, v in sorted(scan.G.items()):
                    # use tab separation to make it easy to pull into spreadsheet columns
                    header_data.append(
                        "#G\t%s\t%s" % (k, "\t".join(v.split(" ")))
                    )
            if cmdArgs.P:
                for k, v in sorted(scan.positioner.items()):
                    header_data.append(
                        "#P\t%s\t%s" % (k, str(v))
                    )  # str(v) vs. %g or other
            if cmdArgs.Q:
                if len(scan.Q) > 0:
                    header_data.append(
                        "#Q\t%s" % "\t".join(map(str, scan.Q))
                    )
            if cmdArgs.V:
                try:
                    for k, v in sorted(scan.metadata.items()):
                        header_data.append("#V\t%s\t%s" % (k, v))
                except AttributeError:
                    pass  # no metadata
            if len(header_data):
                header_data.insert(0, "# data from scan heading")
                header_data.insert(0, "#")
                header_data.append("#")
                header_data.append("# scan data:")
                header_data.append("#")

            # at the top of every file now
            header_data.insert(0, "# scan: " + str(scanNum))
            header_data.insert(0, "# file: " + str(cmdArgs.spec_file))

            fp = open(outFile, "w")
            if len(header_data):
                fp.write("\n".join(header_data) + "\n")
            fp.write("\n".join(txt))
            fp.close()
            if cmdArgs.reporting_level in (
                REPORTING_STANDARD,
                REPORTING_VERBOSE,
            ):
                print("wrote: " + outFile)
            if cmdArgs.reporting_level in (REPORTING_VERBOSE,):
                for item in scan.get_interpreter_comments():
                    print(item)


if __name__ == "__main__":
    main()
